# 🚧 Streamlit Issues

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://issues.streamlitapp.com)

A collection of Streamlit apps to explore potential features and replicate issues. This repo is owned by the open-source team.

## How to add a new issue

1. Create a new folder in [`issues`](./issues) with this naming pattern: `gh-<ISSUE_ID>`.
2. Create an `app.py` file in the created issue folder and use it to reproduce the issue.
3. Once the issue is added, it should be automatically accessible from the [deployed issue explorer](https://issues.streamlitapp.com) after a page refresh.
4. Make sure to link the issue app in the respective issue on Github. Tip:  Inside the `Issue Description` expander, you can find a markdown snippet that allows you to easily add a badge to the GitHub issue. Add this to the issue body in the `Steps to reproduce` section. 

_The app might require a dedicated environment in some situations, e.g. requires specific dependencies, a different python version, or multipaging. In this case, just add a `requirements.txt` or `Pipfile` to the issue folder. This will require the app to run separately._

## Run locally

To run the issue explorer locally, execute in the repo root folder:

```bash
pipenv install --dev && pipenv run app
```

Some apps require a dedicated environment and need to be run separately.