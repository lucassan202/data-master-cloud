# Arquitetura e Documentação Técnica — data-master-cloud

## Contexto do Projeto

O **data-master-cloud** é a evolução cloud-native do projeto [data-master](https://github.com/besgam/data-master), que analisava reclamações de consumidores publicadas no portal [consumidor.gov.br](https://www.consumidor.gov.br) utilizando um cluster Hadoop/Spark on-premise.

O objetivo da migração foi eliminar a necessidade de infraestrutura física gerenciada manualmente, substituindo-a por serviços gerenciados da AWS e Databricks. Com isso, o projeto ganhou:

- **Escalabilidade automática** — sem provisionamento manual de servidores
- **Infraestrutura como Código** — toda a nuvem definida em Terraform
- **CI/CD integrado** — deploy automatizado via GitHub Actions
- **Custo sob demanda** — recursos pagos apenas quando utilizados

O pipeline coleta dados mensais de reclamações, processa-os em camadas de qualidade progressiva (Medallion Architecture) e disponibiliza visões analíticas agregadas para consumo por ferramentas de BI.

---

## Arquitetura de Alto Nível

```
                        ┌─────────────────────────────────────────────┐
                        │               AWS Cloud                      │
                        │                                             │
  dados.mj.gov.br ──►  │  Lambda (CSV Downloader)                    │
                        │        │                                    │
  consumidor.gov.br ──► │  ECS Fargate (Selenium) ──► Lambda (Scraper)│
                        │        │                         │          │
                        │        └──────────┬──────────────┘          │
                        │                   ▼                         │
                        │              S3 (Data Lake)                 │
                        │         ┌─────────────────┐                 │
                        │         │  Bronze / Raw   │                 │
                        │         └────────┬────────┘                 │
                        │                  ▼                          │
                        │         ┌─────────────────┐                 │
                        │         │ Silver / Filtered│                 │
                        │         └────────┬────────┘                 │
                        │                  ▼                          │
                        │         ┌─────────────────┐                 │
                        │         │  Gold / Agregado │                 │
                        │         └────────┬────────┘                 │
                        │                  │                          │
                        └──────────────────┼──────────────────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │  Databricks  │  (processamento)
                                    │  Airflow DAG │  (orquestração)
                                    └─────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │   Power BI  │  (visualização)
                                    └─────────────┘
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

- Imagem: `selenium/standalone-chrome`
- Comunicação: a Lambda conecta via DNS interno `selenium.<namespace>` (AWS Cloud Map)
- Monitoramento: health check no endpoint `/status`
- Logs: CloudWatch Logs com retenção de 7 dias

O ECS é orquestrado pelo Airflow — o `desired_count` do serviço é controlado dinamicamente e ignorado pelo Terraform (`lifecycle.ignore_changes`).

---

### Databricks

Substitui o cluster Hadoop/Spark on-premise. Responsável por todo o processamento das camadas de dados:

- **Notebooks** gerenciados por Terraform ([IaC/notebooks.tf](../IaC/notebooks.tf))
- **Jobs** automatizados com notificação por e-mail ([IaC/jobs.tf](../IaC/jobs.tf))
- Autenticação via Service Principal (OAuth M2M)

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

O pipeline de CI/CD é acionado automaticamente por Pull Requests:

```
PR aberto
    │
    ├── Build Lambda packages (make all)
    ├── Upload para S3 (aws s3 cp)
    ├── terraform init
    ├── terraform validate
    ├── terraform plan
    └── terraform apply
```

Workflows:

| Arquivo | Gatilho |
|---------|---------|
| [.github/workflows/develop.yml](../.github/workflows/develop.yml) | PR para `develop` → deploy `dev` |
| [.github/workflows/main.yml](../.github/workflows/main.yml) | PR para `main` → deploy `pro` |
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

## Orquestração — Airflow DAG

O DAG do Airflow ([app/src/airflow/dags/databricks_etl_dag.py](../app/src/airflow/dags/databricks_etl_dag.py)) coordena a execução dos jobs Databricks na seguinte ordem:

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
- Dashboards Power BI publicados automaticamente via CI/CD
- Streaming para ingestão em tempo real (substituindo o batch mensal)
