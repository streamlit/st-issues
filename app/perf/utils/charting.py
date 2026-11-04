# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2025)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from collections.abc import Sequence
from typing import Any

import pandas as pd

from app.utils import echarts as ec


def run_distribution_chart(
    points: pd.DataFrame,
    *,
    runs: Sequence[str],
    value: str,
    value_label: str,
    stats: pd.DataFrame | None = None,
    mean: pd.DataFrame | None = None,
    title: str | None = None,
    y_title: str | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    tooltip_dims: Sequence[str] = (),
) -> dict[str, Any]:
    """Build an ECharts option with one category per run (oldest first).

    Draws the selectable ``points`` (``run`` and ``value``) over an optional box
    plot (``stats`` with ``run``, ``low``, ``q1``, ``median``, ``q3``, ``high``)
    and an optional mean line (``mean`` with ``run`` and ``mean``). Only the
    points are selectable, so selections map to ``points`` rows.
    """
    datasets: list[dict[str, Any]] = [{"source": points.reset_index(drop=True)}]
    series: list[dict[str, Any]] = [
        {
            "type": "scatter",
            "name": value_label,
            "datasetIndex": 0,
            "encode": {"x": "run", "y": value},
            "tooltip": ec.item_tooltip([value, *tooltip_dims], labels={value: value_label}),
            "selectedMode": "single",
            "symbolSize": 6,
            "itemStyle": {"opacity": 0.6},
            "z": 3,
        }
    ]
    if stats is not None and not stats.empty:
        datasets.append({"source": stats.reset_index(drop=True)})
        series.append(
            {
                "type": "boxplot",
                "name": "Distribution",
                "datasetIndex": len(datasets) - 1,
                "encode": {"x": "run", "y": ["low", "q1", "median", "q3", "high"]},
                "z": 1,
            }
        )
    if mean is not None and not mean.empty:
        datasets.append({"source": mean.reset_index(drop=True)})
        series.append(
            {
                "type": "line",
                "name": "Mean",
                "datasetIndex": len(datasets) - 1,
                "encode": {"x": "run", "y": "mean"},
                "showSymbol": False,
                "z": 2,
            }
        )

    y_axis: dict[str, Any] = {"type": "value", "scale": True}
    if y_title:
        y_axis["name"] = y_title
    if y_min is not None:
        y_axis["min"] = y_min
        y_axis.setdefault("axisLabel", {})["showMinLabel"] = False
    if y_max is not None:
        y_axis["max"] = y_max
        y_axis.setdefault("axisLabel", {})["showMaxLabel"] = False

    option: dict[str, Any] = {
        "dataset": datasets,
        "tooltip": {"trigger": "item"},
        "grid": {"top": 48 if title else 32, "left": 8, "right": 16},
        "xAxis": {"type": "category", "data": list(runs), "name": "Commit", "axisLabel": {"rotate": 45}},
        "yAxis": y_axis,
        "series": series,
    }
    if title:
        option["title"] = {"text": title, "textStyle": {"fontSize": 14, "width": 460, "overflow": "truncate"}}
    return option


def make_gantt_entry(
    now: datetime.datetime, measurement: dict[str, Any], task_name: str, location: str
) -> dict[str, Any]:
    """Create a Gantt chart entry.

    Args:
        now: The current datetime.
        measurement: A dictionary containing measurement data.
        task_name: The name of the task.
        location: The location of the task.

    Returns:
        A dictionary representing a Gantt chart entry.
    """
    start_time = now + datetime.timedelta(milliseconds=measurement["startTime"])
    finish_time = now + datetime.timedelta(milliseconds=measurement["startTime"] + measurement["duration"])

    return {
        "Task": task_name,
        "Start": start_time,
        "Finish": finish_time,
        "Location": location,
    }
