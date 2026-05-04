<img width="600" alt="rlstatsapi-logo" src="https://github.com/manucabral/rl-overlay-hub/blob/main/assets/social-preview.png" />

# RL Overlay Hub
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/github/downloads/manucabral/rl-overlay-hub/total)](https://github.com/manucabral/rl-overlay-hub/releases)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/manucabral/rl-overlay-hub/releases)
[![License](https://img.shields.io/github/license/manucabral/rl-overlay-hub)](https://github.com/manucabral/rl-overlay-hub/blob/main/LICENSE)

Desktop app that connects Rocket League to OBS browser-source overlays, no coding required to get started.

RL Overlay Hub reads live game data from Rocket League through `rlstatsapi`, runs a local web server, and pushes match events to your HTML overlays in real time through WebSocket.

It is designed for streamers, overlay creators, and developers who want Rocket League overlays for OBS without having to build their own game-data bridge.

---

## How it works

```text
Rocket League → RL Overlay Hub → WebSocket → HTML Overlay → OBS Browser Source
```

The hub reads live match data, serves your overlays locally, and sends events such as goals, replays, stat updates, match lifecycle changes, and session totals.

Overlay URLs look like this:

```text
http://127.0.0.1:49100/overlay/<overlay-id>/
```

## Download

The latest release is available in the [Releases](https://github.com/manucabral/rl-overlay-hub/releases) section.

No Python setup is required. Just install and run.


## What it does

- Runs as a local desktop app on Windows
- Starts an embedded FastAPI server
- Serves installed HTML/CSS/JS overlays over HTTP
- Pushes live Rocket League events through WebSocket
- Provides a small JavaScript client at `/overlay-api.js`
- Includes Preview Mode for testing overlays without Rocket League running
- Supports local overlays and a community overlay registry
- Works with OBS Browser Sources



### Requirements

- Windows
- Rocket League
- OBS Studio, if you want to use overlays on stream

---

## Documentation

Full guides and API reference are available here:

**[manucabral.github.io/rl-overlay-hub](https://manucabral.github.io/rl-overlay-hub/)**

| Page | What it covers |
|------|----------------|
| [Quick Start](https://manucabral.github.io/rl-overlay-hub/quickstart/) | Get your first overlay running |
| [JavaScript API](https://manucabral.github.io/rl-overlay-hub/api/) | Events and state your overlay can use |
| [State Reference](https://manucabral.github.io/rl-overlay-hub/state/) | Full game state object structure |
| [Event Snippets](https://manucabral.github.io/rl-overlay-hub/examples/event-snippets/) | Copy-paste code examples |

---

## Create your first overlay

1. Copy `creator-template/` into your installed overlays folder:

   ```text
   C:\Users\<you>\.rl-overlay-hub\overlays\installed\
   ```

2. Edit `manifest.json`.

   At minimum, set:

   ```json
   {
     "id": "my-overlay",
     "name": "My Overlay",
     "author": "YourName"
   }
   ```

3. Open RL Overlay Hub.

4. Go to the **Overlays** tab.

5. Enable **Preview Mode** to test without Rocket League running.

6. Open your overlay in a browser or add it to OBS as a Browser Source:

   ```text
   http://127.0.0.1:49100/overlay/<overlay-id>/
   ```


## Development workflow

When building an overlay, you can:

- Use the **Preview** tab to simulate Rocket League events
- Open the overlay in a normal browser while editing
- Reload manually after changing HTML, CSS, or JavaScript
- Use the **Live** tab to inspect real match data
- Use the **Logs** tab to debug connection or event issues

The shared JavaScript API is served at:

```text
http://127.0.0.1:49100/overlay-api.js
```


## Run from source

For contributors and advanced users.

### Requirements

- Python `3.12+`
- Windows
- Rocket League

Create a virtual environment and install the project:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the desktop app:

```powershell
python run.py
```

The hub will open its desktop window and start the local server, usually at:

```text
http://127.0.0.1:49100
```


## Run tests

```powershell
python -m pytest
```


## Run docs locally

```powershell
python -m pip install -r docs\requirements.txt
python -m mkdocs serve
```

GitHub Pages deploys from the `gh-pages` branch using the workflow in:

```text
.github/workflows/docs.yml
```



## Community overlays

Community overlays are submitted through the `community-overlays/` folder.

Each overlay should include a `manifest.json` file with basic metadata:

```json
{
  "id": "my-overlay",
  "name": "My Overlay",
  "version": "1.0.0",
  "author": "YourName",
  "description": "A brief description of what your overlay does.",
  "entry": "index.html",
  "preview": "preview.png"
}
```

Submitted overlays should be reviewed before being added to the community registry.


## Contributing

See [CONTRIBUTING.md](https://github.com/manucabral/rl-overlay-hub/blob/main/CONTRIBUTING.md) for app, documentation, and community overlay contribution guidelines.

## Contributors
People who contribute to the development, maintenance, and improvement of the application.

<a href="https://github.com/manucabral/rl-overlay-hub/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=manucabral/rl-overlay-hub" />
</a>

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
