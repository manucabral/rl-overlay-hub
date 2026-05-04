# Rocket League Stats API
RL_STATS_API_PORT = 49123
RL_RECONNECT_DELAY = 2.0
RL_MAX_RECONNECT_DELAY = 30.0

# App metadata
APP_NAME = "RL Overlay Hub"
APP_VERSION = "0.1.0"

# Overlay hub server
DEFAULT_PORT = 49100

# Community registry
DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/manucabral/rl-overlay-hub/main"
    "/community-overlays/registry.json"
)

# Overlay validation
OVERLAY_REQUIRED_FILES = frozenset({"manifest.json", "index.html"})

# Logging - third-party loggers to silence
QUIET_LOGGERS = ("uvicorn.access", "uvicorn.error", "httpx", "httpcore")
SUPPRESS_LOGGERS = ("rlstatsapi.config",)
