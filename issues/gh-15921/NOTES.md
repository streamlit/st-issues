# gh-15921: Keyboard focus indicator moves twice on file uploader

## Summary

The file uploader (`st.file_uploader`) exposes two consecutive keyboard focus
stops — the dropzone `<section>` and the **Upload** button inside it — even
though both trigger the same file-open action. This creates a redundant tab
stop for keyboard users.

## Finding

**Bug confirmed** on Streamlit 1.59.1 (latest release). Not limited to the
playground or the reporter's version (1.40.1).

## Reproduction

Reproduced on macOS with Chromium via Playwright. The tab order through a
`st.file_uploader("Upload a file")` widget is:

```
Tab N:   <SECTION>  testId=stFileUploaderDropzone  tabIndex=0  role=presentation
Tab N+1: <BUTTON>   testId=stBaseButton-secondary  tabIndex=0  text="Upload"
```

Both elements open the same file picker dialog, so the dropzone stop is
redundant.

## Root Cause

`FileDropzone.tsx` spreads `{...getRootProps()}` on the dropzone `<section>`.
react-dropzone populates `getRootProps()` with `tabIndex: 0` (and
`role: "presentation"`) by default. The **Upload** `<button>` inside is a
native focusable element. Since Streamlit passes neither `noKeyboard` nor
`tabIndex: -1` to `getRootProps()`, both elements appear in the keyboard tab
order.

Relevant code:

```
frontend/lib/src/components/widgets/FileUploader/FileDropzone.tsx:75-82
```

## Classification

- **Type:** Bug (accessibility)
- **Status:** Confirmed on latest release (1.59.1)
- **Areas:** frontend, FileUploader / FileDropzone, react-dropzone integration
- **Priority:** Low — cosmetic keyboard-nav issue, doesn't block functionality
- **Fix complexity:** Small — pass `{ tabIndex: -1 }` to `getRootProps()` or
  set `noKeyboard: true` on the `useDropzone` hook
