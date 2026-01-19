.PHONY: install app check fix clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies and pre-commit hooks"
	@echo "  make app        - Run the Streamlit app"
	@echo "  make check      - Run linting, pre-commit, and type checking"
	@echo "  make fix        - Auto-fix lint issues and format code"
	@echo "  make clean      - Remove cache and build artifacts"

install:
	uv sync
	uv run pre-commit install

app:
	uv run streamlit run 🚧_Streamlit_Issue_Explorer.py

check:
	# Lint with ruff:
	uv run ruff check
	# Check formatting (run `make fix` if this fails):
	uv run ruff format --check
	# Type check with ty:
	uv run ty check
	# Type check with mypy:
	uv run mypy

fix:
	# Apply lint fixes with ruff but dont fail:
	uv run ruff check --fix || true
	# Format code with ruff:
	uv run ruff format || true
	# Run pre-commit hooks to apply fixes (ignore exit code):
	uv run pre-commit run || true

clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
