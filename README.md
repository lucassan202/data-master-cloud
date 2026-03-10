# data-master-cloud

Pipeline de dados em nuvem para análise de reclamações de consumidores do [consumidor.gov.br](https://www.consumidor.gov.br). Migração cloud-native da solução on-premise [data-master](https://github.com/besgam/data-master), substituindo o cluster Hadoop/Spark por AWS Lambda, ECS Fargate e Databricks, com infraestrutura gerenciada por Terraform e CI/CD via GitHub Actions.

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
git clone https://github.com/besgam/data-master-cloud.git
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

---

### 3. Empacote as funções Lambda

```bash
make all
```

Isso cria os arquivos `lambda_function.zip` (downloader CSV) e `selenium_layer.zip` (layer do Selenium).

---

### 4. Inicialize o Terraform

```bash
terraform -chdir=IaC init
```

Para ambientes distintos, use workspaces:

```bash
terraform -chdir=IaC workspace new dev
terraform -chdir=IaC workspace select dev
```

---

### 5. Planeje e aplique a infraestrutura

```bash
# Visualize as mudanças
terraform -chdir=IaC plan

# Aplique
terraform -chdir=IaC apply
```

---

### 6. CI/CD via GitHub Actions

O deploy automatizado é ativado ao abrir um Pull Request:

| Branch    | Ambiente |
|-----------|----------|
| `develop` | `dev`    |
| `main`    | `pro`    |

O workflow reusável está em [.github/workflows/terraform.yml](.github/workflows/terraform.yml). Ele:
1. Empacota as funções Lambda
2. Faz upload dos pacotes para o S3
3. Executa `terraform init / plan / apply`

> Para destruir a infraestrutura, defina `"destroy": true` em `IaC/destroy_config.json` e abra um PR.

---

## Estrutura do Projeto

```
data-master-cloud/
├── app/src/
│   ├── lambda/          # Funções Lambda (downloader e scraper)
│   ├── airflow/dags/    # DAG do Airflow para orquestração
│   ├── bronze.py        # Notebook Databricks — camada Bronze
│   ├── silver.py        # Notebook Databricks — camada Silver
│   └── *_gold.py        # Notebooks Databricks — camada Gold
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
- Pipeline de CI/CD
- Melhorias futuras planejadas
