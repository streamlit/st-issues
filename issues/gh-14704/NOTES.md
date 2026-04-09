# gh-14704: Namespace package import fails on rerun

## Summary

PEP 420 namespace packages (e.g. `bioimageio.spec` / `bioimageio.core`) fail on rerun with `AttributeError: module 'bioimageio' has no attribute 'spec'`. First run works; subsequent reruns after file changes crash.

## Root cause

**Partial eviction** of namespace package modules from `sys.modules` by `LocalSourcesWatcher.on_path_changed`.

When a namespace package spans local source (watched) and site-packages (blacklisted):
- `bioimageio` (namespace parent) → evicted (has local `_NamespacePath` component)
- `bioimageio.core` → evicted (local source under script folder)
- `bioimageio.spec` → **NOT evicted** (in site-packages, blacklisted by `**/site-packages`)

On rerun, Python creates a **new** `bioimageio` namespace module. When code does `import bioimageio.spec`, Python finds the old module in `sys.modules` and returns it via `_find_and_load()` — **without calling `setattr(parent, 'spec', module)`** on the new parent (that only happens in `_find_and_load_unlocked()`, which is skipped when the module is already cached). Subsequent attribute access `bioimageio.spec.__version__` fails because `spec` was never set on the new parent object.

**Key detail:** `from bioimageio.spec import X` does NOT trigger this bug (goes through `_handle_fromlist` which handles it). The bug requires `import bioimageio.spec` + attribute access `bioimageio.spec.X`.

**Location:** `lib/streamlit/watcher/local_sources_watcher.py`, `on_path_changed` lines 142–156.

## Reproduction

Fully reproduced both as pure Python simulation and through Streamlit's runtime.

**Repro structure** (in `streamlit` repo at `work-tmp/bugfix/gh-14704/repro2/`):
```
repro2/
├── app.py                          # Streamlit app
├── simulate_partial_eviction.py    # Pure-Python repro (no Streamlit needed)
├── local_pkg/                      # Simulates locally-developed package
│   └── myns/                       #   No __init__.py (namespace package)
│       └── core/
│           ├── __init__.py         #   Imports cli
│           └── cli.py              #   Does `import myns.spec` + attribute access
└── site-packages/                  # Simulates pip-installed package (blacklisted)
    └── myns/                       #   No __init__.py (namespace package)
        └── spec/
            └── __init__.py
```

**Pure Python repro:**
```bash
cd work-tmp/bugfix/gh-14704/repro2
uv run python simulate_partial_eviction.py
# → REPRODUCED BUG: AttributeError: module 'myns' has no attribute 'spec'
```

**Streamlit runtime repro:**
```bash
PYTHONPATH=work-tmp/bugfix/gh-14704/repro2/local_pkg \
  make debug work-tmp/bugfix/gh-14704/repro2/app.py
# Edit app.py → AttributeError on rerun
```

## Proposed fix

When evicting a module from `sys.modules`, also evict all children (keys starting with `modulename.`). This ensures orphaned children of evicted namespace parents are cleanly re-imported with proper `setattr` on the new parent.

```python
# In on_path_changed, after collecting modules_to_evict:
all_to_evict = set()
for name in modules_to_evict:
    all_to_evict.add(name)
    prefix = name + "."
    for key in sys.modules:
        if key.startswith(prefix):
            all_to_evict.add(key)
```

## Classification

- **Type:** Bug (reproduced)
- **Status:** Root cause confirmed, fix proposed
- **Areas:** backend, watcher, module reloading
- **Priority:** P3
- **Related:** #10992 (namespace `__path__` watching)
- **Key files:** `lib/streamlit/watcher/local_sources_watcher.py`
- **Analysis:** `streamlit` repo `work-tmp/bugfix/gh-14704/analysis.md`

## Repro app

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "site-packages"))

import myns.core
import myns.spec

import streamlit as st

st.write(f"myns.spec version: {myns.spec.__version__}")
st.write(f"myns.core version: {myns.core.__version__}")
st.write(f"cli label: {myns.core.cli._LABEL}")

# st.write("hello")  # Toggle this to trigger a rerun
```
