# Investigation notes — Issue #15618

These notes capture what was found while reproducing
[streamlit/streamlit#15618](https://github.com/streamlit/streamlit/issues/15618).

## Summary of findings

Reproduced and root-caused on Streamlit **1.58.0** (current `develop`).

| Option type | `format_func` does dict lookup? | Widget state after selecting "two" | Value returned to script | Result |
|---|---|---|---|---|
| frozen `@dataclass` | yes | `two` | `one` | **bug** |
| plain class | yes | `two` | `one` | **bug** |
| `NamedTuple` | yes | `two` | `two` | ok |
| frozen `@dataclass` | no | `two` | `two` | ok |
| plain class | no | `two` | `two` | ok |
| `NamedTuple` | no | `two` | `two` | ok |

Key observations:

- The bug **does** occur for a frozen dataclass — it is not specific to plain
  classes. (Value-based `__hash__`/`__eq__` does **not** save it.)
- The widget's stored state is actually correct (`two`); the bug is that
  `st.selectbox(...)` **returns the wrong option** (`one`, the default) to the
  script. The UI then reflects that returned value, so it "reverts".
- Removing the dict lookup (any expression that hashes the option) from
  `format_func` makes all cases work.

## Root cause

The trace below comes from monkeypatching
`streamlit.elements.lib.options_selector_utils.validate_and_sync_value_with_options`
during an `AppTest` run after selecting the second option:

```
[validate] current='two' formatted="<raise KeyError(MyDataClass(id=2, name='two'))>" in_set=False set={'two','one'} -> returned='one' reset=True
markdown rendered: Selected: one
```

What happens, step by step:

1. The selected option is stored in session state as a `deepcopy`.
2. On the next rerun, the app script re-executes and **redefines the option
   class** (`MyDataClass` is declared at module scope, so a brand new class
   object is created each run).
3. `validate_and_sync_value_with_options` validates the stored value by calling
   the user's `format_func` on it. Here `format_func` does `x[s]`, a dict lookup
   keyed by the option.
4. The stored value is an instance of the **previous** run's class, while `x`'s
   keys are instances of the **current** run's class. A dataclass's generated
   `__eq__` requires `other.__class__ is self.__class__`, so the lookup misses
   and raises `KeyError`. (The hash matches — it is value-based — but `__eq__`
   is class-gated, so `in`/`[]` still fail.)
5. `validate_and_sync_value_with_options` wraps the `format_func` call in a broad
   `except Exception`, interpreting **any** failure as "value not in options",
   and resets the selection to the default index (0 → "one").

So the user-visible revert is caused by a user-code exception inside
`format_func` being swallowed and reinterpreted as an invalid selection.

### Why NamedTuple is immune

`NamedTuple` subclasses `tuple` and uses `tuple.__eq__`/`__hash__`, which compare
element-wise and are **not** gated on the class. A `NamedTuple` instance from a
previous run still equals one from the current run, so the dict lookup succeeds
and no exception is raised.

### Why removing the lookup fixes it

Without `x[s]`, `format_func` only reads `s.name` and never raises. The
validation step then finds the formatted value in the option set and keeps the
selection.

## Relevant code

- `lib/streamlit/elements/lib/options_selector_utils.py` —
  `validate_and_sync_value_with_options` (the broad `except Exception` that
  resets to default when `format_func` raises).
- `lib/streamlit/elements/widgets/selectbox.py` — `_selectbox` calls the
  validation helper (around the `validate_and_sync_value_with_options(...)`
  call) and returns its result.

## Suggested fix direction (for maintainers)

The validation step conflates two very different situations:

- the formatted value genuinely not being among the options, and
- the user's `format_func` raising an exception.

Only the first should trigger a silent reset. A user-code exception in
`format_func` should either propagate (so the user sees their own error) or at
least not cause the selection to be discarded. Narrowing the `except` and/or
validating option membership without depending on a side-effecting `format_func`
would address the regression.

## How this was verified

- Headless `AppTest` matrix across all six combinations (see table above).
- Monkeypatched trace of `validate_and_sync_value_with_options` to capture the
  swallowed `KeyError` and the reset.
- An earlier full-browser Playwright run (before the dev VM was reset) confirmed
  the same revert-to-"one" behavior in the actual UI.
