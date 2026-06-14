# CV project — how to update

The résumé is a single design file, **`CV Template.dc.html`**, that renders all of its
content from **`profile.json`**.

## To update the CV
Edit **`profile.json`** only. Never edit text/content inside `CV Template.dc.html` —
that file is layout + styling and reads everything from the JSON.

Field notes:
- `skills` and `languages`: each item has `pct` (0–100) which sets the bar length.
- `interests[].icon` must be one of: `camera`, `piano`, `chess`, `dumbbell`.
  (To add a new icon, add its SVG to the `ICONS` map in `CV Template.dc.html`.)
- `tools` is the "Frameworks & Tools" chip list.
- `photo` is the profile image path (a square image works best; it is cropped to a square).

## Layout constraints
- Single page, **US Legal size (8.5 × 14 in / 816 × 1344 px)**, two columns
  (white main + navy `#1f3a5f` sidebar on the right).
- Keep the sidebar content ≤ 1344px tall so it stays one page. If you add a lot,
  tighten the `gap`/`padding` on the `<aside>` or shrink the photo.
- Fonts: IBM Plex Sans + IBM Plex Mono.

## Print / PDF
Print to PDF at Legal size with margins set to "None" (page is already sized for it).
