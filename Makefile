
MAIN := main.py
MAP  ?= maps/easy/02_simple_fork.txt
 
.PHONY: install run debug clean lint lint-strict
 
run:
	uv run python $(MAIN) $(MAP)
 
install:
	uv add arcade
	uv sync
 
debug:
	uv run python -m pdb $(MAIN) $(MAP)
 
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
 
lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
 
lint-strict:
	uv run flake8 .
	uv run mypy . --strict