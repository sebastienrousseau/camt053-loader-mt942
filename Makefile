# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Developer tasks. `make check` runs every gate CI runs, in the same order;
# run it inside a virtualenv after `make dev`.

.PHONY: help dev test lint format type-check complexity reuse versions audit bench examples build demo check clean

PYTHON ?= python3
SRC := camt053_loader_mt942/ tests/ examples/ benches/ scripts/ fuzz/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

dev: ## Install the hash-pinned CI toolchain and this package (editable)
	$(PYTHON) -m pip install --require-hashes -r requirements/ci.txt
	$(PYTHON) -m pip install --no-deps -e .

test: ## Tests with the 100% line + branch coverage gate, docstring gate
	$(PYTHON) -m pytest tests/
	$(PYTHON) -m interrogate -c pyproject.toml camt053_loader_mt942

lint: ## Ruff lint and format check
	$(PYTHON) -m ruff check $(SRC)
	$(PYTHON) -m ruff format --check $(SRC)

format: ## Apply ruff formatting
	$(PYTHON) -m ruff format $(SRC)

type-check: ## mypy --strict on the package and the stdlib-only scripts
	$(PYTHON) -m mypy camt053_loader_mt942/ scripts/check_suite_consistency.py scripts/verify_versions.py

complexity: ## Complexity ceilings against complexity-baseline.json
	$(PYTHON) scripts/check_complexity.py
	complexipy camt053_loader_mt942 scripts benches examples fuzz --max-complexity-allowed 15 --quiet

reuse: ## REUSE 3.3 licensing check
	reuse lint

versions: ## Every version source agrees with pyproject.toml
	$(PYTHON) scripts/verify_versions.py

audit: ## pip-audit over the pinned requirements (needs requirements/audit.txt)
	pip-audit -r requirements/ci.txt --require-hashes --disable-pip --progress-spinner off
	pip-audit -r requirements/build.txt --require-hashes --disable-pip --progress-spinner off
	pip-audit -r requirements/fuzz.txt --require-hashes --disable-pip --progress-spinner off

bench: ## Run the benchmark (quick mode, as CI does)
	$(PYTHON) benches/bench_parse_mt942.py --quick

examples: ## Run every example end to end
	@for example in examples/*.py; do echo "--- $$example ---"; $(PYTHON) "$$example" || exit 1; done

build: ## Build sdist + wheel and run twine check
	rm -rf dist/
	$(PYTHON) -m build
	$(PYTHON) -m twine check --strict dist/*

demo: ## Render .github/demo.gif from .github/demo.tape (needs vhs)
	vhs .github/demo.tape

check: lint type-check test complexity reuse versions bench examples ## Every CI gate

clean: ## Remove build and test artefacts
	rm -rf dist/ build/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/ coverage.xml .coverage
