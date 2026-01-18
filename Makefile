.PHONY: install app lint lint-fix format typecheck test clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make app        - Run the Streamlit issue explorer"
	@echo "  make lint       - Check code with ruff"
	@echo "  make lint-fix   - Auto-fix linting issues"
	@echo "  make format     - Format code with ruff"
	@echo "  make typecheck  - Run mypy and ty type checking"
	@echo "  make test       - Run pytest"
	@echo "  make clean      - Remove cache and build artifacts"

install:
	uv sync

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
