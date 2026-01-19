.PHONY: install app check fix pre-commit clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies and pre-commit hooks"
	@echo "  make app        - Run the Streamlit app"
	@echo "  make check      - Run linting, pre-commit, and type checking"
	@echo "  make fix        - Auto-fix lint issues and format code"
	@echo "  make pre-commit - Run all pre-commit hooks on all files"
	@echo "  make clean      - Remove cache and build artifacts"

install:
	uv sync
	uv run pre-commit install

pre-commit:
	uv run pre-commit run --all-files

app:
	uv run streamlit run 🚧_Streamlit_Issue_Explorer.py

check:
	# Lint with ruff:
	uv run ruff check
	# Run pre-commit hooks on changed files:
	uv run pre-commit run
	# Type check with ty:
	uv run ty check
	# Type check with mypy:
	uv run mypy

fix:
	# Apply lint fixes with ruff but dont fail:
	uv run ruff check --fix
	# Format code with ruff:
	uv run ruff format

clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
