# 🚧 Streamlit Issues

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://issues.streamlitapp.com)

A collection of Streamlit apps to explore potential features and replicate issues. The goal is to make it very easy to create and share reproducible examples. This repo is owned by the open-source team.

## How to add a new issue

1. Create a new folder in [`issues`](./issues) with this naming pattern: `gh-<GITHUB_ISSUE_ID>`.
2. Create an `app.py` file in the created issue folder and use it to reproduce the issue.
3. Once the issue is added, it should be automatically accessible from the [deployed issue explorer](https://issues.streamlitapp.com) after a page refresh.
4. Make sure to link the issue app in the respective issue on Github. Tip:  Inside the `Issue Description` expander, you can find a markdown snippet that allows you to easily add a badge to the GitHub issue. Add this to the issue body in the `Steps to reproduce` section.

## Run locally

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. To run the issue explorer locally:

```bash
make install  # Install dependencies and pre-commit hooks
make app      # Run the Streamlit app
```

Other available commands:

```bash
make help       # Show all available commands
make check      # Run linting, pre-commit, and type checking
make fix        # Auto-fix lint issues and format code
make pre-commit # Run all pre-commit hooks on all files
make clean      # Remove cache and build artifacts
```
