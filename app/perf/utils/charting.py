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
from typing import Any


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
