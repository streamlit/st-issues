"""
Reproduction for GitHub Issue #12792
Title: "Copy to Clipboard" button not work in st.code widget
Issue URL: https://github.com/streamlit/streamlit/issues/12792

Description:
This app reproduces the reported issue where the copy-to-clipboard button
in st.code widgets does not work when clicked. The button appears on hover
but clicking it does not copy the code to the clipboard.

Expected Behavior:
Clicking the copy button should copy the code text to the clipboard and
show a checkmark icon indicating success.

Actual Behavior (Reported):
Nothing happens when clicking the copy button. The clipboard remains unchanged.

Reported Version: Streamlit 1.50
Reported Environment: Linux (Tencent OS/CentOS), Chrome, Python 3.11.13

Test Results:
- Playwright tests PASS (cannot reproduce in automated tests)
- Issue appears to be ENVIRONMENT-SPECIFIC
"""

import streamlit as st

# === HEADER ===
st.title("Issue #12792: st.code Copy to Clipboard Not Working")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12792)")

# === IMPORTANT NOTICE ===
st.warning("""
⚠️ **Important Testing Note:**

Our automated tests **PASS** (clipboard works correctly), which suggests this is an
**environment-specific issue**. This could be caused by:
- HTTP vs HTTPS context (clipboard API requires secure context)
- Browser permissions or security policies
- Linux-specific clipboard handling
- Enterprise/corporate browser restrictions

**Please test this app and check your browser's developer console for errors!**
""")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("✅ Expected Behavior")
    st.write("""
    1. Hover over code block → copy button appears
    2. Click copy button → text copies to clipboard
    3. Button shows checkmark icon briefly
    4. Paste anywhere → code text appears
    """)

with col2:
    st.subheader("🐛 Reported Behavior")
    st.error("""
    1. Hover over code block → copy button appears ✓
    2. Click copy button → **nothing happens** ❌
    3. No visual feedback
    4. Clipboard remains unchanged
    """)

st.divider()

# === DIAGNOSTIC INSTRUCTIONS ===
st.header("🔍 How to Test This Issue")

st.markdown("""
**Step-by-step testing instructions:**

1. **Hover** over any code block below → you should see a copy button (📋) in the top-right
2. **Click** the copy button
3. **Try to paste** (Ctrl+V / Cmd+V) the code somewhere (e.g., a text editor)
4. **Open your browser's Developer Console** (F12 or right-click → Inspect → Console tab)
5. **Look for any errors** in the console (especially when clicking copy button)

**Expected Result:** Code should paste successfully, button should show checkmark briefly

**Bug Symptom:** Nothing is pasted, clipboard is unchanged
""")

# === DIAGNOSTIC CHECKLIST ===
with st.expander("📋 Diagnostic Checklist", expanded=True):
    st.markdown("""
    Please check the following and report back:

    - [ ] Are you running on **HTTP or HTTPS**? (Check URL bar)
    - [ ] Are you on **localhost** or a remote server?
    - [ ] Do you see **any errors in browser console** when clicking copy?
    - [ ] Does **manual copy-paste** work? (Select code with mouse, Ctrl+C)
    - [ ] Does copy work in **a different browser** (Firefox, Edge)?
    - [ ] What is your **Chrome version**? (chrome://version/)
    - [ ] Are you behind a **corporate firewall or using VPN**?
    - [ ] Do you have any **browser extensions** that might block clipboard access?
    """)

st.divider()

# === TEST CASES ===
st.header("🧪 Test Cases")

st.write("Try copying each code block below and report which ones work or don't work:")

# Test Case 1: Simple single-line
st.subheader("Test 1: Simple Single-Line Code")
st.write("**Code to copy:** `# This code is awesome!`")

code1 = "# This code is awesome!"
st.code(code1)

st.caption(
    "✅ After clicking copy, try pasting in a text editor. You should get the exact text above."
)

st.divider()

# Test Case 2: Multiline Python code
st.subheader("Test 2: Multiline Python Function")
st.write("**Code to copy:** Python function with indentation")

code2 = """def hello():
    print("Hello, Streamlit!")"""

st.code(code2, language="python")

st.caption("✅ After pasting, verify the indentation is preserved correctly.")

st.divider()

# Test Case 3: SQL (original user's example)
st.subheader("Test 3: SQL Query (Original User's Example)")
st.write("**Code to copy:** SQL query (same as reported in issue)")

formatted_sql = "select * from expdatabase.exptable limit 200;"
st.code(formatted_sql, language="sql")

st.caption("✅ This is the exact code from the original bug report.")

st.divider()

# Test Case 4: Longer code block
st.subheader("Test 4: Longer Multi-Line Code")
st.write("**Code to copy:** Longer Python code block")

