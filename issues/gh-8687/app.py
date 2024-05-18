import streamlit as st

st.code("""
--- main
+++ develop
@@ -52,21 +52,19 @@
     "title": "Democracy index",
     "yAxis": {
         "max": 10,
-        "min": -10,
-        "facetDomain": "shared"
+        "min": -10
     },
""",
language="diff"
)
