.PHONY: install app lint lint-fix format typecheck clean pre-commit pre-commit-install help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make app               - Run the Streamlit issue explorer"
	@echo "  make lint              - Check code with ruff"
	@echo "  make lint-fix          - Auto-fix linting issues"
	@echo "  make format            - Format code with ruff"
	@echo "  make typecheck         - Run mypy and ty type checking"
	@echo "  make pre-commit        - Run all pre-commit hooks"
	@echo "  make pre-commit-install - Install pre-commit git hooks"
	@echo "  make clean             - Remove cache and build artifacts"

install:
	uv sync
	uv run pre-commit install

pre-commit:
	uv run pre-commit run --all-files

app:
	uv run streamlit run 🚧_Streamlit_Issue_Explorer.py

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

typecheck:
	uv run ty check
	uv run mypy

clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
