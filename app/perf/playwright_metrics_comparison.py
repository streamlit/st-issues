import json

import pandas as pd
import streamlit as st

from app.perf.utils.perf_traces import (
    get_phases_for_all_profiles,
    sum_long_animation_frames,
)

TITLE = "Streamlit Performance - Playwright Metrics Comparison"

st.set_page_config(page_title=TITLE)

st.header(TITLE)


@st.cache_data
def get_metrics_data(all_phases, file_1_calculations, file_2_calculations):
    # Create a DataFrame for the metrics
    metrics_data = {
        "Profile": [],
        "Metric": [],
        "Run 1": [],
        "Run 2": [],
        "Difference": [],
    }

    for profile in all_profiles:
        for phase in all_phases:
            metrics_data["Profile"].extend([profile] * 2)
            metrics_data["Metric"].extend(
                [
                    f"{phase} - Duration (ms)",
                    f"{phase} - Count",
                ]
            )
            metrics_data["Run 1"].extend(
                [
                    file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("actualDuration", 0),
                    file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("count", 0),
                ]
            )
            metrics_data["Run 2"].extend(
                [
                    file_2_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("actualDuration", 0),
                    file_2_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("count", 0),
                ]
            )
            metrics_data["Difference"].extend(
                [
                    file_2_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("actualDuration", 0)
                    - file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("actualDuration", 0),
                    file_2_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("count", 0)
                    - file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("count", 0),
                ]
            )

    return metrics_data


upload_row = st.container(horizontal=True, gap="medium")
run1 = upload_row.container(width=500)
run2 = upload_row.container(width=500)

with run1:
    file_1 = st.file_uploader("Run 1 (Baseline)", type=["json"])

with run2:
    file_2 = st.file_uploader("Run 2 (Treatment)", type=["json"])

if not file_1 or not file_2:
    st.stop()

file_1_as_dict = json.loads(file_1.getvalue().decode("utf-8"))
file_2_as_dict = json.loads(file_2.getvalue().decode("utf-8"))

file_1_calculations = {
    "long_animation_frames": sum_long_animation_frames(file_1_as_dict),
    "phases": get_phases_for_all_profiles(file_1_as_dict),
}

file_2_calculations = {
    "long_animation_frames": sum_long_animation_frames(file_2_as_dict),
    "phases": get_phases_for_all_profiles(file_2_as_dict),
}

all_phases = set()
all_profiles = set(file_1_calculations["phases"].keys()).union(
    file_2_calculations["phases"].keys()
)

for profile in all_profiles:
    all_phases.update(file_1_calculations["phases"].get(profile, {}).keys())
    all_phases.update(file_2_calculations["phases"].get(profile, {}).keys())


metrics_data = get_metrics_data(all_phases, file_1_calculations, file_2_calculations)

data_view = st.segmented_control(
    "Comparison View", ["Breakdown", "Table"], default="Breakdown"
)

if data_view == "Table":
    st.dataframe(pd.DataFrame(metrics_data))

if data_view == "Breakdown":
    total_duration_run1 = round(
        sum(
            file_1_calculations["phases"]
            .get(profile, {})
            .get(phase, {})
            .get("actualDuration", 0)
            for profile in all_profiles
            for phase in all_phases
        ),
        2,
    )
    total_duration_run2 = round(
        sum(
            file_2_calculations["phases"]
            .get(profile, {})
            .get(phase, {})
            .get("actualDuration", 0)
            for profile in all_profiles
            for phase in all_phases
        ),
        2,
    )
    total_count_run1 = round(
        sum(
            file_1_calculations["phases"]
            .get(profile, {})
            .get(phase, {})
            .get("count", 0)
            for profile in all_profiles
            for phase in all_phases
        ),
        2,
    )
    total_count_run2 = round(
        sum(
            file_2_calculations["phases"]
            .get(profile, {})
            .get(phase, {})
            .get("count", 0)
            for profile in all_profiles
            for phase in all_phases
        ),
        2,
    )

    duration_diff = total_duration_run2 - total_duration_run1
    duration_percentage = (
        (duration_diff / total_duration_run1) * 100 if total_duration_run1 != 0 else 0
    )
    count_diff = total_count_run2 - total_count_run1
    count_percentage = (
        (count_diff / total_count_run1) * 100 if total_count_run1 != 0 else 0
    )

    st.write(
        f"""
### Comparison between Run 1 and Run 2

**Total Duration:**
- Run 1: `{total_duration_run1}ms`
- Run 2: `{total_duration_run2}ms`
- Difference: `{round(duration_diff, 2)}ms` ({'🐢 slower' if duration_diff > 0 else '🚀 faster' if duration_diff < 0 else '⏸️ unchanged'} by `{abs(round(duration_percentage, 2))}%`)

**Total Count:**
- Run 1: `{total_count_run1}`
- Run 2: `{total_count_run2}`
- Difference: `{round(count_diff, 2)}` ({'🔺 more' if count_diff > 0 else '🔻 fewer' if count_diff < 0 else '⏸️ unchanged'} by `{abs(round(count_percentage, 2))}%`)

#### Phase-wise Comparison:
        """
    )

    for i, profile in enumerate(all_profiles):
        for j, phase in enumerate(all_phases):
            index = 2 * (i * len(all_phases) + j)
            if index + 1 < len(metrics_data["Difference"]):
                duration_diff = round(metrics_data["Difference"][index], 2)
                count_diff = round(metrics_data["Difference"][index + 1], 2)
                duration_percentage = (
                    duration_diff
                    / file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("actualDuration", 1)
                ) * 100
                count_percentage = (
                    count_diff
                    / file_1_calculations["phases"]
                    .get(profile, {})
                    .get(phase, {})
                    .get("count", 1)
                ) * 100
                st.write(
                    f"""
    **Profile: {profile}, Phase: {phase}**
    - Duration Difference: `{duration_diff}ms` ({'🐢 slower' if duration_diff > 0 else '🚀 faster' if duration_diff < 0 else '⏸️ unchanged'} by `{abs(round(duration_percentage, 2))}%`)
    - Count Difference: `{count_diff}` ({'🔺 more' if count_diff > 0 else '🔻 fewer' if count_diff < 0 else '⏸️ unchanged'} by `{abs(round(count_percentage, 2))}%`)
                    """
                )
            else:
                st.write(f"**Profile: {profile}, Phase: {phase}** - Data not available")