code4 = """import streamlit as st
import pandas as pd

def process_data(df):
    # Process the dataframe
    df_clean = df.dropna()
    df_sorted = df_clean.sort_values('column')
    return df_sorted

# Main app
st.title("My App")
df = pd.read_csv("data.csv")
result = process_data(df)
st.dataframe(result)"""

st.code(code4, language="python")

st.caption("✅ Test with a longer code block to verify it handles multiline content.")

st.divider()

# === MANUAL TEST ===
st.header("🔬 Manual Verification Test")

st.write("""
To verify if the issue is with the copy button specifically or with clipboard access in general:

1. **Test manual copy-paste:** Try selecting the code below with your mouse and using Ctrl+C (Cmd+C):
""")

st.code("test manual copy paste", language="text")

st.write("2. **Paste it here:** Click in the text box and paste (Ctrl+V / Cmd+V):")

manual_paste = st.text_input("Paste the code here:", key="manual_paste")

if manual_paste:
    if manual_paste == "test manual copy paste":
        st.success("✅ Manual copy-paste works! Issue is specific to the copy button.")
    else:
        st.warning(f"⚠️ Pasted text doesn't match: `{manual_paste}`")

st.divider()

# === ENVIRONMENT INFO ===
st.header("💻 Environment Information")

st.write("**Your Current Environment:**")

col1, col2 = st.columns(2)

with col1:
    st.code(f"""Streamlit version: {st.__version__}
Python version: (check your terminal)""")

with col2:
    st.code("""Browser: (check browser settings)
OS: (check system info)
URL Protocol: (http:// or https://)""")

# === TECHNICAL DETAILS ===
with st.expander("🔧 Technical Details (for developers)"):
    st.markdown("""
    **Implementation Details:**

    - Copy button uses `navigator.clipboard.writeText()` API
    - This API requires a **secure context** (HTTPS or localhost)
    - Error logging is implemented in `useCopyToClipboard.ts` hook
    - Errors should appear in browser console if clipboard access is denied

    **Known Limitations:**

    - Clipboard API may be blocked by browser security policies
    - Some corporate/enterprise environments restrict clipboard access
    - HTTP (non-localhost) contexts will fail with modern browsers
    - Linux clipboard systems (X11/Wayland) can be complex

    **Related Code:**
    - Frontend: `frontend/lib/src/hooks/useCopyToClipboard.ts`
    - Component: `frontend/lib/src/components/elements/CodeBlock/CopyButton.tsx`
    - E2E Tests: `e2e_playwright/st_code_test.py` (tests PASS)
    """)

# === BROWSER CONSOLE INSTRUCTIONS ===
st.header("🖥️ How to Check Browser Console")

st.markdown("""
**Opening the Developer Console:**

1. **Chrome/Edge:** Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
2. **Firefox:** Press `F12` or `Ctrl+Shift+K` (Windows/Linux) or `Cmd+Option+K` (Mac)
3. Click the **Console** tab
4. Click the copy button on a code block above
5. **Look for red error messages** that appear after clicking

**What to report:**
- Any error messages that mention "clipboard", "permission", or "writeText"
- Screenshots of the console with errors visible
""")

st.image(
    "https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/static/img/console-example.png",
    caption="Example: Browser Console (look for red error messages)",
    use_container_width=True,
)

# === NEXT STEPS ===
st.header("📝 What to Report Back")

st.markdown("""
Please comment on the [GitHub issue](https://github.com/streamlit/streamlit/issues/12792) with:

1. ✅ **Which test cases work/don't work** (Test 1, 2, 3, 4 above)
2. 🔍 **Any browser console errors** (copy the exact error message)
3. 💻 **Your environment details:**
   - HTTP or HTTPS? (check URL bar)
   - Chrome version? (chrome://version/)
   - Exact Linux distribution and version
   - Are you on localhost or remote server?
4. 🧪 **Manual copy-paste test result** (does selecting + Ctrl+C work?)
5. 🌐 **Does it work in Firefox or another browser?**

This information will help us determine if this is a Streamlit bug or an environment-specific issue.
""")

# === WORKAROUND ===
st.divider()
st.header("🔄 Workaround")

st.write("""
**If the copy button doesn't work for you:**

Use manual copy-paste as a temporary workaround:
1. Select the code with your mouse
2. Press Ctrl+C (Windows/Linux) or Cmd+C (Mac)
3. Paste where needed

This should work in all environments, even if the copy button doesn't.
""")

# === FOOTER ===
st.divider()
st.caption("""
**Test Results Summary:**
- Automated Playwright tests: ✅ PASS (clipboard works correctly)
- Issue classification: Environment-specific (likely browser security/permissions)
- Related Issue: Not a duplicate of #8838 (that's about text modification)
- Test file: e2e_playwright/st_code_test.py (lines 216-293)
""")
