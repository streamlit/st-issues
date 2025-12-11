import datetime
import json

import plotly.express as px
import streamlit as st

from app.perf.utils.charting import make_gantt_entry
from app.perf.utils.docs import METRIC_DEFINITIONS
from app.perf.utils.perf_traces import (
    get_phases_for_all_profiles,
    sum_long_animation_frames,
)

TITLE = "Playwright Metrics Explorer"

DOCS = """
Every Performance job in CI, and any run of a performance job locally outputs json file artifacts that contain the captured traces from the Playwright run. This tool allows you to upload one of these json files and visualize the captured traces in a Gantt chart as well as understand the meaning of the key metrics.
"""

def render_metrics_explorer() -> None:
    with st.container(width="content"):
        st.markdown(DOCS)

    st.divider()

    json_file = st.file_uploader("Upload JSON File", type=["json"])


    if not json_file:
        st.stop()

    json_file_as_dict = json.loads(json_file.getvalue().decode("utf-8"))

    with st.expander("View JSON File"):
        st.json(json_file_as_dict)


    json_file_calculations = {
        "long_animation_frames": sum_long_animation_frames(json_file_as_dict),
        "phases": get_phases_for_all_profiles(json_file_as_dict),
    }


    @st.cache_data
    def get_json_data(the_file):
        return json.load(the_file)


    data = get_json_data(json_file)


    @st.cache_data
    def get_gantt_data(the_data):
        timestamp_parsed = datetime.datetime.strptime(
            json_file.name.split("_")[0], "%Y%m%d%H%M%S"
        )

        # Extract relevant data for the Gantt chart
        gantt_data = []

        for phase in the_data["capturedTraces"]["profiles"]:
            for entry in the_data["capturedTraces"]["profiles"][phase]["entries"]:
                start_time = timestamp_parsed + datetime.timedelta(
                    milliseconds=entry["startTime"]
                )
                finish_time = timestamp_parsed + datetime.timedelta(
                    milliseconds=entry["startTime"] + entry["actualDuration"]
                )
                gantt_data.append(
                    {
                        "Task": entry["phase"],
                        "Start": start_time,
                        "Finish": finish_time,
                        "Location": phase,
                    }
                )

        for measurement in the_data["capturedTraces"]["measure"]:
            if measurement["name"] == "script-run-cycle":
                gantt_data.append(
                    make_gantt_entry(
                        timestamp_parsed, measurement, "script-run-cycle", "Global"
                    )
                )

        TRACES = ["long-animation-frame"]

        for trace in TRACES:
            if trace in the_data["capturedTraces"]:
                for measurement in the_data["capturedTraces"][trace]:
                    gantt_data.append(
                        make_gantt_entry(timestamp_parsed, measurement, trace, "Global")
                    )

        all_start_times = [entry["Start"] for entry in gantt_data]
        all_finish_times = [entry["Finish"] for entry in gantt_data]

        return {
            "gantt_data": gantt_data,
            "start_time": min(all_start_times),
            "finish_time": max(all_finish_times),
        }

    gantt_data = get_gantt_data(data)

    # Create a Gantt chart
    fig = px.timeline(
        gantt_data["gantt_data"],
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Location",
        title="Performance Metrics",
    )
    # Update layout for better readability
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Measurement",
        xaxis=dict(range=[gantt_data["start_time"], gantt_data["finish_time"]]),
    )

    st.plotly_chart(fig, width="stretch")

    st.divider()

    with st.container(width="content"):
        with st.expander("Metric Definitions"):
            st.markdown(METRIC_DEFINITIONS)

    def check_mount_count(phase_values, profile_id):
        st.write("#### Mount")
        res = f"""
Total time spent in mount: `{round(phase_values["actualDuration"], 2)}ms`
"""

        if phase_values["count"] > 1:
            res += f"""
❌ {phase_values["count"]} mounts detected

This is problematic because it means that the entire `{profile_id}` subtree is
being unmounted and remounted. This is expensive and most likely unnecessary,
unless we are dealing with a full page transition/reload.
"""
        else:
            res += """
✅ Single mount detected
"""

        return res

    def check_nested_update(phase_values, profile_id):
        st.write("#### Nested Update")
        res = f"""
Total time spent in nested updates: `{round(phase_values["actualDuration"], 2)}ms`
"""

        if phase_values["count"] > 0:
            res += f"""
❌ {phase_values["count"]} nested updates detected

Nested updates are likely to cause performance issues since they are
synchronous. Expand the Metric Definitions section above for more information.
"""
        else:
            res += "✅ Single nested update detected"

        return res

    def check_update(phase_values, profile_id):
        st.write("#### Update")
        res = f"""
Total time spent in updates: `{round(phase_values["actualDuration"], 2)}ms`
"""

        if phase_values["count"] > 1:
            res += f"""
{phase_values["count"]} updates detected

Having updates is expected. But having too many updates could point to
performance issues. Expand the Metric Definitions section above for more
information.
"""
        else:
            res += "✅ Single update detected"

        return res

    checks = {
        "mount": check_mount_count,
        "update": check_update,
        "nested-update": check_nested_update,
    }

    profiles_grid = st.container(horizontal=True, gap="medium")

    for profile_id, values in json_file_calculations["phases"].items():
        tile = profiles_grid.container(border=False, width=500)
        with tile:
            st.write(f"### {profile_id}")
            for phase, phase_values in values.items():
                check = checks.get(phase)
                if check:
                    st.markdown(check(phase_values, phase))


def _standalone() -> None:
    st.set_page_config(page_title=f"Streamlit Performance - {TITLE}", layout="wide")
    st.header(f"Streamlit Performance - {TITLE}")
    render_metrics_explorer()


if __name__ == "__main__":
    _standalone()
