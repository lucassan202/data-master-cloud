# Arquitetura e Documentação Técnica — data-master-cloud

## Contexto do Projeto

O **data-master-cloud** é a evolução cloud-native do projeto [data-master](https://github.com/besgam/data-master), que analisava reclamações de consumidores publicadas no portal [consumidor.gov.br](https://www.consumidor.gov.br) utilizando um cluster Hadoop/Spark on-premise.

O objetivo da migração foi eliminar a necessidade de infraestrutura física gerenciada manualmente, substituindo-a por serviços gerenciados da AWS e Databricks. Com isso, o projeto ganhou:

- **Escalabilidade automática** — sem provisionamento manual de servidores
- **Infraestrutura como Código** — toda a nuvem definida em Terraform
- **CI/CD integrado** — deploy automatizado via GitHub Actions
- **Custo sob demanda** — recursos pagos apenas quando utilizados

O projeto opera dois pipelines complementares de ingestão: um **mensal**, que baixa o CSV consolidado de reclamações do portal `dados.mj.gov.br`, e um **diário**, que faz web scraping incremental das reclamações publicadas em `consumidor.gov.br`. Os dados são processados em camadas de qualidade progressiva (Medallion Architecture) e disponibilizados em um dashboard analítico Databricks Lakeview.

---

## Arquitetura de Alto Nível

```
                        ┌──────────────────────────────────────────────────┐
                        │                   AWS Cloud                      │
                         │                                                 │
  dados.mj.gov.br ──►   │  Lambda (CSV Downloader)        [mensal]         │
                        │        │                                        │
  consumidor.gov.br ──► │  ECS Fargate (Selenium) ──► Lambda (Scraper)    │
                        │        │                         │  [diário]    │
                        │        └──────────┬──────────────┘              │
                        │                   ▼                             │
                        │              S3 (Data Lake)                     │
                        │         ┌─────────────────┐                     │
                        │         │  Bronze / Raw   │                     │
                        │         └────────┬────────┘                     │
                        │                  ▼                              │
                        │         ┌─────────────────┐                     │
                        │         │ Silver / Filtered│                     │
                        │         └────────┬────────┘                     │
                        │                  ▼                              │
                        │         ┌─────────────────┐                     │
                        │         │  Gold / Agregado │                     │
                        │         └────────┬────────┘                     │
                        │                  │                              │
                        └──────────────────┼──────────────────────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │  Databricks  │  (processamento)
                                    │  Airflow DAGs│  (orquestração)
                                    └──────┬──────┘
                                           │
                                  ┌────────▼────────┐
                                  │    Databricks    │
                                  │Lakeview Dashboard│  (visualização)
                                  └─────────────────┘
```

---

## Componentes de Infraestrutura

### AWS Lambda

Duas funções Lambda são responsáveis pela ingestão de dados:

| Função | Descrição | Arquivo |
|--------|-----------|---------|
| `download-csv-consumer` | Baixa o CSV mensal de reclamações de `dados.mj.gov.br` e salva no S3 | [app/src/lambda/lambda_download_csv.py](../app/src/lambda/lambda_download_csv.py) |
| `screp` | Scraper Selenium que extrai o texto completo das reclamações via navegador headless | [app/src/lambda/screp_reclamacoes.py](../app/src/lambda/screp_reclamacoes.py) |

As Lambdas são empacotadas via `Makefile` e armazenadas no S3 antes do deploy pelo Terraform.

---

### ECS Fargate — Selenium Standalone

O scraper Selenium exige um navegador real. Para isso, um container **Selenium Standalone** roda no ECS Fargate:

- Imagem: configurável via variável Terraform (`var.docker_image_name`)
- Comunicação: a Lambda conecta via DNS interno `selenium.<namespace>` (AWS Cloud Map)
- Monitoramento: health check no endpoint `/status`
- Logs: CloudWatch Logs com retenção de 7 dias

O ECS é orquestrado pelo Airflow — o `desired_count` do serviço é controlado dinamicamente e ignorado pelo Terraform (`lifecycle.ignore_changes`).

---

### Databricks

Substitui o cluster Hadoop/Spark on-premise. Responsável por todo o processamento das camadas de dados:

- **Notebooks** gerenciados por Terraform ([IaC/notebooks.tf](../IaC/notebooks.tf))
- **Jobs** automatizados com notificação por e-mail ([IaC/jobs.tf](../IaC/jobs.tf))
- **Dashboard Lakeview** gerenciado por Terraform ([IaC/dashboards.tf](../IaC/dashboards.tf))
- Autenticação via Service Principal (OAuth M2M)

---

### Databricks Lakeview Dashboard

A visualização dos dados é feita por um **Dashboard Lakeview** nativo do Databricks, implantado automaticamente via Terraform a partir do arquivo [dash/dash_consumidor.lvdash.json](../dash/dash_consumidor.lvdash.json).

O dashboard consome as tabelas Gold e apresenta os seguintes componentes:

**Datasets (queries SQL):**

| Dataset | Tabela Gold | Descrição |
|---------|-------------|-----------|
| `ds_reclamacao` | `g_consumidor.reclamacaotopten` | Top 10 reclamações por instituição |
| `ds_mediaresposta` | `g_consumidor.mediaresposta` | Tempo médio de resposta por instituição |
| `ds_mediaavaliacao` | `g_consumidor.mediaavaliacao` | Média de avaliação por instituição |
| `ds_reclamacaouf` | `g_consumidor.reclamacaouf` | Volume de reclamações por UF |

**Visualizações:**

| Tipo | Título | Descrição |
|------|--------|-----------|
| KPI (counter) | Total Reclamações | Soma total de reclamações |
| KPI (counter) | Média Tempo Resposta (dias) | Média geral do tempo de resposta |
| KPI (counter) | Média Avaliação | Nota média dos consumidores |
| Gráfico de barras | Total Reclamações por Instituição | Ranking horizontal por volume |
| Gráfico de barras | Quantidade Reclamações por UF | Distribuição geográfica |
| Gráfico de linhas | Quantidade de reclamações por mês | Evolução temporal |

**Filtros globais:** Instituição Financeira e Ano-Mês, aplicados a todos os widgets simultaneamente.

---

### S3 — Data Lake

O S3 é o armazenamento central do pipeline. Os dados são organizados por camada:

```
s3://{env}-{region}-data-master/
├── raw/          # Arquivos CSV brutos (Bronze)
├── silver/       # Dados filtrados em Parquet (Silver)
└── gold/         # Agregações em Parquet (Gold)
```

O acesso ao S3 pelas Lambdas e pelo ECS é feito via **S3 Gateway Endpoint**, sem tráfego pela internet e sem custo adicional.

---

### VPC e Rede

- VPC dedicada com subnets públicas e privadas configuráveis
- Subnets privadas sem NAT Gateway (isolamento intencional para redução de custo)
- S3 Gateway Endpoint para acesso direto ao S3
- AWS Cloud Map para descoberta de serviço do Selenium (DNS interno)
- Security Groups isolados para Lambda e ECS

---

### GitHub Actions — CI/CD

O pipeline de CI/CD é acionado automaticamente por **push** nas branches protegidas:

```
Push para branch
    │
    ├── Build Lambda packages (make all)
    ├── Upload para S3 (aws s3 cp)
    ├── terraform init
    ├── terraform validate
    ├── terraform plan
    ├── terraform apply
    └── Sync DAGs para S3 (apenas produção)
```

Workflows:

| Arquivo | Gatilho |
|---------|--------|
| [.github/workflows/develop.yml](../.github/workflows/develop.yml) | Push para `develop` → deploy `dev` |
| [.github/workflows/main.yml](../.github/workflows/main.yml) | Push para `main` → deploy `pro` + sync DAGs para S3 |
| [.github/workflows/terraform.yml](../.github/workflows/terraform.yml) | Workflow reusável (chamado pelos dois acima) |

---

## Camadas de Dados — Medallion Architecture

A arquitetura Medallion organiza os dados em três camadas de qualidade crescente: **Bronze**, **Silver** e **Gold**.

### Bronze — Dados Brutos

**Objetivo:** Ingerir o dado exatamente como recebido, sem transformações.

- **Fonte:** CSV mensal baixado de `dados.mj.gov.br` pela Lambda
- **Formato de saída:** Parquet
- **Tabela:** `b_consumidor.consumidor`
- **Notebook:** [app/src/bronze.py](../app/src/bronze.py)

Nesta camada, todos os campos originais são preservados, incluindo dados de todos os segmentos econômicos. Serve como fonte de verdade imutável do dado bruto.

---

### Silver — Dados Filtrados e Limpos

**Objetivo:** Aplicar regras de negócio para selecionar apenas o subconjunto relevante.

- **Filtro aplicado:** Apenas reclamações do setor de **Serviços Financeiros**
- **Formato de saída:** Parquet
- **Tabela:** `s_consumidor.consumidorservicosfinanceiros`
- **Notebook:** [app/src/silver.py](../app/src/silver.py)

A camada Silver elimina registros irrelevantes e padroniza os tipos de dados, reduzindo o volume processado nas etapas seguintes.

---

### Gold — Dados Agregados para Análise

**Objetivo:** Gerar visões analíticas prontas para consumo por ferramentas de BI.

São produzidas **5 tabelas Gold**, cada uma com um foco analítico distinto:

| Tabela | Descrição | Notebook |
|--------|-----------|---------|
| `g_consumidor.grupoProblema` | Top 10 grupos de problemas mais reclamados | [app/src/problema_gold.py](../app/src/problema_gold.py) |
| `g_consumidor.mediaavaliacao` | Média de avaliação dos consumidores por empresa | [app/src/avaliacao_gold.py](../app/src/avaliacao_gold.py) |
| `g_consumidor.mediaresposta` | Tempo médio de resposta por empresa | [app/src/resposta_gold.py](../app/src/resposta_gold.py) |
| `g_consumidor.reclamacaouf` | Volume de reclamações por estado (UF) | [app/src/uf_gold.py](../app/src/uf_gold.py) |
| `g_consumidor.reclamacao` | Ranking das reclamações mais frequentes | [app/src/reclamacao_gold.py](../app/src/reclamacao_gold.py) |

---

## Orquestração — Airflow DAGs

O projeto utiliza **dois DAGs** no Airflow, cada um responsável por um pipeline de ingestão distinto.

### DAG Mensal — ETL Databricks

**Arquivo:** [app/src/airflow/dags/databricks_etl_dag.py](../app/src/airflow/dags/databricks_etl_dag.py)  
**Schedule:** Dia 15 de cada mês, à meia-noite  
**Objetivo:** Baixar o CSV consolidado mensal, processar nas camadas Bronze → Silver → Gold.

```
create_tables
     │
     ▼
  download_csv (Lambda)
     │
     ▼
   bronze
     │
     ▼
   silver
     │
     ├──► problema_gold
     ├──► avaliacao_gold
     ├──► mediaresposta_gold
     ├──► reclamacaouf_gold
     └──► reclamacao_gold
```

Os jobs Databricks são executados via `DatabricksRunNowOperator` com o parâmetro `dat_ref_carga` gerado dinamicamente. Em caso de falha, cada task faz até 3 retentativas com intervalo de 1 minuto.

---

### DAG Diário — Web Scraper

**Arquivo:** [app/src/airflow/dags/dag_screp.py](../app/src/airflow/dags/dag_screp.py)  
**Schedule:** Diariamente às 6h  
**Objetivo:** Extrair incrementalmente o texto completo das reclamações publicadas em `consumidor.gov.br`.

```
start_ecs_selenium (desired_count = 1)
     │
     ▼
wait_selenium_ready (health check /status, timeout 10 min)
     │
     ▼
invoke_lambda_scraper
     │
     ▼
stop_ecs_selenium (desired_count = 0)  ← executa sempre (ALL_DONE)
```

O scraper utiliza um mecanismo de **bastão** (arquivo de controle no S3) que armazena o timestamp da última execução, garantindo que apenas reclamações novas sejam coletadas a cada execução. O container ECS Selenium é ligado sob demanda e desligado após a conclusão, independente do resultado (`TriggerRule.ALL_DONE`), evitando custos desnecessários.

---

## Ambientes

O projeto suporta múltiplos ambientes via Terraform workspaces:

| Workspace | Ambiente | Branch CI/CD |
|-----------|----------|--------------|
| `dev`     | Desenvolvimento | `develop` |
| `pro`     | Produção        | `main`    |

O nome do bucket S3 segue o padrão: `{env}-{region}-data-master`
Exemplo: `dev-us-east-2-data-master`

---

## Melhorias Futuras

- Análise de sentimentos no texto das reclamações (NLP)
- Alertas automáticos para anomalias nos KPIs Gold
- Novas visões analíticas (sazonalidade, evolução temporal)
- Streaming para ingestão em tempo real (complementando o batch mensal)
