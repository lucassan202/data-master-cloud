# Makefile

PYTHON_VERSION := python3.11

# --- local bootstrap ---
ENVIRONMENT          ?= dev
AWS_REGION           ?= us-east-2
S3_BUCKET            ?= $(ENVIRONMENT)-us-east-2-data-master
TF_STATE_BUCKET      ?=
TF_LOCK_TABLE        ?=
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

build-all: build-csv build-screp
	@command -v aws >/dev/null 2>&1 || { echo "Erro: aws não encontrado no PATH."; exit 1; }
	@command -v terraform >/dev/null 2>&1 || { echo "Erro: terraform não encontrado no PATH."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Erro: docker não encontrado no PATH."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "Erro: Docker Compose não está disponível."; exit 1; }
	@set -eu; \
	if [ -f .env ]; then set -a; . ./.env; set +a; fi; \
	if [ -z "$${AWS_ACCESS_KEY_ID:-}" ]; then unset AWS_ACCESS_KEY_ID; fi; \
	if [ -z "$${AWS_SECRET_ACCESS_KEY:-}" ]; then unset AWS_SECRET_ACCESS_KEY; fi; \
	if [ -z "$${AWS_SESSION_TOKEN:-}" ]; then unset AWS_SESSION_TOKEN; fi; \
	TF_STATE_BUCKET="$${TF_STATE_BUCKET:-$(TF_STATE_BUCKET)}"; \
	TF_LOCK_TABLE="$${TF_LOCK_TABLE:-$(TF_LOCK_TABLE)}"; \
	AWS_REGION="$${AWS_REGION:-$(AWS_REGION)}"; \
	ENVIRONMENT="$${ENVIRONMENT:-$(ENVIRONMENT)}"; \
	S3_BUCKET="$${S3_BUCKET:-$(S3_BUCKET)}"; \
	export TF_STATE_BUCKET TF_LOCK_TABLE AWS_REGION ENVIRONMENT S3_BUCKET; \
	if [ -n "$${TF_STATE_BUCKET}" ]; then \
		echo "Usando backend S3 remoto: $${TF_STATE_BUCKET}"; \
		terraform -chdir=IaC/buckets init -reconfigure \
			-backend-config="bucket=$${TF_STATE_BUCKET}" \
			-backend-config="key=$(TF_BUCKETS_KEY)" \
			-backend-config="region=$${AWS_REGION}" \
			$${TF_LOCK_TABLE:+-backend-config=dynamodb_table=$${TF_LOCK_TABLE}}; \
	else \
		echo "Usando state local do Terraform (TF_STATE_BUCKET não configurado)"; \
		terraform -chdir=IaC/buckets init -reconfigure -backend=false; \
	fi; \
	terraform -chdir=IaC/buckets workspace select "$${ENVIRONMENT}" || terraform -chdir=IaC/buckets workspace new "$${ENVIRONMENT}"; \
	terraform -chdir=IaC/buckets apply -auto-approve \
		-var="env=$${ENVIRONMENT}" \
		-var="aws_region=$${AWS_REGION}"; \
	aws s3 cp "$(CSV_PACKAGE)" "s3://$${S3_BUCKET}/tmp/$(CSV_PACKAGE)" --region "$${AWS_REGION}"; \
	aws s3 cp "$(SCREP_PACKAGE)" "s3://$${S3_BUCKET}/tmp/$(SCREP_PACKAGE)" --region "$${AWS_REGION}"; \
	if [ -n "$${TF_STATE_BUCKET}" ]; then \
		terraform -chdir=IaC init -reconfigure \
			-backend-config="bucket=$${TF_STATE_BUCKET}" \
			-backend-config="key=$(TF_APP_KEY)" \
			-backend-config="region=$${AWS_REGION}" \
			$${TF_LOCK_TABLE:+-backend-config=dynamodb_table=$${TF_LOCK_TABLE}}; \
	else \
		terraform -chdir=IaC init -reconfigure -backend=false; \
	fi; \
	terraform -chdir=IaC workspace select "$${ENVIRONMENT}" || terraform -chdir=IaC workspace new "$${ENVIRONMENT}"; \
	terraform -chdir=IaC apply -auto-approve \
		-var="env=$${ENVIRONMENT}" \
		-var="environment=$${ENVIRONMENT}"; \
	docker compose up -d

terraform-destroy:
	@command -v terraform >/dev/null 2>&1 || { echo "Erro: terraform não encontrado no PATH."; exit 1; }
	@set -eu; \
	if [ -f .env ]; then set -a; . ./.env; set +a; fi; \
	TF_STATE_BUCKET="$${TF_STATE_BUCKET:-$(TF_STATE_BUCKET)}"; \
	TF_LOCK_TABLE="$${TF_LOCK_TABLE:-$(TF_LOCK_TABLE)}"; \
	AWS_REGION="$${AWS_REGION:-$(AWS_REGION)}"; \
	ENVIRONMENT="$${ENVIRONMENT:-$(ENVIRONMENT)}"; \
	terraform -chdir=IaC workspace select "$${ENVIRONMENT}" || terraform -chdir=IaC workspace new "$${ENVIRONMENT}"; \
	terraform -chdir=IaC destroy -auto-approve \
		-var="env=$${ENVIRONMENT}" \
		-var="environment=$${ENVIRONMENT}"

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

.PHONY: default build-all terraform-destroy build-csv build-screp _venv _dependencies _package clean clean-csv clean-screp
