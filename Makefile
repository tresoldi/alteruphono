# AlteruPhono Makefile
# Development and maintenance tasks for the AlteruPhono project

.PHONY: help clean install install-dev test lint format notebooks notebooks-clean check-notebooks docs all

# Default target
help:
	@echo "AlteruPhono Development Tasks"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install package in development mode"
	@echo "  install-dev   Install package with development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  test          Run the test suite"
	@echo "  lint          Run linting (ruff, mypy)"
	@echo "  format        Format code with ruff"
	@echo ""
	@echo "Notebooks:"
	@echo "  notebooks     Execute all notebooks in examples/ (populates output cells)"
	@echo "  notebooks-clean  Clear all notebook outputs"
	@echo "  check-notebooks  Check if notebooks have been executed"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          Build documentation (if available)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         Clean up build artifacts and cache files"
	@echo "  all           Run format, lint, and tests"

# Installation targets
install:
	@echo "Installing AlteruPhono in development mode..."
	pip install -e .

install-dev: install
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"

# Code quality targets
test:
	@echo "Running test suite..."
	python -m pytest tests/ -v

lint:
	@echo "Running linting checks..."
	@echo "- ruff..."
	python -m ruff check .
	@echo "- mypy..."
	python -m mypy alteruphono

format:
	@echo "Formatting code..."
	python -m ruff format .
	python -m ruff check . --fix

# Notebook targets
notebooks:
	@echo "Executing all notebooks in examples/ directory..."
	@echo "This will populate output cells for GitHub display."
	@if [ ! -d "examples" ]; then \
		echo "No examples/ directory found."; \
		exit 1; \
	fi
	@notebook_count=$$(find examples/ -name "*.ipynb" | wc -l); \
	if [ $$notebook_count -eq 0 ]; then \
		echo "No Jupyter notebooks found in examples/"; \
		exit 0; \
	fi; \
	echo "Found $$notebook_count notebook(s) to execute..."
	@failed_notebooks=""; \
	for notebook in $$(find examples/ -name "*.ipynb"); do \
		echo "Executing $$notebook..."; \
		if python -m jupyter nbconvert --to notebook --execute --inplace "$$notebook" \
			--ExecutePreprocessor.timeout=300 \
			--ExecutePreprocessor.kernel_name=python3; then \
			echo "$$notebook executed successfully"; \
		else \
			echo "Failed to execute $$notebook"; \
			failed_notebooks="$$failed_notebooks $$notebook"; \
		fi; \
	done; \
	if [ -n "$$failed_notebooks" ]; then \
		echo ""; \
		echo "Some notebooks failed to execute:$$failed_notebooks"; \
		echo "Successfully executed notebooks will still have populated outputs."; \
		echo "Check the failed notebooks for missing dependencies or errors."; \
	else \
		echo "All notebooks executed successfully!"; \
	fi; \
	echo "Output cells are now populated and will be visible on GitHub."

notebooks-clean:
	@echo "Clearing all notebook outputs..."
	@if [ ! -d "examples" ]; then \
		echo "No examples/ directory found."; \
		exit 1; \
	fi
	@notebook_count=$$(find examples/ -name "*.ipynb" | wc -l); \
	if [ $$notebook_count -eq 0 ]; then \
		echo "No Jupyter notebooks found in examples/"; \
		exit 0; \
	fi
	@for notebook in $$(find examples/ -name "*.ipynb"); do \
		echo "Clearing outputs from $$notebook..."; \
		python -m jupyter nbconvert --to notebook --clear-output --inplace "$$notebook"; \
		echo "$$notebook outputs cleared"; \
	done
	@echo "All notebook outputs cleared."

check-notebooks:
	@echo "Checking if notebooks have been executed..."
	@if [ ! -d "examples" ]; then \
		echo "No examples/ directory found."; \
		exit 1; \
	fi
	@notebook_count=$$(find examples/ -name "*.ipynb" | wc -l); \
	if [ $$notebook_count -eq 0 ]; then \
		echo "No Jupyter notebooks found in examples/"; \
		exit 0; \
	fi
	@has_outputs=true; \
	for notebook in $$(find examples/ -name "*.ipynb"); do \
		if ! python -c "import json; nb=json.load(open('$$notebook')); cells=[c for c in nb['cells'] if c['cell_type']=='code']; outputs=[c for c in cells if c.get('outputs')]; exit(0 if outputs else 1)" 2>/dev/null; then \
			echo "$$notebook has no output cells (not executed)"; \
			has_outputs=false; \
		else \
			echo "$$notebook has output cells"; \
		fi; \
	done; \
	if [ "$$has_outputs" = "false" ]; then \
		echo ""; \
		echo "Some notebooks are missing outputs. Run 'make notebooks' to execute them."; \
		exit 1; \
	else \
		echo "All notebooks have been executed and have output cells."; \
	fi

# Documentation target (placeholder)
docs:
	@echo "Building documentation..."
	@if [ -f "docs/Makefile" ]; then \
		cd docs && make html; \
	else \
		echo "No documentation build system found."; \
		echo "Documentation files are available in docs/ directory."; \
	fi

# Cleanup target
clean:
	@echo "Cleaning up build artifacts and cache files..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find . -type f -name ".coverage" -delete
	@echo "Cleanup complete."

# Comprehensive check
all: format lint test
	@echo ""
	@echo "All checks passed! The project is ready."
