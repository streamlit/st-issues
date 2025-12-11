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

import sys
import warnings
from typing import Dict, List, TypedDict

from scipy import stats  # type: ignore

from .perf_traces import load_files
from .test_run_utils import get_stable_test_name
from .types import CalculatedPhases

ProcessTestDirectoryOutput = Dict[str, Dict[str, List[float]]]


class TestMetrics(TypedDict):
    t_stat: float
    p_value: float
    baseline_metrics: List[float]
    treatment_metrics: List[float]


StatisticalDiff = Dict[str, Dict[str, TestMetrics]]


class AnalyzedTestDiffResults(TypedDict):
    regression_count: int
    improvement_count: int
    no_change_count: int


def _extract_react_profile_metrics(
    all_phases: List[Dict[str, CalculatedPhases]],
    index: int,
    react_profile_key: str,
    phase: str,
    results_per_test: ProcessTestDirectoryOutput,
    stable_test_name: str,
) -> None:
    """
    Extracts metrics from the test phases and updates the results dictionary.

    Args:
        all_phases (List[Dict[str, CalculatedPhases]]): All phases data.
        index (int): Index of the current test file.
        react_profile_key (str): React profile key.
        phase (str): Phase of the test.
        results_per_test (ProcessTestDirectoryOutput): Dictionary to store the results.
        stable_test_name (str): Stable test name.
    """
    metrics = all_phases[index][react_profile_key][phase].keys()
    for metric in metrics:
        key = f"{react_profile_key}__{phase}__{metric}"
        if key not in results_per_test[stable_test_name]:
            results_per_test[stable_test_name][key] = []
        results_per_test[stable_test_name][key].append(
            all_phases[index][react_profile_key][phase][metric]  # type: ignore
        )


def process_test_results_directory(
    directory: str, load_all_metrics: bool = False
) -> ProcessTestDirectoryOutput:
    """
    Processes the directory of test result information by returning a dictionary
    where the key is the test name and the value is a dictionary of metrics.

    Args:
        directory (str): The directory.

    Returns:
        ProcessTestDirectoryOutput: A dictionary where the key is the test name and the value is a dictionary of metrics.
    """

    load_files_output = load_files(directory)
    filenames = load_files_output["filenames"]
    all_phases = load_files_output["all_phases"]
    all_long_animation_frames = load_files_output["all_long_animation_frames"]
    all_metrics = load_files_output["all_metrics"]

    results_per_test: ProcessTestDirectoryOutput = {}

    # Step 1: Iterate over each test file
    for index, filename in enumerate(filenames):
        stable_test_name = get_stable_test_name(filename)

        if stable_test_name not in results_per_test:
            results_per_test[stable_test_name] = {}

        # Step 2: Add metrics from the Chrome DevTools Protocol data
        if (
            "long_animation_frames_duration_ms"
            not in results_per_test[stable_test_name]
        ):
            results_per_test[stable_test_name]["long_animation_frames_duration_ms"] = []

        results_per_test[stable_test_name]["long_animation_frames_duration_ms"].append(
            all_long_animation_frames[index]
        )

        # Step 3: Add metrics from the React Profiler data
        react_profiles_keys = all_phases[index].keys()
        phases = ["mount", "nested-update", "update"]

        for react_profile_key in react_profiles_keys:
            for phase in phases:
                if phase in all_phases[index][react_profile_key]:
                    _extract_react_profile_metrics(
                        all_phases,
                        index,
                        react_profile_key,
                        phase,
                        results_per_test,
                        stable_test_name,
                    )

        if load_all_metrics:
            # Step 4: Add metrics from the tracked metrics data
            for metric in all_metrics[index]:
                metric_name = metric["name"]
                if metric_name not in results_per_test[stable_test_name]:
                    results_per_test[stable_test_name][metric_name] = []

                results_per_test[stable_test_name][metric_name].append(metric["value"])

    return results_per_test


def find_outlier_indices(data: List[float]) -> List[int]:
    """
    Finds the indices of the outliers in the data.

    Args:
        data (List[float]): The data.

    Returns:
        List[int]: The indices of the outliers.
    """
    with warnings.catch_warnings():
        # Suppress warnings from the zscore function since there are some
        # expected cases where every piece of data is the same
        warnings.simplefilter("ignore")
        z_scores = stats.zscore(data)

    return [index for index, z_score in enumerate(z_scores) if abs(z_score) > 3]


