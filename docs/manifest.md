# Manifest Reference

Every overlay must have a `manifest.json` file at the root of its folder. The hub reads this file to identify and display your overlay.

## Example

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

## Fields

### id

**Required.** String. Unique identifier for the overlay. Must match the folder name exactly. Use lowercase letters, numbers, and hyphens only.

```json
"id": "my-overlay"
```

### name

**Required.** String. Display name shown in the hub UI.

```json
"name": "My Overlay"
```

### entry

**Required.** String. Filename of the HTML page to serve as the overlay root. Almost always `"index.html"`.

```json
"entry": "index.html"
```

### version

Optional. String. Version of your overlay. Displayed in the hub UI. Use semantic versioning (`major.minor.patch`).

```json
"version": "1.0.0"
```

### author

Optional. String. Your name or handle. Displayed in the hub UI.

```json
"author": "YourName"
```

### description

Optional. String. One or two sentences describing what the overlay does. Displayed in the hub UI.

```json
"description": "Shows a banner with the scorer's name when a goal is scored."
```

### preview

Optional. String. Filename of a PNG screenshot of your overlay. Displayed as a thumbnail in the hub UI. Recommended size is 1280x720 or any 16:9 ratio.

```json
"preview": "preview.png"
```

### permissions

Optional. Array of strings. Reserved for future use. You can include it to document what data your overlay uses, but the hub does not enforce it.

```json
"permissions": ["match:read", "events:goals"]
```

## Rules

- The file must be valid JSON. Use a JSON validator if the overlay does not appear in the hub.
- The `id` value must match the folder name exactly, including capitalization. A mismatch will cause the overlay to fail to load.
- The hub looks for `manifest.json` and `index.html` at the top level of the folder. Do not nest them inside a subdirectory.

## Community Submission

If you want your overlay to appear in the app's Community tab, you also need to submit it to the project repository:

- place the overlay folder inside `community-overlays/`
- add or update its entry in `community-overlays/registry.json`
- open a pull request with both changes together

The registry entry is what makes the overlay discoverable and installable for other users.
