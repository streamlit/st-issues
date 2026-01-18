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

import json
import pathlib
from collections.abc import Iterable
from typing import Any, TypedDict

from app.perf.utils.types import (
    CalculatedPhases,
    CapturedTraces,
    LongAnimationFrame,
    Metric,
    Profile,
)


def get_long_animation_frames(
    file_as_dict: dict[str, CapturedTraces],
) -> list[LongAnimationFrame] | None:
    # Access using get() since "long-animation-frame" is not a valid Python identifier
    # but is the actual key in the JSON file. We need to cast because TypedDict can't
    # have hyphenated keys as valid Python identifiers.
    captured_traces = file_as_dict["capturedTraces"]
    result = captured_traces.get("long-animation-frame")  # type: ignore[typeddict-item]
    return result  # type: ignore[return-value]


def get_react_profiles(file_as_dict: dict[str, CapturedTraces], profile_name: str) -> Profile:
    profiles = file_as_dict["capturedTraces"].get("profiles")
    if profiles is None:
        return {"entries": [], "totalWrittenEntries": 0}
    return profiles.get(profile_name, {"entries": [], "totalWrittenEntries": 0})


def get_all_profile_names(file_as_dict: dict[str, CapturedTraces]) -> list[str]:
    profiles = file_as_dict["capturedTraces"].get("profiles")
    if profiles is None:
        return []
    return list(profiles.keys())


def calculate_phases(file_as_dict: dict[str, CapturedTraces], profile_name: str) -> CalculatedPhases:
    """Calculate phases for a specific profile from the given dictionary.

    Args:
        file_as_dict (Dict[str, CapturedTraces]): A dictionary containing JSON data.
        profile_name (str): The name of the profile to extract phases from.

    Returns:
        CalculatedPhases: A dictionary containing phases and their durations and counts.
    """
    profiles = get_react_profiles(file_as_dict, profile_name)
    phases: CalculatedPhases = {}

    for profile in profiles["entries"]:
        phase = profile["phase"]

        if phase not in phases:
            phases[phase] = {"duration_ms": 0.0, "count": 0}

        phases[phase]["duration_ms"] += profile["actualDuration"]
        phases[phase]["count"] += 1

    return phases


def calculate_phases_for_all_profiles(
    file_as_dict: dict[str, CapturedTraces],
) -> dict[str, CalculatedPhases]:
    """Calculate phases for all profiles from the given dictionary.

    Args:
        file_as_dict (Dict[str, CapturedTraces]): A dictionary containing JSON data.

    Returns:
        Dict[str, CalculatedPhases]: A dictionary containing phases for all profiles.
    """
    profile_names = get_all_profile_names(file_as_dict)
    return {profile_name: calculate_phases(file_as_dict, profile_name) for profile_name in profile_names}


def extract_react_profiles(file_as_dict: dict[str, Any], profile_name: str) -> dict[str, Any]:
    """Extract React profiles from the given file.

    Args:
        file_as_dict: A dictionary containing JSON data.
        profile_name: The name of the profile to extract.

    Returns:
        A dictionary containing the specified React profile.
    """
    return file_as_dict["capturedTraces"].get("profiles", {}).get(profile_name, {})


def get_phases(file_as_dict: dict[str, Any], profile_name: str) -> dict[str, Any]:
    """Get phases for a specific profile from the given file.

    Args:
        file_as_dict: A dictionary containing JSON data.
        profile_name: The name of the profile to extract phases from.

    Returns:
        A dictionary containing phases and their durations.
    """
    profiles = extract_react_profiles(file_as_dict, profile_name)

    if "entries" not in profiles:
        return {}

    phases: dict[str, Any] = {}
    for profile in profiles["entries"]:
        if profile["phase"] not in phases:
            phases[profile["phase"]] = {
                "actualDuration": 0,
                "baseDuration": 0,
                "count": 0,
            }

        phases[profile["phase"]]["actualDuration"] += profile["actualDuration"]
        phases[profile["phase"]]["baseDuration"] += profile["baseDuration"]
        phases[profile["phase"]]["count"] += 1

    return phases


def get_phases_for_all_profiles(file: dict[str, Any]) -> dict[str, Any]:
    """Get phases for all profiles from the given file.

    Args:
        file: A file-like object containing JSON data.

    Returns:
        A dictionary containing phases for all profiles.
    """
    profile_names = get_all_profile_names(file)  # type: ignore[arg-type]
    return {profile_name: get_phases(file, profile_name) for profile_name in profile_names}


def sum_long_animation_frames(
    file_as_dict: dict[str, CapturedTraces],
    first_mount_time: float | None = None,
) -> float:
    """Sum the durations of all long animation frames from the given dictionary.

    Only includes frames that occur after the first mount time if provided.

    We filter out frames that occur before the first mount because they appear to be
    artifacts from the Chrome DevTools Protocol initialization and browser setup,
    not related to actual Streamlit app performance.

    Args:
        file_as_dict (Dict[str, CapturedTraces]): A dictionary containing JSON data.
        first_mount_time (Optional[float]): Only include frames after this timestamp.
            Frames before this time are likely CDP initialization artifacts.

    Returns:
        float: The sum of durations of all long animation frames that occurred
            after the first mount.
    """
    long_animation_frames = get_long_animation_frames(file_as_dict)
    if long_animation_frames is None:
        return 0.0

    filtered_frames = long_animation_frames
    if first_mount_time is not None:
        filtered_frames = [frame for frame in long_animation_frames if frame.get("startTime", 0) >= first_mount_time]

    return sum(frame["duration"] for frame in filtered_frames)


