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


def get_stable_test_name(filename: str) -> str:
    """
    Extracts a stable test name from a given test run filename.

    Args:
        filename (str): The filename to process.

    Returns:
        str: The stable test name extracted from the filename.

    Raises:
        ValueError: If the filename does not end with '.json' or if the filename
        format is invalid.
    """
    if not filename.endswith(".json"):
        raise ValueError("Filename must end with '.json'")

    try:
        # Remove the timestamp and the underscore
        base_filename = filename.split("_", 1)[1]
        # Remove anything in brackets []
        base_filename = base_filename.split("[", 1)[0]
        # Remove the `.json` extension
        base_filename = base_filename.replace(".json", "")

        return base_filename
    except IndexError:
        raise ValueError("Invalid filename format")
