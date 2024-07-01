import streamlit as st
import json
import pandas as pd

# Define the data
data = {
    'age_group': ['18-35', '18-35', '36-50', '36-50', '51-65', '51-65', '65+', '65+'],
    'patient_gender': ['female', 'male', 'female', 'male', 'female', 'male', 'female', 'male'],
    'count': [783, 845, 748, 697, 737, 723, 232, 235]
}

VEGA_LITE_WRONG_SPECS=json.loads(
    """{
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Distribution of patients by age group and gender.",
        "layer": [
            {
            "selection": {
                "grid": {
                "type": "interval",
                "bind": "scales"
                }
            }
            }
        ],
        "encoding": {
            "x": {
            "field": "Age Group",
            "type": "nominal",
            "title": "Age Group",
            "axis": {"labelAngle": 0}
            },
            "y": {
            "field": "Count",
            "type": "quantitative",
            "title": "Patient Count"
            },
            "color": {
            "field": "Gender",
            "type": "nominal",
            "title": "Gender",
            "scale": {"scheme": "category10"}
            },
            "tooltip": [
            {"field": "Age Group", "type": "nominal", "title": "Age Group"},
            {"field": "Gender", "type": "nominal", "title": "Gender"},
            {"field": "Count", "type": "quantitative", "title": "Patient Count"}
            ]
        },
        "mark": {
            "type": "bar",
            "tooltip": true,
            "opacity": 0.7
        }
    }"""
)
try:
   st.vega_lite_chart(data, spec=VEGA_LITE_WRONG_SPECS)
except st.streamlit.errors.StreamlitAPIException as e:
   st.error(f"Error creating a chart: {str(e)}")

except Exception as e:
   st.error(f"Error creating a chart: {str(e)}")
