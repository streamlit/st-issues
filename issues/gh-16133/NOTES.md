# gh-16133: multiselect cursor jumps to start after keyboard re-selection

## Summary

When an option is chosen in `st.multiselect` using the keyboard, the text
caret is placed correctly (at the end) on the first selection. After the user
clears the selection with **Escape** and selects again, the caret jumps to the
**beginning** of the input, so subsequently typed characters are inserted
before the existing content instead of after it.

## Reproduction

- **Version:** `streamlit>=1.60.0` (reported on 1.60.0).
- **Steps:**
  1. Click the multiselect to focus it.
  2. Type `Red`, press Enter.
  3. Press Escape twice (close dropdown + clear).
  4. Type `Red` again, press Enter.
  5. Keep typing — the caret is at the start of the input, not the end.
- **Browsers reported:** Edge, Opera, Firefox.

## Classification

- **Type:** Bug (frontend, keyboard/caret handling in the multiselect input).
- **Status:** Confirmed bug per the issue; marked as a regression.
- **Areas:** frontend — `Multiselect` widget input / React Aria combobox caret
  management.
- **Priority:** P3 (medium) per the issue triage — a keyboard-usability
  annoyance affecting a specific interaction sequence, with no data loss and a
  simple mouse-based workaround (click at the end of the input before typing).
