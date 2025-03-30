import os
import streamlit as st
import time
import numpy as np
import pandas as pd
from copy import deepcopy
import random

data_points = {}
references = {}
existing_entries = {}

CATEGORIES = ['cat1', 'cat2', 'cat3']
METRICS = ['metric1', 'metric2', 'metric3', 'metric4', 'metric5', 'metric6', 'metric7', 'metric8', 'metric9', 'metric10', 'metric11', 'metric12', 'metric13']
IMPACTS = ['impact1', 'impact2', 'impact3', 'impact4', 'impact5', 'impact6', 'impact7', 'impact8', 'impact9', 'impact10', 'impact11', 'impact12', 'impact13']
METRIC_ALIASES = {'metric1': 'm1', 'metric2': 'm2', 'metric3': 'm3', 'metric4': 'm4', 'metric5': 'm5', 'metric6': 'm6', 'metric7': 'm7', 'metric8': 'm8', 'metric9': 'm9', 'metric10': 'm10', 'metric11': 'm11', 'metric12': 'm12', 'metric13': 'm13'}
shift_types = ['percent', 'percent point']
shift_evolutions = ['constant', 'fade', 'rise']

for impact_name in IMPACTS:
    data_points[impact_name] = {
        metric: {
            category: {
                'shift_value': round(random.uniform(-1.0, 1.0), 3),
                'shift_type': random.choice(shift_types),
                'shift_evolution': random.choice(shift_evolutions),
                'shift_start': random.randint(0, 1000),
                'shift_end': random.randint(0, 1000),
                'version_start_conversion_week': '2023-W01',
                'version_end_conversion_week': '2023-W52',
                'version_start_delivery_week': '2023-W01',
                'version_end_delivery_week': '2023-W52'
            } for category in CATEGORIES
        } for metric in METRICS
    }

print(data_points)

def apply_references(entry_details, reference, metric):
    if reference != 'Define individually':
        for category in CATEGORIES:
            entry_details[metric][category] = deepcopy(entry_details[metric][reference])
    return entry_details

st.sidebar.button("test_widgets")

# Text input for creating a new entry
tab_side_test = st.sidebar
tab_side_test.text_input(
    label='Create New Entry',
    value='',
    placeholder='New Entry',
    key='new_entry'
)

# Create a form for assumptions
assumptions_form = tab_side_test.form('assumptions_form')

# Tabs for existing data points if available
if len(data_points.keys()):
    tabs_for_entries = assumptions_form.tabs(list(data_points.keys()))
else:
    tabs_for_entries = []

# Iterate over each tab (data point) to process details
for tab_idx, tab in enumerate(tabs_for_entries):
    entry_name = list(data_points.keys())[tab_idx]
    entry_details = data_points[entry_name]
    references[entry_name] = {}

    # entry_details['comment'] = tab.text_input(
    #     label=f'Comment:',
    #     value=entry_details['comment'],
    #     key=f'{entry_name}_comment'
    # )

    # Tabs for metrics inside each data point
    metric_tabs = tab.tabs(list(METRIC_ALIASES.values()))
    for metric_idx, metric_tab in enumerate(metric_tabs):
        metric = METRICS[metric_idx]
        metric_alias = list(METRIC_ALIASES.values())[metric_idx]

        # Drop-down for category definition
        references[entry_name][metric] = metric_tab.selectbox(
            'Category Definition',
            options=['Define individually'] + [f"Apply {category} to all" for category in CATEGORIES],
            index=0,
            key=f'category_{entry_name}_{metric_alias}'
        ).replace('Apply ', '').replace(' to all', '')

        # Iterate over categories
        category_tabs = metric_tab.tabs(CATEGORIES)
        for category_idx, category_tab in enumerate(category_tabs):
            category = CATEGORIES[category_idx]
            current_assumptions = deepcopy(entry_details[metric][category])

            # Numeric input for percentage value
            entry_details[metric][category]['shift_value'] = category_tab.number_input(
                label=f'Value % (e.g., 1.5%)',
                min_value=-1.000, max_value=1.000,
                step=1e-3,
                value=min(float(current_assumptions['shift_value']), 1.000),
                format="%.3f",
                key=f'{entry_name}_{metric}_{category}_shift_value'
            )

            # Drop-down for shift type
            entry_details[metric][category]['shift_type'] = category_tab.selectbox(
                'Shift Type',
                index=shift_types.index(current_assumptions['shift_type']),
                options=shift_types,
                format_func=lambda x: f'{x.capitalize()} of baseline' if x == 'percent' else x.capitalize(),
                key=f'{entry_name}_{metric}_{category}_shift_type'
            )

            # Drop-down for shift evolution
            entry_details[metric][category]['shift_evolution'] = category_tab.selectbox(
                'Shift Evolution',
                index=shift_evolutions.index(current_assumptions['shift_evolution']),
                options=shift_evolutions,
                format_func=lambda x: x.capitalize(),
                key=f'{entry_name}_{metric}_{category}_shift_evolution'
            )

            # Inputs for start and end values
            col1, col2 = category_tab.columns([1, 1])
            entry_details[metric][category]['shift_start'] = col1.number_input(
                label=f'Start Value:',
                min_value=0, max_value=1000,
                value=min(current_assumptions['shift_start'], 1000),
                step=1,
                key=f'{entry_name}_{metric}_{category}_shift_start'
            )
            entry_details[metric][category]['shift_end'] = col2.number_input(
                label=f'End Value:',
                min_value=0, max_value=1000,
                value=min(current_assumptions['shift_end'], 1000),
                step=1,
                key=f'{entry_name}_{metric}_{category}_shift_end'
            )

            # Additional fields for versioning
            col1.text_input(
                label=f'From Week:',
                value=current_assumptions['version_start_conversion_week'],
                key=f'{entry_name}_{metric}_{category}_version_start'
            )
            col2.text_input(
                label=f'To Week:',
                value=current_assumptions['version_end_conversion_week'],
                key=f'{entry_name}_{metric}_{category}_version_end'
            )

        # Apply category references
        entry_details = apply_references(entry_details, references[entry_name][metric], metric)

# Form submission button
assumptions_form.form_submit_button("Submit")
