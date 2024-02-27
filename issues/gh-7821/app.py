import streamlit as st

table_html = f"""
<div style="position: relative;">
   <div id="copy-button-container">
        <button class="copy-button" id="btn-copy" style="float:right;">
            <img src="https://img.icons8.com/material-rounded/24/000000/copy.png"/>
        </button>
   </div>
   <table>
      <tr>
          <th>Calendar Year</th>
          <th>Volume</th>
     <tr>
     <tr>
          <th>12.32</th>
          <th>12.32</th>
     <tr>
   </table>
</div>
"""
    
# JavaScript code for clipboard.js
clipboard_js = """
    <script type="text/javascript">
        document.getElementById("btn-copy").addEventListener("click", function() {
            var table = document.getElementById('st-custom-table');
            var range = document.createRange();
            range.selectNode(table);
            window.getSelection().addRange(range);
            var successful = document.execCommand('copy');
            window.getSelection().removeAllRanges();
            if (successful) {
                alert('Table copied to clipboard!');
            } else {
                alert('Unable to copy table.');
            }
        });
    </script>
"""
# Display the custom CSS and JavaScript
st.components.v1.html(table_html + clipboard_js, scrolling=True)
