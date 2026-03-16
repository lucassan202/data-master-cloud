# Makefile

PYTHON_VERSION := python3.11

# --- csv build ---
CSV_VENV     := .lambda_venv_csv
CSV_PACKAGE  := lambda_function.zip
CSV_REQS     := requirements-lambda.txt
CSV_FUNCTION := lambda_download_csv.py

# --- screp build ---
SCREP_VENV     := .lambda_venv_screp
SCREP_PACKAGE  := selenium_layer.zip
SCREP_REQS     := requirements-lambda-screp.txt
SCREP_FUNCTION := screp_reclamacoes.py

# Internal variables (set via recursive make)
LAMBDA_VENV     ?= .lambda_venv
PACKAGE_NAME    ?= lambda_function.zip
REQUIREMENTS    ?= requirements-lambda.txt
LAMBDA_FUNCTION ?= lambda_download_csv.py

default: build-csv

build-csv:
	$(MAKE) _package \
		LAMBDA_VENV=$(CSV_VENV) \
		PACKAGE_NAME=$(CSV_PACKAGE) \
		REQUIREMENTS=$(CSV_REQS) \
		LAMBDA_FUNCTION=$(CSV_FUNCTION)

build-screp:
	$(MAKE) _package \
		LAMBDA_VENV=$(SCREP_VENV) \
		PACKAGE_NAME=$(SCREP_PACKAGE) \
		REQUIREMENTS=$(SCREP_REQS) \
		LAMBDA_FUNCTION=$(SCREP_FUNCTION)

_venv:
	$(PYTHON_VERSION) -m venv $(LAMBDA_VENV) --without-pip
	curl -sS https://bootstrap.pypa.io/get-pip.py | $(LAMBDA_VENV)/bin/python3
	$(LAMBDA_VENV)/bin/pip install -U pip

_dependencies: _venv
	$(LAMBDA_VENV)/bin/pip install -r $(REQUIREMENTS)

_package: _dependencies
	@PYTHON_DIR=$$(ls $(LAMBDA_VENV)/lib/ | head -n 1); \
	cd $(LAMBDA_VENV)/lib/$$PYTHON_DIR/site-packages; zip -r9 $(CURDIR)/$(PACKAGE_NAME) .
	zip -gj $(PACKAGE_NAME) ./app/src/lambda/$(LAMBDA_FUNCTION)

clean-csv:
	rm -rf $(CSV_VENV)
	rm -f $(CSV_PACKAGE)

clean-screp:
	rm -rf $(SCREP_VENV)
	rm -f $(SCREP_PACKAGE)

clean: clean-csv clean-screp

.PHONY: default build-csv build-screp _venv _dependencies _package clean clean-csv clean-screp
