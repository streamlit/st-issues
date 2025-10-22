"""
Playwright test for GitHub Issue #12846
This test automates verification of the bug reproduction.

Expected: st.dataframe should accept width='stretch' parameter without errors
Actual: TypeError: 'str' object cannot be interpreted as an integer

This test should PASS when the bug is fixed (no TypeError occurs).
This test should FAIL when the bug exists (TypeError occurs).
"""

from playwright.sync_api import Page, expect

from e2e_playwright.conftest import wait_for_app_loaded


def test_issue_12846_width_stretch_with_fragment(app: Page):
    """
    Test that st.dataframe with width='stretch' works inside a fragment.
    
    This is the exact scenario from the issue report.
    Should PASS when bug is fixed (no error message displayed).
    Should FAIL when bug exists (error message shown).
    """
    wait_for_app_loaded(app)
    
    # Look for the success message from Test 1 (fragment test)
    # If bug exists, there will be an error element instead
    test1_section = app.get_by_text("Test 1: Using width='stretch'")
    expect(test1_section).to_be_visible()
    
    # Check that no error occurred in Test 1
    # The app shows an error element with "TypeError occurred" if bug exists
    # Using locator with has filter to check within the test section context
    test1_error = app.locator("text=❌ TypeError occurred").first
    
    # Bug exists if we see the error message
    # Test should fail when bug exists, so we expect NO error to be visible
    expect(test1_error).not_to_be_visible()
    
    # Confirm success message is shown instead
    test1_success = app.locator("text=✅ Test passed - width='stretch' works correctly").first
    expect(test1_success).to_be_visible()


def test_issue_12846_width_stretch_no_fragment(app: Page):
    """
    Test that st.dataframe with width='stretch' works without fragment.
    
    Should PASS when bug is fixed.
    Should FAIL when bug exists.
    """
    wait_for_app_loaded(app)
    
    # Check Test 2 (without fragment)
    test2_section = app.get_by_text("Test 2: Using width='stretch' without fragment")
    expect(test2_section).to_be_visible()
    
    # No error should be shown
    test2_error = app.locator("text=❌ TypeError occurred").nth(1)
    expect(test2_error).not_to_be_visible()
    
    # Success message should be visible
    test2_success = app.locator("text=✅ Test passed - width='stretch' works without fragment").first
    expect(test2_success).to_be_visible()


def test_issue_12846_deprecated_use_container_width(app: Page):
    """
    Test that the deprecated use_container_width=True still works.
    
    This should work regardless of the width='stretch' bug.
    """
    wait_for_app_loaded(app)
    
    # Check Test 3 (deprecated parameter)
    test3_section = app.get_by_text("Test 3: Using use_container_width=True")
    expect(test3_section).to_be_visible()
    
    # Should show success
    test3_success = app.locator("text=✅ Test passed - use_container_width=True still works").first
    expect(test3_success).to_be_visible()


def test_issue_12846_width_content(app: Page):
    """
    Test that width='content' parameter works.
    
    This tests another new width option to ensure it's not affected.
    """
    wait_for_app_loaded(app)
    
    # Check Test 4 (width='content')
    test4_section = app.get_by_text("Test 4: Using width='content'")
    expect(test4_section).to_be_visible()
    
    # Should show success
    test4_success = app.locator("text=✅ Test passed - width='content' works").first
    expect(test4_success).to_be_visible()


def test_issue_12846_width_integer(app: Page):
    """
    Test that integer width parameter still works.
    
    This ensures the basic width functionality isn't broken.
    """
    wait_for_app_loaded(app)
    
    # Check Test 5 (integer width)
    test5_section = app.get_by_text("Test 5: Using width as integer")
    expect(test5_section).to_be_visible()
    
    # Should show success
    test5_success = app.locator("text=✅ Test passed - width=500 (integer) works").first
    expect(test5_success).to_be_visible()


def test_issue_12846_all_tests_pass(app: Page):
    """
    Comprehensive test that all width parameter variants work correctly.
    
    This test verifies that:
    1. width='stretch' works (with and without fragment)
    2. width='content' works
    3. width=<int> works
    4. use_container_width=True still works (deprecated)
    
    Should PASS when all variants work correctly (bug fixed).
    Should FAIL if any variant throws TypeError (bug exists).
    """
    wait_for_app_loaded(app)
    
    # Count all success messages (should be 5)
    success_messages = app.locator("text=/✅ Test passed/")
    expect(success_messages).to_have_count(5)
    
    # Count all error messages (should be 0)
    error_messages = app.locator("text=/❌.*TypeError/")
    expect(error_messages).to_have_count(0)

