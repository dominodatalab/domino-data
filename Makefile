#* Variables
SHELL := /usr/bin/env bash
PYTHON := python

#* OpenAPI variables
TRAININGSET_YAML := openapi/trainingset.yaml
DATASOURCE_YAML := openapi/datasource.yaml

#* Poetry
.PHONY: poetry-download
poetry-download:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) -

.PHONY: poetry-remove
poetry-remove:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) - --uninstall

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

#* Formatters
.PHONY: codestyle
codestyle:
	poetry run pyupgrade --exit-zero-even-if-changed --py38-plus **/*.py
	poetry run isort --settings-path pyproject.toml ./
	poetry run black --config pyproject.toml ./

.PHONY: formatting
formatting: codestyle

#* Linting
.PHONY: test
test:
	poetry run pytest --cov=domino_data_sdk tests/

.PHONY: check-codestyle
check-codestyle:
	poetry run isort --diff --check-only --settings-path pyproject.toml ./
	poetry run black --diff --check --config pyproject.toml ./
	poetry run darglint --verbosity 2 domino_data_sdk tests

.PHONY: mypy
mypy:
	poetry run mypy --config-file pyproject.toml ./

.PHONY: check-safety
check-safety:
	poetry check
	poetry run safety check --full-report
	poetry run bandit -ll --recursive domino_data_sdk tests

.PHONY: lint
lint: test check-codestyle mypy check-safety

#* Cleaning
.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: clean-all
clean-all: pycache-remove build-remove

#* Docs

.PHONY: docs
docs:
	cd docs; poetry run make html

.PHONY: open-docs
open-docs:
	open docs/build/html/index.html
