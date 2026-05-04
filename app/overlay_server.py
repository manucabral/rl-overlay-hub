from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import config
from .rlstats_client import RLStatsClient
from .routers import (
    overlay_routes,
    preview_routes,
    rl_config_routes,
    session_routes,
    state_routes,
    system_routes,
)
from .state_manager import StateManager
from .websocket_events import ConnectionManager


def create_app(
    state_manager: StateManager,
    connection_manager: ConnectionManager,
    settings: dict,
    rl_client: RLStatsClient,
) -> FastAPI:
    """Factory function to create the FastAPI app with the given dependencies."""
    app = FastAPI(title="RL Overlay Hub", docs_url=None, redoc_url=None)

    app.state.state_manager = state_manager
    app.state.connection_manager = connection_manager
    app.state.settings = settings
    app.state.rl_client = rl_client

    if config.panel_dir.exists():
        app.mount(
            "/panel/static",
            StaticFiles(directory=str(config.panel_dir)),
            name="panel_static",
        )

    app.include_router(system_routes.router)
    app.include_router(state_routes.router)
    app.include_router(session_routes.router)
    app.include_router(rl_config_routes.router)
    app.include_router(overlay_routes.router)
    app.include_router(preview_routes.router)

    return app
