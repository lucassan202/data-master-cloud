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

### 2. Configure as variáveis e suba o ambiente

Copie o arquivo de exemplo, preencha as variáveis necessárias e mantenha o
arquivo `.env` apenas localmente, pois ele pode conter credenciais:

```bash
cp .env.example .env
```

Preencha as variáveis de acordo com o uso desejado:

| Grupo | Variáveis | Observação |
|---|---|---|
| Airflow | `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL` | Credenciais do usuário administrador local. |
| SMTP obrigatório | `AIRFLOW__SMTP__SMTP_HOST`, `AIRFLOW__SMTP__SMTP_PORT`, `AIRFLOW__SMTP__SMTP_MAIL_FROM` | Necessárias para inicializar o Airflow local. |
| SMTP opcional | `AIRFLOW__SMTP__SMTP_USER`, `AIRFLOW__SMTP__SMTP_PASSWORD`, `AIRFLOW__SMTP__SMTP_STARTTLS`, `AIRFLOW__SMTP__SMTP_SSL` | Preencha conforme o servidor SMTP. |
| Notificações | `AIRFLOW_NOTIFICATION_EMAILS` | E-mails separados por vírgula. |
| AWS | `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` | As credenciais podem ser omitidas quando a AWS CLI usa profile, role ou outro mecanismo padrão. |
| Databricks | `DATABRICKS_HOST`, `DATABRICKS_TOKEN` | Necessárias para a execução local das DAGs e jobs que acessam o Databricks. |
| Jobs | `AIRFLOW_ENV`, `DAT_REF_CARGA`, `DAT_REF_CARGA_M`, `PROJECT`, `ECS_CLUSTER`, `ECS_SERVICE`, `LAMBDA_SCREP`, `LAMBDA_DOWNLOAD` | Parâmetros dos jobs; os valores do arquivo de exemplo atendem ao ambiente local padrão. |
| Terraform remoto | `TF_STATE_BUCKET`, `TF_LOCK_TABLE` | Opcionais. Sem `TF_STATE_BUCKET`, o Terraform usa state local. `TF_LOCK_TABLE` só é usada quando o backend S3 está configurado. |

O state remoto S3 é recomendado para ambientes compartilhados. Para uso local,
deixe `TF_STATE_BUCKET` e `TF_LOCK_TABLE` vazias. Não alterne entre state local
e remoto sem migrar o state Terraform conscientemente.

```bash
make build-all
```

O comando prepara os pacotes das Lambdas, provisiona a infraestrutura,
configura o bucket e inicia os serviços locais. Por padrão, usa o ambiente
`dev` e a região `us-east-2`.

Para sobrescrever esses valores:

```bash
make build-all ENVIRONMENT=pro AWS_REGION=us-east-2
```

### CI/CD via GitHub Actions

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

### Destruir os recursos localmente

Para destruir automaticamente os recursos da aplicação gerenciados pelo Terraform:

```bash
make terraform-destroy
```

O comando não pede confirmação. Para destruir outro ambiente ou usar outra região:

```bash
make terraform-destroy ENVIRONMENT=pro AWS_REGION=us-east-2
```

Esse alvo destrói somente os recursos da aplicação em `IaC`. Os buckets de
bootstrap e de state gerenciados em `IaC/buckets` não são destruídos. Se estiver
usando state remoto, configure `TF_STATE_BUCKET` e `TF_LOCK_TABLE` no `.env` para
que o comando opere sobre o mesmo backend e workspace usados no deploy.

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
