# gh-17082: GlobalHotkeys crashes on keydown/keyup events without a key

## Summary

`GlobalHotkeys` listens on `document` for `keydown`/`keyup` and immediately
calls `normalizeKey(event.key)`, which does `key.toLowerCase()`. A plain
`Event("keydown")` / `Event("keyup")` has no `key`, so the handler throws
`TypeError: Cannot read properties of undefined (reading 'toLowerCase')`.

## Finding

**Bug confirmed.** Reproduced with Playwright against released wheels
1.63.0 (reported) and 1.64.0 (latest). The same unguarded call is still on
`origin/develop` (`GlobalHotkeys.tsx`). 1.62.0 does **not** throw — this
regressed when `react-hot-keys` was replaced by `GlobalHotkeys` in #16655.

## Reproduction

Any Streamlit app is enough; the listeners are attached globally.

1. Load the app.
2. Dispatch keyless events:

   ```js
   document.dispatchEvent(new Event("keydown"))
   document.dispatchEvent(new Event("keyup"))
   ```

3. Playwright's `pageerror` handler records:

   `Cannot read properties of undefined (reading 'toLowerCase')`

| Version | Result |
| ------- | ------ |
| 1.62.0  | No throw |
| 1.63.0  | TypeError (confirmed) |
| 1.64.0  | TypeError (confirmed) |
| develop | Same unguarded `normalizeKey(event.key)` in source |

Screenshots: `repro_1.63.0.png` / `repro_1.64.0.png` (banner with the
TypeError) and `repro_1.62.0.png` (no error).

## Root Cause

`frontend/app/src/components/GlobalHotkeys/GlobalHotkeys.tsx` assumes every
dispatched event is a `KeyboardEvent` with a string `key`:

```ts
function normalizeKey(key: string): string {
  return key === "Escape" || key === "Esc" ? "esc" : key.toLowerCase()
}

const handleKeyDown = (event: KeyboardEvent): void => {
  const normalizedKey = normalizeKey(event.key)  // line 57
  // ...
}

const handleKeyUp = (event: KeyboardEvent): void => {
  const normalizedKey = normalizeKey(event.key)  // line 81
  // ...
}
```

Real `KeyboardEvent`s always have a string `key` (empty string if
unspecified), so normal typing is fine. The TypeScript annotation does not
protect against synthetic `Event` objects from hosts, extensions, or test
harnesses. Widget shortcut code already uses `event.key ?? ""`
(`useRegisterShortcut.ts`).

Introduced in `50a7e8c4a161dad3b2c88e4631d201c994428233`
([chore] Replace several frontend deps with in-house code (#16655)), first
released in 1.63.0.

**Fix direction:** return early in both handlers when
`typeof event.key !== "string"`. Add `GlobalHotkeys.test.tsx` cases that
dispatch keyless `keydown`/`keyup` and assert no exception and no shortcut
callback. `Dialog.tsx` also calls `e.key.toLowerCase()` unguarded on
capture-phase `keydown`; that is a related gap, not this issue.

## Classification

- **Type:** Bug
- **Status:** Confirmed on 1.63.0 and 1.64.0; absent on 1.62.0; still present on develop
- **Areas:** frontend, GlobalHotkeys / app-menu shortcuts
- **Priority:** P3 — uncaught exception on a document listener every app
  installs, but only when a synthetic event has no string `key`. Typical
  keyboard use is unaffected; reach is specific (hosts, extensions, test
  harnesses), so this is worth a small defensive fix without urgency.
- **Fix complexity:** Small — string guard in both handlers plus a unit test