def find_and_remove_outliers(
    results_per_test: ProcessTestDirectoryOutput,
) -> ProcessTestDirectoryOutput:
    """
    Finds and removes outliers from the test results.

    Args:
        results_per_test (ProcessTestDirectoryOutput): The test results.

    Returns:
        ProcessTestDirectoryOutput: The test results with outliers removed.
    """
    for test_name in results_per_test.keys():
        test_outliers = set()
        for metric_name, metric_data in results_per_test[test_name].items():
            outliers = find_outlier_indices(metric_data)
            test_outliers.update(outliers)

        if test_outliers:
            for metric_name, metric_data in results_per_test[test_name].items():
                results_per_test[test_name][metric_name] = [
                    metric_data[index]
                    for index in range(len(metric_data))
                    if index not in test_outliers
                ]

    return results_per_test


def calculate_statistical_diff(
    baseline_results: ProcessTestDirectoryOutput,
    treatment_results: ProcessTestDirectoryOutput,
) -> StatisticalDiff:
    """
    Determines the differences between baseline and treatment test results.

    Args:
        baseline_results (ProcessTestDirectoryOutput): Baseline test results.
        treatment_results (ProcessTestDirectoryOutput): Treatment test results.

    Returns:
        StatisticalDiff: A dictionary containing the test differences.
    """
    all_keys = set(baseline_results.keys()).union(treatment_results.keys())

    results: StatisticalDiff = {}

    for test_name in all_keys:
        if test_name not in treatment_results:
            print(
                f"Test: `{test_name}` not found in treatment results. Assuming this test has been deleted in the new change set."
            )
            continue

        if test_name not in baseline_results:
            print(
                f"Test: `{test_name}` not found in baseline results. Assuming this is a new test."
            )
            continue

        # It is possible for there to be different keys in the baseline vs
        # treatment results due to legitimate changes in the test or source. We
        # only want to compare the keys that are common between both.
        keys_intersection = set(baseline_results[test_name].keys()).intersection(
            treatment_results[test_name].keys()
        )

        for metric_name in keys_intersection:
            baseline_metrics = baseline_results[test_name][metric_name]
            treatment_metrics = treatment_results[test_name][metric_name]

            t_stat, p_value = stats.ttest_ind(
                baseline_metrics, treatment_metrics, nan_policy="raise"
            )

            if test_name not in results:
                results[test_name] = {}

            results[test_name][metric_name] = {
                "t_stat": t_stat,
                "p_value": p_value,
                "baseline_metrics": baseline_metrics,
                "treatment_metrics": treatment_metrics,
            }

    return results


def get_analyzed_test_diff_results(
    statistical_diff: StatisticalDiff, alpha: float = 0.05
) -> AnalyzedTestDiffResults:
    """
    Analyzes the test difference results to count regressions, improvements, and no changes.

    Args:
        statistical_diff (StatisticalDiff): Test difference results.
        alpha (float): Significance level for statistical tests.

    Returns:
        AnalyzedTestDiffResults: Counts of regressions, improvements, and no changes.
    """
    regression_count = 0
    improvement_count = 0
    no_change_count = 0

    for test_file, test_results in statistical_diff.items():
        for metric_name, metric_results in test_results.items():
            t_stat = metric_results["t_stat"]
            p_value = metric_results["p_value"]

            if p_value < alpha:
                if t_stat < 0:
                    regression_count += 1
                    print(
                        f"❌ Test: `{test_file}` Metric: {metric_name} has statistically significant regression."
                    )
                else:
                    improvement_count += 1
                    print(
                        f"✅ Test: `{test_file}` Metric: {metric_name} has statistically significant improvement."
                    )
                print("Baseline Metrics:", metric_results["baseline_metrics"])
                print("Treatment Metrics:", metric_results["treatment_metrics"])
            else:
                no_change_count += 1
                print(
                    f"🟰 Test: `{test_file}` Metric: {metric_name} has no statistically significant change."
                )

    return {
        "regression_count": regression_count,
        "improvement_count": improvement_count,
        "no_change_count": no_change_count,
    }


def main(baseline_dir: str, treatment_dir: str) -> AnalyzedTestDiffResults:
    """
    Main function to process test results and analyze differences.

    Args:
        baseline_dir (str): Directory containing baseline test results.
        treatment_dir (str): Directory containing treatment test results.

    Returns:
        AnalyzedTestDiffResults: Analyzed test difference results.
    """
    baseline_processed = process_test_results_directory(baseline_dir)
    treatment_processed = process_test_results_directory(treatment_dir)

    statistical_diff = calculate_statistical_diff(
        baseline_processed, treatment_processed
    )

    return get_analyzed_test_diff_results(statistical_diff)


if __name__ == "__main__":
    baseline_dir = sys.argv[1]
    treatment_dir = sys.argv[2]

    analyzed_test_diff_results = main(baseline_dir, treatment_dir)

    if analyzed_test_diff_results["regression_count"] > 0:
        print(
            "There are performance regressions. Please view output above for details."
        )
        sys.exit(1)
