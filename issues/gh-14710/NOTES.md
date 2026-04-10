# Notes: #14710 — CCv2 setTriggerValue dropped on mount

## Summary

Reporter calls `setTriggerValue` synchronously on mount from multiple CCv2
component instances. Values are sent from JS (confirmed via console.log) but
Python intermittently receives `None`. With multiple instances, only the last
one's trigger survives.

## Reporter's code issues

1. Missing `on_get_cookies_change` callback — without it, trigger values are
   never surfaced on the result object regardless of timing.
2. Using `setTriggerValue` on mount — all documented examples call it from user
   interaction handlers (clicks, form submissions), not on mount. `setStateValue`
   is the right tool for initialization data.

## Root cause: coalescing gap

When multiple component instances fire `setTriggerValue` at slightly different
times, each trigger is sent as a separate `rerunScript` BackMsg. If these queue
up while a script run is active, `_coalesce_widget_states` in
`lib/streamlit/runtime/scriptrunner_utils/script_requests.py` merges them.

The preservation list only covers:
- `trigger_value` (boolean — `st.button`) ✓
- `chat_input_value` (`st.chat_input`) ✓

Missing:
- `json_trigger_value` (CCv2 `setTriggerValue`) ✗
- `string_trigger_value` ✗

Earlier triggers are silently dropped during the merge.

## Reproduction

The app in `app.py` uses 4 CCv2 instances with staggered `setTimeout` delays
(0/50/100/150ms) to force triggers into separate macrotasks. After reload, only
the last instance's trigger survives. The workaround section shows the same 4
instances using `setStateValue` — all 4 succeed every time.

## Proposed fix

Add `json_trigger_value` and `string_trigger_value` to the `trigger_value_types`
list in `_coalesce_widget_states`. Main consideration: merge semantics when the
same widget ID has JSON triggers in both old and new messages (unlikely in
practice since the frontend deletes triggers after flushing, but needs handling).

## Open question for Bob

Is this a bug we should fix, or is it expected/by-design given that
`setTriggerValue` is intended for user-driven events? Even with the documented
use case, two component instances triggering at similar times (e.g., rapid
clicks on two different CCv2 buttons) could hit the same coalescing loss — just
much harder to trigger than the mount scenario.

## Links

- Issue: https://github.com/streamlit/streamlit/issues/14710
- Analysis: `work-tmp/bugfix/gh-14710/analysis.md` (in streamlit repo)
