import asyncio
import logging
import os
import subprocess
import threading

import uvicorn

from . import session_storage
from . import storage
from .config import config
from .constants import APP_NAME, APP_VERSION
from .logger import get_logger, setup as _setup_logging
from .overlay_server import create_app
from .rlstats_client import RLStatsClient
from .runtime import wait_for_port
from .schemas import SettingsModel
from .state_manager import StateManager
from .websocket_events import ConnectionManager

_setup_logging(
    level=logging.DEBUG if storage.get("verbose") else logging.INFO,
    log_file=config.log_path,
)
log = get_logger(__name__)


class PanelAPI:
    """
    API exposed to the panel Js via pywebview. Must be thread-safe since
    pywebview calls, it from the main thread while the app logic
    runs in a background thread.
    """

    def __init__(self) -> None:
        self._window = None

    def set_window(self, window) -> None:
        self._window = window

    def pick_folder(self) -> str | None:
        import webview

        if self._window is None:
            return None
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def open_data_folder(self) -> None:
        path = config.data_dir
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            subprocess.Popen(["explorer", str(path)])  # pylint: disable=consider-using-with


def main() -> None:
    """Main entry point for the application."""
    import webview

    panel_api = PanelAPI()
    settings = SettingsModel.model_validate(storage.load())
    port = settings.port
    session_store = session_storage.load()

    state_manager = StateManager(preview=settings.preview_mode, session_store=session_store)
    connection_manager = ConnectionManager()
    rl_client = RLStatsClient(state_manager, connection_manager)

    fastapi_app = create_app(state_manager, connection_manager, settings, rl_client)

    # pywebview requires the main thread, so the entire asyncio world
    # uvicorn + RL client runs in a dedicated background thread with its own loop
    loop = asyncio.new_event_loop()

    def _loop_exception_handler(_loop, context):
        """
        on Windows the ProactorEventLoop raises ConnectionResetError when the
        remote side (browser / OBS) closes a ws before asyncio finishes
        its own shutdown, this is normal behaviour not an app error
        """
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError):
            return
        _loop.default_exception_handler(context)

    loop.set_exception_handler(_loop_exception_handler)

    def run_async_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(target=run_async_loop, daemon=True).start()

    rl_future = asyncio.run_coroutine_threadsafe(rl_client.run(), loop)

    uvicorn_config = uvicorn.Config(
        fastapi_app,
        host="127.0.0.1",
        port=port,
        loop="none",
        log_level="warning",
    )
    server = uvicorn.Server(uvicorn_config)
    server_future = asyncio.run_coroutine_threadsafe(server.serve(), loop)

    if not wait_for_port("127.0.0.1", port, timeout=5.0):
        raise RuntimeError(f"Server failed to start on port {port}")
    log.info("Server running at http://127.0.0.1:%d", port)

    window = webview.create_window(
        f"{APP_NAME} {APP_VERSION}",
        f"http://127.0.0.1:{port}/panel",
        width=config.window_width,
        height=config.window_height,
        min_size=(config.window_min_width, config.window_min_height),
        background_color=config.window_bg_color,
        js_api=panel_api,
    )
    panel_api.set_window(window)
    webview.start(debug=config.development_mode)

    # tasks must be cancelled before loop.stop(). Stopping the loop without
    # cancellation causes the gc to throw GeneratorExit into running coroutines,
    # which rlstatsapi catches and converts into a runtime_error + reconnect loop
    log.info("Window closed, shutting down")
    server.should_exit = True
    try:
        server_future.result(timeout=5)
    except Exception:  # pylint: disable=broad-exception-caught
        log.debug("Server future did not finish before shutdown timeout", exc_info=True)
    rl_client.cancel(loop)
    try:
        rl_future.result(timeout=5)
    except Exception:  # pylint: disable=broad-exception-caught
        log.debug("RL client future did not finish before shutdown timeout", exc_info=True)
    loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    main()
