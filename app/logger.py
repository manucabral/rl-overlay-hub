import logging
import logging.handlers
from pathlib import Path

from .constants import QUIET_LOGGERS, SUPPRESS_LOGGERS

_COLORS = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[35m",  # magenta
}
_RESET = "\033[0m"

_FMT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATE_FMT = "%H:%M:%S"


class _QueueFullFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "queue full" not in record.getMessage()


class _ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelno, "")
        # Copy so we don't mutate the shared LogRecord seen by other handlers
        # (e.g. the file handler would otherwise get ANSI escape codes on disk).
        record = logging.makeLogRecord(record.__dict__)
        record.levelname = f"{color}{record.levelname}{_RESET}"
        return super().format(record)


def setup(
    level: int = logging.INFO,
    log_file: Path | None = None,
    quiet: tuple[str, ...] = QUIET_LOGGERS,
    suppress: tuple[str, ...] = SUPPRESS_LOGGERS,
) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(_ColorFormatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
        root.addHandler(file_handler)

    for name in quiet:
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in suppress:
        logging.getLogger(name).setLevel(logging.ERROR)

    logging.getLogger("rlstatsapi").addFilter(_QueueFullFilter())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
