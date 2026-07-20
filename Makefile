
MAIN = main.py
MAP  = maps/easy/02_simple_fork.txt
 
 
run:
	uv run python $(MAIN) $(MAP)
 
install:
	uv add arcade
	uv add flake8
	uv add mypy

	uv sync
 
debug:
	uv run python -m pdb $(MAIN) $(MAP)
 
clean:
	find src/ -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
 
lint:
	uv run flake8 main.py src/
	uv run mypy main.py src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
 
lint-strict:
	uv run flake8 main.py src/
	uv run mypy main.py src --strict

.PHONY: install run debug clean lint lint-strict