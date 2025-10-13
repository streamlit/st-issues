"""
Reproduction for GitHub Issue #12607
Title: After File Upload the file stays in RAM
Issue URL: https://github.com/streamlit/streamlit/issues/12607

Description:
When uploading files with st.file_uploader, the file remains in RAM even after
the upload is processed and clear_on_submit is set to True. The RAM is only
freed when the Streamlit instance is completely closed.

Expected Behavior:
After file upload and processing, the file should be removed from RAM when
clear_on_submit=True or when the uploader widget is cleared.

Actual Behavior:
- RAM usage increases during upload (as expected)
- After upload completion, file remains in RAM (~660MB for a 600MB file)
- Closing browser tab doesn't free the RAM
- Only closing the Streamlit instance frees the memory

Note: The workaround is to NOT use clear_on_submit and manually clear the
file using the X button in the widget.
"""

import gc
import os
import shutil
import sys
import tempfile
from datetime import datetime

import streamlit as st

st.title("Issue #12607: File Upload Memory Leak")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12607)")

st.header("Issue Description")

st.write("""
This app demonstrates the memory leak issue with `st.file_uploader`.
When `clear_on_submit=True`, uploaded files stay in RAM even after processing.
""")

st.divider()

st.header("Test Setup")

st.write("""
**To reproduce this issue:**
1. Monitor RAM usage before uploading (use Task Manager / Activity Monitor)
2. Upload a large file (>100MB recommended)
3. Click "Process File"
4. Observe RAM usage stays high even after processing
5. Close the browser tab - RAM usage still high
6. Only closing Streamlit completely frees the RAM
""")

st.divider()

# Initialize session state
if "upload_counter" not in st.session_state:
    st.session_state.upload_counter = 0

if "last_upload_size" not in st.session_state:
    st.session_state.last_upload_size = None

# Dynamic key for file uploader
file_key = f"file_upload_{st.session_state.upload_counter}"

st.header("File Upload Test")

with st.form("upload_form", clear_on_submit=True):
    uploaded_file = st.file_uploader(
        "Upload a file (larger files make the issue more visible)",
        type=["txt", "pdf", "jpg", "png", "zip"],
        key=file_key,
    )

    submitted = st.form_submit_button("Process File")

    if submitted:
        if uploaded_file is None:
            st.error("Please select a file.")
        else:
            file_size = uploaded_file.size
            st.session_state.last_upload_size = file_size

            # Simulate processing - save to temp location
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, f"streamlit_test_{uploaded_file.name}")

            with open(save_path, "wb") as f:
                shutil.copyfileobj(uploaded_file, f)

            st.success(f"File processed: {uploaded_file.name} ({file_size:,} bytes)")
            st.write(f"Saved to: {save_path}")

            # Attempt to free memory (this doesn't work due to the bug)
            del uploaded_file
            gc.collect()

            # Increment counter for next upload
            st.session_state.upload_counter += 1

            st.warning(
                "⚠️ **BUG:** The file is still in RAM even though we deleted "
                "it and called gc.collect()!"
            )

            st.rerun()

st.divider()

st.header("Memory Information")

col1, col2 = st.columns(2)

with col1:
    st.metric("Upload Counter", st.session_state.upload_counter)

with col2:
    if st.session_state.last_upload_size:
        st.metric(
            "Last Upload Size", f"{st.session_state.last_upload_size / 1024 / 1024:.2f} MB"
        )
    else:
        st.metric("Last Upload Size", "N/A")

# Show current Python process memory usage (requires psutil)
try:
    import psutil

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    st.metric("Current Process RAM", f"{mem_info.rss / 1024 / 1024:.2f} MB")
except ImportError:
    st.info(
        "Install `psutil` to see process memory usage: `pip install psutil`"
    )

st.divider()

st.header("Expected vs Actual")

st.write("""
**Expected:**
- After upload and processing, RAM should be freed
- `clear_on_submit=True` should clear the file from memory
- `gc.collect()` should release the memory

**Actual:**
- File remains in RAM (approximately the file size + overhead)
- `clear_on_submit=True` doesn't free memory
- Manual deletion + `gc.collect()` doesn't work
- Only closing Streamlit completely frees the memory
""")

st.divider()

st.header("Workaround")

st.write("""
The only workaround is to:
1. Set `clear_on_submit=False`
2. Do NOT use `st.rerun()`
3. Let users manually clear the file using the ❌ button in the widget
4. Only then will the RAM be freed
""")

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: {sys.version.split()[0]}
OS: Windows 11 / Linux / macOS
""")

st.divider()

st.header("Additional Notes")

st.write("""
- The issue is particularly problematic for apps that handle large files
- Server memory can grow indefinitely if multiple users upload files
- The issue has been confirmed across multiple browsers and operating systems
- Related to the internal `UploadedFileManager` implementation
""")

