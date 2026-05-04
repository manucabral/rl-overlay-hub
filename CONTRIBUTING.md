# Contributing to RL Overlay Hub

Thanks for contributing to RL Overlay Hub.

This project accepts both code contributions and community overlay submissions. If you are contributing an overlay, the most important part is following the community overlay structure and updating the shared registry in the same pull request.

## Ways to Contribute

- fix bugs in the desktop app or backend
- improve documentation in `docs/`
- add or improve built-in overlays
- submit a new community overlay
- improve creator tooling and templates

## Local Development

### 1. Set up the environment

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the app

```powershell
python run.py
```

### 3. Run checks before opening a PR

```powershell
venv\Scripts\python.exe -m black .
venv\Scripts\python.exe -m pylint app tests
venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp
```

## Submitting a Community Overlay

If you want your overlay to appear in the in-app Community tab, submit it to this repository.

### Required PR contents

Your pull request should include both:

1. the overlay folder inside `community-overlays/`
2. an updated `community-overlays/registry.json` entry for that overlay

Do not submit only the files without updating the registry, and do not update the registry without including the overlay files.

### Expected folder structure

```text
community-overlays/
  my-overlay/
    manifest.json
    index.html
    style.css
    script.js
    preview.png
```

Minimum required files:

- `manifest.json`
- `index.html`

Recommended files:

- `style.css`
- `script.js`
- `preview.png`

### Overlay requirements

- `manifest.json` must be valid JSON
- `id` must be unique
- `id` must match the folder name
- the overlay must work as a standard HTML/CSS/JS browser source
- relative asset paths must resolve correctly from `index.html`
- the overlay should be testable in RL Overlay Hub Preview Mode

### Updating `registry.json`

Add a new entry for your overlay with the metadata needed by the app.

At minimum, make sure the entry is consistent with your manifest:

- `id`
- `name`
- `author`
- `version`
- `description`
- `path`

`path` should point to the folder under `community-overlays/`.

### Before opening the PR

Please verify:

- the overlay loads locally in RL Overlay Hub
- the overlay URL works in a browser
- the overlay works in OBS as a Browser Source
- Preview Mode behaves correctly
- the registry entry matches the overlay folder and manifest

## Code Contributions

For app or backend changes:

- keep changes focused
- include tests when behavior changes
- preserve the public overlay API unless the change is intentional and documented
- update `docs/` when creator-facing behavior changes

## Pull Request Checklist

- I ran formatting, linting, and tests locally
- I updated documentation if behavior changed
- If this PR adds a community overlay, it includes both the overlay folder and the `registry.json` change
- The change is scoped to one clear purpose
