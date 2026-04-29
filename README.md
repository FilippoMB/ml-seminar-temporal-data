# Deep Learning for Temporal Data

The published presentation is available at:

https://filippomb.github.io/ml-seminar-temporal-data/presentation_temporal.html

## Local Preview

From the repository root, start a static local server:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/presentation_temporal.html
```

Stop the preview server with `Ctrl+C` in the terminal where it is running.

If the terminal is gone but the port is still busy:

```bash
lsof -ti :8000 | xargs kill
```

## Browser Text Editor

Use the reveal.js editor helper to edit slide text directly in the browser:

```bash
node /Users/fbi005/Library/CloudStorage/OneDrive-UiTOffice365/Documents/NORCE-EO-time-series-spatio-temporal-presentation/.agents/skills/revealjs/scripts/edit-html.js /Users/fbi005/Library/CloudStorage/OneDrive-UiTOffice365/Documents/NORCE-EO-time-series-spatio-temporal-presentation/presentation_temporal.html
```

This starts an editor service at:

```text
http://localhost:3456
```

Click any text to edit it, press `Escape` to deselect, then click `Save` to write changes back to `presentation_temporal.html`.

Stop the editor service with `Ctrl+C` in the terminal where it is running.

If port `3456` is still busy:

```bash
lsof -ti :3456 | xargs kill
```

## QA Commands

Install the local Node dependencies once:

```bash
npm install
```

Check all slides for layout overflow:

```bash
npm run check:overflow
```

Export a PDF and screenshot every slide:

```bash
mkdir -p screenshots
SCREEN_DIR="screenshots/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SCREEN_DIR"
npx decktape reveal "presentation_temporal.html?export" output.pdf --screenshots --screenshots-directory "$SCREEN_DIR"
```

Generated `output.pdf` and `screenshots/` are ignored by git.
