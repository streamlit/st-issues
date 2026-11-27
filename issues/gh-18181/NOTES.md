# gh-18181: Green and blue patches in print preview

## Summary

The reporter sees solid blue and green vertical patches when printing a
Streamlit 1.67.0 app to PDF from Chrome or Edge on Windows. The report includes
a print-preview screenshot but no app code, custom CSS, theme configuration, or
public app URL.

## Finding

**Bug confirmed with a synthetic trigger.** A fixed-height keyed container with
custom blue and green background regions stays bounded in Streamlit 1.66.0 but
expands substantially in 1.67.0 print layout when it contains a dataframe and a
chart. The expansion produces long vertical strips like the reported patches.

The reporter's exact selector remains unknown because the issue does not include
the app or its CSS. The synthetic reproduction confirms the 1.67.0 layout
regression and a plausible mechanism, not the reporter's precise styling.

## Reproduction

- Python: 3.13
- Browser automation: headless Chromium, print media emulation, and PDF output
- Released wheels tested: 1.66.0 and 1.67.0
- Server URL: `http://localhost:8601`

The minimized app includes the same broad surfaces visible in the report: wide
layout, an open sidebar, controls, a dataframe, a chart, and custom colored
background regions on a fixed-height ancestor.

Observed print geometry:

- In 1.66.0, the panel remained `display:flex`, `height:420px`, and
  `overflow:auto`; its colored regions were 418 px tall.
- In 1.67.0, the same panel became `display:block`, grew to 675.6 px, and used
  `overflow:visible`; its colored regions grew to 674 px.
- The fuller synthetic app grew from 520 px to 1,017 px, and its PDF expanded
  from two pages to four.
- Direct backgrounds on the stacking columns became horizontal bands, while a
  background on the fixed-height ancestor produced the vertical-patch shape.

## Root Cause

The likely regression source is the print-layout overhaul in commit
`8176539668e5b4d4894b65eb3d4ad0bbeaa62a35`, shipped in 1.67.0. It added broad
`@media print` changes that:

- switch app containers from fixed viewport geometry to content-driven height;
- force the sidebar to a 200 px print width and stretch it with the app;
- convert vertical flex containers to block layout; and
- stack column rows that contain dataframes or charts.

Together, these rules release the fixed height and overflow of an ancestor
containing a chart or dataframe row. A custom background on that ancestor then
paints across the expanded print area. This mechanism is verified by computed
geometry, print-media screenshots, and Chromium's paginated PDF output.

Code pointers:

- `frontend/app/src/components/AppView/styled-components.ts:37-44`
- `frontend/app/src/components/Sidebar/styled-components.ts:91-107`
- `frontend/lib/src/components/core/Block/styled-components.ts:495-619`

Fix direction: narrow the 1.67.0 height-release rule so fixed-height ancestors
do not unexpectedly expand custom backgrounds, while preserving the intended
chart/dataframe stacking and overflow behavior.

## Workaround

The published repro includes a checkbox that injects a print-only override to
remove the custom panel background. Playwright verifies that the colored patches
are absent from print media when the override is enabled while the on-screen
background remains. Pinning `streamlit==1.66.0` also avoids the 1.67.0 height
expansion.

## Classification

- **Type:** Bug (print-layout regression; reporter's exact CSS unknown)
- **Status:** Confirmed synthetically on 1.67.0 and bracketed against 1.66.0
- **Areas:** Frontend, print layout, app/sidebar/block containers
- **Priority:** P2 — the screenshot shows a noticeable print/PDF visual
  regression introduced in 1.67.0, which the prioritization guide places at
  least at P2, while the print-only path and missing source app keep it below P1.
- **Fix complexity:** Medium — likely a scoped print-CSS correction after the
  source-app trigger is available, but the 1.67.0 rules intentionally coordinate
  sidebar, block, chart, and dataframe printing.
- **Confidence:** Medium — the release-specific layout mechanism and patch-like
  result are deterministic, but the reporter's exact CSS is unavailable.

## Evidence

- `reporter_screenshot.png` — screenshot attached to the issue
- `screen_1.66.0.png`, `screen_1.67.0.png` — normal media
- `print_1.66.0.png`, `print_1.67.0.png` — print media
- `print_1.66.0.pdf`, `print_1.67.0.pdf` — generated PDFs
- `print_geometry_1.66.0.json`, `print_geometry_1.67.0.json` — computed print
  geometry and styles
- `server_1.66.0.log`, `server_1.67.0.log` — released-wheel server logs
- `synthetic_minimal_printmedia_1.66.0.png`,
  `synthetic_minimal_printmedia_1.67.0.png` — minimized release comparison
- `synthetic_minimal_1.66.0.pdf`, `synthetic_minimal_1.67.0.pdf` — paginated
  Chromium PDFs
- `synthetic_minimal_results.json` — computed panel and color bounds
- `SYNTHETIC_FINDINGS.md` — full variant matrix and mechanism analysis
