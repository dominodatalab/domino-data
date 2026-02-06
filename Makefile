#* Variables
SHELL := /usr/bin/env bash
PYTHON := python3

#* OpenAPI variables
TRAININGSET_YAML := openapi/trainingset.yaml
DATASOURCE_YAML := openapi/datasource.yaml
REMOTEFS_YAML := remotefs/api/swagger.json

#* Poetry
.PHONY: poetry-download
poetry-download:
	curl -sSL https://install.python-poetry.org | $(PYTHON) - || (cat /home/runner/work/domino-data/domino-data/poetry-installer-error-*.log && exit 1)

.PHONY: poetry-remove
poetry-remove:
	curl -sSL https://install.python-poetry.org | $(PYTHON) - --uninstall

#* Installation
.PHONY: install
install:
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n
	-poetry run mypy --install-types --non-interactive ./

.PHONY: pre-commit-install
pre-commit-install:
	poetry run pre-commit install

#* OpenAPI clients
.PHONY: install-trainingset
install-trainingset:
	poetry run openapi-python-client generate --meta none --path $(TRAININGSET_YAML)

.PHONY: update-trainingset
update-trainingset:
	poetry run openapi-python-client update --meta none --path $(TRAININGSET_YAML)

.PHONY: install-datasource
install-datasource:
	poetry run openapi-python-client generate --meta none --path $(DATASOURCE_YAML)

.PHONY: update-datasource
update-datasource:
	poetry run openapi-python-client update --meta none --path $(DATASOURCE_YAML)

.PHONY: install-remotefs
install-remotefs:
	swagger-codegen generate -i $(REMOTEFS_YAML) -l python -o . --additional-properties=packageName=remotefs_api_client

#* Formatters
.PHONY: codestyle
codestyle:
	poetry run pyupgrade --exit-zero-even-if-changed --py38-plus **/*.py
	poetry run isort --settings-path pyproject.toml ./
	poetry run black --config pyproject.toml ./
	poetry run flake8 --config setup.cfg domino_data/

.PHONY: formatting
formatting: codestyle

#* Linting
.PHONY: test
test:
	poetry run pytest --cov=domino_data tests/

.PHONY: check-codestyle
check-codestyle:
	poetry run isort --diff --check-only --settings-path pyproject.toml ./
	poetry run black --diff --check --config pyproject.toml ./
	poetry run flake8 --config setup.cfg domino_data/
	poetry run darglint --verbosity 2 domino_data tests

.PHONY: mypy
mypy:
	poetry run mypy --config-file pyproject.toml ./

.PHONY: check-safety
check-safety:
	poetry check
	# TODO remove pip ignore flag when fixed
	poetry run safety check --full-report -i 62044 -i 70612 -i 73884 -i 76170 -i 75976 -i 77744 -i 77745 -i 83159 -i 82754
	poetry run bandit -ll --recursive domino_data tests

.PHONY: lint
lint: test check-codestyle mypy check-safety

#* Cleaning
.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: clean
clean: pycache-remove build-remove docs-remove

#* Docs
.PHONY: docs
docs:
	cd docs; poetry run make html

.PHONY: open-docs
open-docs:
	open docs/build/html/index.html

.PHONY: docs-remove
docs-remove:
	cd docs; poetry run make clean

#* Submodules
update-submodules:
	git submodule update --recursive --remote

gen-services:
	poetry run python scripts/gen.py
