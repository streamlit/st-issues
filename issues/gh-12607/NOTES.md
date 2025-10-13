# Issue #12607 Notes: File Upload Memory Leak Reproduction

## Issue Summary

Uploaded files remain in RAM even after processing is complete and `clear_on_submit=True` is used. The RAM is only freed when the Streamlit instance is completely closed.

## Original Issue Report

**Symptoms:**

- 600MB file upload → RAM usage goes to ~660MB during upload
- RAM spikes to 1800MB during processing
- After upload completes, RAM stays at 660MB
- Closing browser tab doesn't free RAM
- Only closing Streamlit instance frees memory

**Failed Attempts:**

- `clear_on_submit=True`
- Working with session_state keys
- `gc.collect()`
- `st.rerun()`

**Workaround:**

- Set `clear_on_submit=False`
- Don't use `st.rerun()`
- Let users manually clear with ❌ button in widget
- Only then is RAM freed

## Enhanced Reproduction Strategy

Based on the approach used in [issue #6354](https://github.com/streamlit/streamlit/issues/6354) for memory leak testing, we should enhance the reproduction app to:

### 1. Add Memory Monitoring with psutil

Similar to #6354, we should use `psutil` to actively monitor and display memory usage:

```python
import psutil
import os

pid = os.getpid()

def get_memory_mb():
    """Get current memory usage in MB"""
    process = psutil.Process(pid)
    memory_usage = process.memory_info().rss
    return memory_usage / (1024 * 1024)
```

### 2. Continuous Monitoring Display

Add real-time memory monitoring:

```python
memory_placeholder = st.empty()
memory_placeholder.metric("Current RAM Usage", f"{get_memory_mb():.2f} MB")
```

Update this continuously to show memory increasing during upload and staying high after.

### 3. Multiple Upload Test

Similar to #6354's approach with image updates, test multiple file uploads in sequence:

```python
if "upload_count" not in st.session_state:
    st.session_state.upload_count = 0
    st.session_state.memory_history = []

# Track memory after each upload
st.session_state.memory_history.append({
    "upload": st.session_state.upload_count,
    "memory_mb": get_memory_mb()
})

# Display memory history chart
st.line_chart(memory_history)
```

### 4. Clear Test Protocol

**Step-by-step reproduction:**

1. Note initial memory usage
2. Upload a large file (>100MB)
3. Process the file
4. Note memory usage after processing
5. Repeat steps 2-4 multiple times
6. Show memory never decreases
7. Close browser tab
8. Show memory still high (only drops when Streamlit closes)

### 5. Visual Evidence

Add clear visual indicators:

- Memory usage graph over time
- Color coding: green (low), yellow (medium), red (high)
- Annotations showing when uploads happen
- Warning when memory exceeds threshold

## Current Reproduction App Status

The current app at `/issues/gh-12607/app.py` includes:

✅ **Good:**

- Clear description of the issue
- Form with `clear_on_submit=True`
- Attempts to free memory with `gc.collect()`
- Basic memory display with psutil (if installed)

⚠️ **Could Improve:**

- Add continuous memory monitoring
- Show multiple upload cycles
- Add memory history graph
- More explicit test protocol
- Visual indicators of memory growth

## Recommendation

The current app is functional but could be enhanced with the #6354 approach to make the memory leak more visually obvious. However, this enhancement is **optional** because:

1. The issue is real and well-documented in the original report
2. The current app demonstrates the problem
3. Memory monitoring requires manual observation (Task Manager/Activity Monitor)
4. Enhancement would make it easier to see but isn't required for reproduction

## Testing Protocol for Team Member

**To verify this issue:**

1. Open Task Manager (Windows) or Activity Monitor (Mac)
2. Note baseline Streamlit process memory
3. Upload a large file (>100MB recommended)
4. Click "Process File"
5. Observe memory increase
6. **Expected:** Memory should drop after processing
7. **Actual:** Memory stays high
8. Repeat upload 2-3 times - memory keeps growing
9. Close browser tab
10. **Expected:** Memory should drop
11. **Actual:** Memory stays high until Streamlit process ends

## Related Issues

- [#6354](https://github.com/streamlit/streamlit/issues/6354) - Similar memory leak with `st.image` updates
  - Shows approach for memory monitoring
  - Demonstrates memory leak visualization
  - Status: Labeled as `status:unlikely` (will probably not implement)

## Severity Assessment

**Impact:** High for certain use cases

- Apps handling large file uploads
- Multi-user production environments
- Long-running sessions
- Limited server resources

**Workaround Available:** Yes, but awkward

- Users must manually clear files with ❌ button
- Cannot use `clear_on_submit=True`
- Cannot use `st.rerun()` after upload
- Breaks expected workflow patterns

## Potential Root Cause

Similar to #6354 and the selectbox copying issue (#3703), this may be related to how Streamlit manages references to uploaded files for session_state and callback mechanisms. The files may be held in memory to support potential callbacks or state access even after the widget is cleared.

---

**Created:** 2025-01-13
**Status:** Ready for team verification
**App URL:** https://issues.streamlitapp.com/gh-12607
