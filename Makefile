# Makefile

PYTHON_VERSION := python3.11

# --- local bootstrap ---
ENVIRONMENT          ?= dev
AWS_REGION           ?= us-east-2
S3_BUCKET            ?= $(ENVIRONMENT)-us-east-2-data-master
TF_STATE_BUCKET      ?= data-master-us-east-2-terraform-statefile
TF_LOCK_TABLE        ?= data-master-us-east-2-terraform-lock
TF_BUCKETS_KEY       ?= data-master-cloud-buckets
TF_APP_KEY           ?= data-master-cloud

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

build-all:
	@command -v aws >/dev/null 2>&1 || { echo "Erro: aws não encontrado no PATH."; exit 1; }
	@command -v terraform >/dev/null 2>&1 || { echo "Erro: terraform não encontrado no PATH."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Erro: docker não encontrado no PATH."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "Erro: Docker Compose não está disponível."; exit 1; }
	terraform -chdir=IaC/buckets init -reconfigure \
		-backend-config="bucket=$(TF_STATE_BUCKET)" \
		-backend-config="key=$(TF_BUCKETS_KEY)" \
		-backend-config="region=$(AWS_REGION)" \
		-backend-config="dynamodb_table=$(TF_LOCK_TABLE)"
	terraform -chdir=IaC/buckets workspace select $(ENVIRONMENT) || terraform -chdir=IaC/buckets workspace new $(ENVIRONMENT)
	terraform -chdir=IaC/buckets apply -auto-approve \
		-var="env=$(ENVIRONMENT)" \
		-var="aws_region=$(AWS_REGION)"
	$(MAKE) build-csv
	$(MAKE) build-screp
	aws s3 cp $(CSV_PACKAGE) s3://$(S3_BUCKET)/tmp/$(CSV_PACKAGE) --region $(AWS_REGION)
	aws s3 cp $(SCREP_PACKAGE) s3://$(S3_BUCKET)/tmp/$(SCREP_PACKAGE) --region $(AWS_REGION)
	terraform -chdir=IaC init -reconfigure \
		-backend-config="bucket=$(TF_STATE_BUCKET)" \
		-backend-config="key=$(TF_APP_KEY)" \
		-backend-config="region=$(AWS_REGION)" \
		-backend-config="dynamodb_table=$(TF_LOCK_TABLE)"
	terraform -chdir=IaC workspace select $(ENVIRONMENT) || terraform -chdir=IaC workspace new $(ENVIRONMENT)
	terraform -chdir=IaC apply -auto-approve \
		-var="env=$(ENVIRONMENT)" \
		-var="environment=$(ENVIRONMENT)"
	docker compose up -d

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

.PHONY: default build-all build-csv build-screp _venv _dependencies _package clean clean-csv clean-screp
