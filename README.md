# data-master-cloud

Pipeline de dados em nuvem para análise de reclamações de consumidores do [consumidor.gov.br](https://www.consumidor.gov.br). Migração cloud-native da solução on-premise [data-master](https://github.com/lucassan202/data-master), substituindo o cluster Hadoop/Spark por AWS Lambda, ECS Fargate e Databricks, com infraestrutura gerenciada por Terraform e CI/CD via GitHub Actions.

O projeto opera dois pipelines de ingestão: um **mensal** (download de CSV consolidado via Lambda) e um **diário** (web scraping incremental via Selenium + Lambda). Os dados são processados em camadas Medallion (Bronze → Silver → Gold) e visualizados em um **Dashboard Lakeview** nativo do Databricks.

Para documentação completa do projeto, arquitetura técnica e detalhamento das camadas de dados, consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Quick Start

### Pré-requisitos

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configurado com credenciais válidas
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.3
- [Python](https://www.python.org/downloads/) >= 3.10
- `make` disponível no terminal
- Acesso ao workspace do Databricks

---

### 1. Clone o repositório

```bash
git clone https://github.com/lucassan202/data-master-cloud
cd data-master-cloud
```

---

### 2. Configure as variáveis de infraestrutura

Edite o arquivo `IaC/terraform.tfvars` com os valores do seu ambiente:

```hcl
project     = "data-master"
environment = "dev"
aws_region  = "us-east-2"
```

Variáveis sensíveis (Databricks) devem ser configuradas como **secrets no GitHub Actions** ou exportadas como variáveis de ambiente locais:

```bash
export TF_VAR_databricks_host="https://<workspace>.azuredatabricks.net"
export TF_VAR_databricks_client_id="<client-id>"
export TF_VAR_databricks_client_secret="<client-secret>"
```

Para executar o Airflow localmente, copie o arquivo de exemplo e preencha as
configurações SMTP no arquivo local:

```bash
cp .env.example .env
```

Configure no `.env` as variáveis `AIRFLOW__SMTP__SMTP_HOST`,
`AIRFLOW__SMTP__SMTP_PORT`, `AIRFLOW__SMTP__SMTP_USER`,
`AIRFLOW__SMTP__SMTP_PASSWORD`, `AIRFLOW__SMTP__SMTP_MAIL_FROM` e as opções
`AIRFLOW__SMTP__SMTP_STARTTLS`/`AIRFLOW__SMTP__SMTP_SSL`. Os destinatários das
DAGs podem ser definidos em `AIRFLOW_NOTIFICATION_EMAILS`, separados por
vírgulas. O arquivo `.env` pode conter credenciais e não deve ser versionado;
use apenas placeholders no `.env.example`.

No Airflow provisionado pela EC2, as mesmas variáveis devem ser fornecidas pelo
secret manager no arquivo `/etc/airflow/airflow.env`. O `.env` local é usado
somente pelo Docker Compose.

Os destinatários de alertas e o principal dos GRANTs são configuráveis no
`IaC/jobs.auto.tfvars` pelas variáveis `notification_emails` e
`databricks_grant_principal`. Na ausência de configuração, ambas usam
`lucas_san20@hotmail.com`.

O Airflow envia alertas de falha das DAGs via SMTP. Antes de iniciar os
serviços, o arquivo `/etc/airflow/airflow.env` deve ser preenchido pelo
mecanismo de secrets do ambiente com as variáveis `AIRFLOW__SMTP__SMTP_HOST`,
`AIRFLOW__SMTP__SMTP_PORT`, `AIRFLOW__SMTP__SMTP_USER`,
`AIRFLOW__SMTP__SMTP_PASSWORD`, `AIRFLOW__SMTP__SMTP_MAIL_FROM` e,
quando aplicável, `AIRFLOW__SMTP__SMTP_STARTTLS`/`AIRFLOW__SMTP__SMTP_SSL`.

---

### 3. Inicialize o Terraform

O state dos buckets S3 é separado do state da aplicação. O `make build-all` inicializa e aplica os dois states automaticamente.

Para inicialização manual dos buckets:

```bash
terraform -chdir=IaC/buckets init \
  -backend-config="bucket=<bucket-do-estado>" \
  -backend-config="key=data-master-cloud-buckets" \
  -backend-config="region=us-east-2" \
  -backend-config="dynamodb_table=<tabela-de-lock>"
terraform -chdir=IaC/buckets workspace select dev
terraform -chdir=IaC/buckets plan \
  -var="env=dev" \
  -var="aws_region=us-east-2"
```

Para a infraestrutura da aplicação:

```bash
terraform -chdir=IaC init \
  -backend-config="bucket=<bucket-do-estado>" \
  -backend-config="key=data-master-cloud" \
  -backend-config="region=us-east-2" \
  -backend-config="dynamodb_table=<tabela-de-lock>"
```

Para ambientes distintos, use workspaces:

```bash
terraform -chdir=IaC workspace new dev
terraform -chdir=IaC workspace select dev
```

### 4. Configure o Airflow local

Para subir o Airflow localmente, copie o arquivo de exemplo e preencha as credenciais:

```bash
cp .env.example .env
```

### 5. Prepare e suba o ambiente

O comando abaixo empacota as Lambdas, publica os pacotes no S3, aplica a infraestrutura Terraform e sobe o Airflow via Docker Compose:

Opcionalmente, visualize antes as mudanças que serão aplicadas:

```bash
terraform -chdir=IaC plan \
  -var="env=dev" \
  -var="environment=dev"
```

Para outro ambiente, substitua `dev` pelo valor desejado.

```bash
make build-all
```

O ambiente padrão é `dev`, a região padrão é `us-east-2` e o bucket dos pacotes é `dev-us-east-2-data-master`. Esses valores podem ser sobrescritos:

```bash
make build-all ENVIRONMENT=pro AWS_REGION=us-east-2 S3_BUCKET=pro-us-east-2-data-master ...
```

O comando cria `lambda_function.zip` (downloader CSV) e `selenium_layer.zip` (layer do Selenium), copiando-os para `s3://<bucket>/tmp/` antes do `terraform apply`.

> O `build-all` executa `terraform apply -auto-approve` e pode criar recursos e custos na AWS. Verifique as variáveis `TF_VAR_*` e as credenciais AWS antes de executá-lo.

O backend Terraform precisa estar inicializado previamente com `terraform init`, conforme o passo anterior.

Comandos úteis do Airflow:

O serviço `airflow-init` inicializa o banco, cria o usuário administrador, as conexões `aws_default` e `databricks_default` e as variáveis das DAGs. Acesse http://localhost:8080 usando as credenciais definidas em `.env`.

Comandos úteis:

```bash
docker compose logs -f airflow-init
docker compose logs -f airflow-scheduler
docker compose restart
docker compose down
```

Este Compose é destinado ao desenvolvimento (`dev`). Em produção, o Airflow continua sendo provisionado pela infraestrutura Terraform em EC2, com PostgreSQL em RDS.

---

### 6. Terraform manual

```bash
# Aplique
terraform -chdir=IaC apply
```

---

### 7. CI/CD via GitHub Actions

O deploy automatizado é ativado por push na branch:

| Branch    | Ambiente |
|-----------|----------|
| `develop` | `dev`    |
| `main`    | `pro`    |

O workflow reusável está em [.github/workflows/terraform.yml](.github/workflows/terraform.yml). Ele:
1. Empacota as funções Lambda
2. Faz upload dos pacotes para o S3
3. Executa `terraform init / plan / apply`

> Para destruir a infraestrutura, defina `"destroy": true` em `IaC/destroy_config.json` e abra um PR.

### Airflow

O ambiente `pro` provisiona o Airflow em uma EC2 AWS `t3.medium`, com PostgreSQL RDS privado, sincronização dos DAGs pelo bucket S3 e acesso inicial à UI na porta 8080.

---

## Estrutura do Projeto

```
data-master-cloud/
├── app/src/
│   ├── lambda/          # Funções Lambda (downloader CSV e scraper Selenium)
│   ├── airflow/dags/    # DAGs do Airflow (ETL mensal e scraper diário)
│   ├── bronze.py        # Notebook Databricks — camada Bronze
│   ├── silver.py        # Notebook Databricks — camada Silver
│   └── *_gold.py        # Notebooks Databricks — camada Gold
├── dash/                # Dashboard Databricks Lakeview (dash_consumidor.lvdash.json)
├── IaC/                 # Infraestrutura como Código (Terraform)
├── .github/workflows/   # Pipelines de CI/CD
├── Makefile             # Empacotamento das Lambdas
└── docs/
    └── ARCHITECTURE.md  # Documentação técnica detalhada
```

---

## Mais informações

Consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para:
- Contexto completo do projeto
- Diagrama de arquitetura
- Detalhamento das camadas Bronze, Silver e Gold
- Explicação dos componentes de infraestrutura
- Databricks Lakeview Dashboard (visualizações, datasets e filtros)
- Pipelines de ingestão (mensal e diário) e orquestração Airflow
- Pipeline de CI/CD
- Melhorias futuras planejadas