def count_entries_per_phase(file_as_dict: dict[str, CapturedTraces], profile_name: str) -> dict[str, int]:
    """Count the number of entries per phase for a specific profile.

    Args:
        file_as_dict (Dict[str, CapturedTraces]): A dictionary containing JSON data.
        profile_name (str): The name of the profile to count entries for.

    Returns:
        Dict[str, int]: A dictionary with phases as keys and counts as values.
    """
    profiles = get_react_profiles(file_as_dict, profile_name)

    phase_counts: dict[str, int] = {}
    for profile in profiles["entries"]:
        phase = profile["phase"]
        if phase not in phase_counts:
            phase_counts[phase] = 0
        phase_counts[phase] += 1

    return phase_counts


class LoadFilesOutput(TypedDict):
    filenames: list[str]
    all_phases: list[dict[str, CalculatedPhases]]
    all_long_animation_frames: list[float]
    all_metrics: list[list[Metric]]
    first_mount_time: float | None


def load_files_from_dicts(
    files: Iterable[tuple[str, dict[str, Any]]],
) -> LoadFilesOutput:
    """In-memory variant of `load_files()`.

    This accepts already-parsed JSON dicts (e.g. from an artifact zip) and returns
    the same output shape as `load_files()`, without any filesystem access.
    """
    filenames: list[str] = []
    all_phases: list[dict[str, CalculatedPhases]] = []
    all_long_animation_frames: list[float] = []
    first_mount_time: float | None = None
    all_metrics: list[list[Metric]] = []

    for filename, file_content in files:
        phases = calculate_phases_for_all_profiles(file_content)

        # Find first mount time before calculating animation frames
        profiles = file_content["capturedTraces"].get("profiles", {})
        for profile_data in profiles.values():
            for entry in profile_data.get("entries", []):
                if entry["phase"] == "mount":
                    entry_time = entry.get("startTime", None)
                    if entry_time is not None and (first_mount_time is None or entry_time < first_mount_time):
                        first_mount_time = entry_time

        # Now sum animation frames with the mount time filter
        long_animation_frames_sum = sum_long_animation_frames(file_content, first_mount_time)

        filenames.append(filename)
        all_phases.append(phases)
        all_metrics.append(file_content.get("metrics", []))
        all_long_animation_frames.append(long_animation_frames_sum)

    return {
        "filenames": filenames,
        "all_phases": all_phases,
        "all_long_animation_frames": all_long_animation_frames,
        "first_mount_time": first_mount_time,
        "all_metrics": all_metrics,
    }


def load_files(
    directory_path: str,
) -> LoadFilesOutput:
    """Load files from the directory and extract relevant data.

    The function first determines the earliest mount time across all profiles,
    which serves as a baseline to filter out spurious long animation frames.
    Animation frames before the first mount are typically artifacts from
    Chrome DevTools Protocol initialization and not related to actual app performance.

    Args:
        directory_path (str): The path to the directory containing the files.

    Returns:
        LoadFilesOutput: A dictionary containing:
            - filenames: List of processed files
            - all_phases: Calculated phases for each file
            - all_long_animation_frames: Filtered animation frame durations
            - all_metrics: Tracked metrics for each file
            - first_mount_time: Timestamp of the earliest mount event
    """
    if not pathlib.Path(directory_path).exists():
        msg = f"The directory {directory_path} does not exist."
        raise FileNotFoundError(msg)

    filenames = []
    all_phases = []
    all_long_animation_frames = []
    first_mount_time = None
    all_metrics = []

    for file_path in pathlib.Path(directory_path).iterdir():
        if file_path.is_file() and file_path.name.endswith("json"):
            with file_path.open("r", encoding="utf-8") as file:
                file_content = json.load(file)

            phases = calculate_phases_for_all_profiles(file_content)

            # Find first mount time before calculating animation frames
            profiles = file_content["capturedTraces"].get("profiles", {})
            for profile_data in profiles.values():
                for entry in profile_data.get("entries", []):
                    if entry["phase"] == "mount":
                        entry_time = entry.get("startTime", None)
                        if entry_time is not None and (first_mount_time is None or entry_time < first_mount_time):
                            first_mount_time = entry_time

            # Now sum animation frames with the mount time filter
            long_animation_frames_sum = sum_long_animation_frames(file_content, first_mount_time)

            filenames.append(file_path.name)
            all_phases.append(phases)
            all_metrics.append(file_content["metrics"])
            all_long_animation_frames.append(long_animation_frames_sum)

    return {
        "filenames": filenames,
        "all_phases": all_phases,
        "all_long_animation_frames": all_long_animation_frames,
        "first_mount_time": first_mount_time,
        "all_metrics": all_metrics,
    }
