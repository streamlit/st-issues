# Issue #12745 Analysis: Expected Behavior vs Bug

## Issue Summary

When using `st.data_editor` with session_state storage, if a user first inputs integer values and then tries to change them to floats, the data editor prevents entering decimal points. This occurs even when using `st.column_config.NumberColumn(format='%.1f')`.

## Technical Analysis

### How st.data_editor Type Inference Works

**Current Behavior:**

1. `st.data_editor` infers column types from the **pandas DataFrame's dtype**, not from the `column_config`
2. `st.column_config.NumberColumn(format='%.1f')` is primarily for **display formatting**, not type enforcement
3. When the DataFrame has `int64` dtype, the editor treats it as an integer column (no decimal input)
4. When the DataFrame has `float64` dtype, the editor allows decimal input

### What Happens in This Issue

**Step-by-step breakdown:**

1. User starts with `pd.DataFrame(data=[None, None], columns=['number'])` - dtype is likely `object` or `float64`
2. User enters integers (e.g., 1, 2) → pandas automatically coerces to `int64` dtype (since all values are integers)
3. DataFrame with `int64` dtype is stored in session_state
4. On next run, `st.data_editor` receives DataFrame with `int64` dtype
5. Editor sees `int64` → treats as integer column → blocks decimal input
6. The `NumberColumn(format='%.1f')` doesn't override this behavior because it's just a display formatter

## Assessment: Unintuitive Behavior (Possibly a Bug)

### Arguments for This Being a Bug

1. **User Expectation Mismatch:** When users specify `NumberColumn(format='%.1f')`, they reasonably expect to be able to enter float values. The format parameter strongly implies float support.

2. **Column Config Should Have Influence:** The column config should have more influence on the column's editing behavior, not just display formatting. Otherwise, the `format` parameter is misleading.

3. **Poor Documentation:** The tight coupling between DataFrame dtype and input behavior is not well-documented in the API. Users have no way to know this will happen.

4. **Usability Issue:** Users shouldn't need to manually manage dtype conversions to get expected behavior. This creates cognitive overhead and is error-prone.

5. **Inconsistent with Streamlit Philosophy:** Streamlit usually "just works" without requiring deep knowledge of implementation details like pandas dtype coercion.

### Arguments for This Being Expected Behavior

1. **DataFrame Fidelity:** If Streamlit's philosophy is that `st.data_editor` is strictly a DataFrame editor that respects the DataFrame's types, then this is consistent.

2. **Pandas Behavior:** This is technically pandas' behavior (auto-coercing to int64 when all values are integers), and Streamlit is respecting that.

3. **Column Config as Display-Only:** If column config is explicitly documented as display-only, then this is working as designed.

## Reproduction App Status

✅ **App Successfully Demonstrates the Issue**

- The reproduction clearly shows the problem
- Includes working workarounds for comparison
- Well-documented with clear instructions

## Workarounds Provided

The app demonstrates two effective workarounds:

1. **Explicit Float Conversion:**

   ```python
   def btn_on_click():
       st.session_state.df_input = df_result.astype({'number': 'float'})
   ```

2. **Initialize with Float Type:**
   ```python
   pd.DataFrame(data=[None, None], columns=['number'], dtype='float64')
   ```

## Recommendation

### For Streamlit Team

This issue requires team discussion to determine:

1. Is this the intended behavior?
2. Should `NumberColumn(format='%.1f')` enforce float dtype, not just format display?
3. Should documentation be improved to explain dtype inference behavior?

### Potential Solutions

If considered a bug, possible fixes:

1. Make `NumberColumn` with float format preserve/enforce float dtype
2. Add a `dtype` parameter to `NumberColumn` for explicit type specification
3. Add warning when column config format doesn't match DataFrame dtype
4. Improve documentation about dtype inference and column editing behavior

## Next Steps

- [ ] Await Streamlit team decision on expected behavior
- [ ] If bug: Track fix in development
- [ ] If expected: Update documentation to clarify this behavior
- [ ] Consider adding `dtype` enforcement option to column configs

---

**Created:** 2025-01-13
**Status:** Pending team review
**App URL:** https://issues.streamlitapp.com/gh-12745
