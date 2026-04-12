# Análise para PR: `develop` -> `main`

> Referência de comparação usada nesta análise:
> - Base (`main`): `25c7cee`
> - Head (`develop`): `af3bc20`
>
> Observação: o repositório local está apenas com a branch `work`; a análise foi montada a partir do histórico de merges e da faixa de commits equivalente a `develop` acima de `main`.

## Resumo executivo

A faixa de mudanças entre `main` e `develop` adiciona uma evolução importante do pipeline de dados focada em classificação por IA, com:

- nova camada **bronze diária** para ingestão de reclamações;
- nova camada **silver de classificação de relatos com IA**;
- novas tabelas **gold diárias** para métricas derivadas por IA (nota, macro-categoria e status);
- atualização de **IaC** para notebooks/jobs no Databricks;
- inclusão de um **dashboard LakeView** para consumo analítico;
- ajustes de DAGs do Airflow e de scripts de criação/remoção de tabelas;
- atualização extensa da documentação de arquitetura.

## Principais modificações por domínio

### 1) Orquestração e automação

- Ajustes no workflow de CI/CD em `.github/workflows/develop.yml`.
- Atualizações em DAGs do Airflow (`dag_screp.py` e `databricks_etl_dag.py`) para acomodar o fluxo diário e novos estágios.

### 2) Infraestrutura como código (IaC)

- `IaC/jobs.tf`: expansão relevante da definição de jobs, com novos blocos para processamento IA.
- `IaC/notebooks.tf`: inclusão/ajuste de notebooks necessários para as novas etapas.
- `IaC/dashboards.tf`: inclusão de recursos para dashboard analítico.

### 3) Camadas de dados (bronze/silver/gold)

#### Bronze
- Novo script `app/src/bronze_screp.py` para processamento diário de dados da origem de reclamações.

#### Silver
- Novo script `app/src/silver_ai_classificacao_relatos.py` para classificação de relatos com IA e estruturação da camada silver.

#### Gold
- Novos scripts para tabelas/métricas gold com IA:
  - `app/src/nota_ai_gold.py`
  - `app/src/macro_categoria_ai_gold.py`
  - `app/src/status_ai_gold.py`

### 4) Suporte operacional

- Atualizações em `create_consumidor_tables.py` e `drop_consumidor_tables.py` para incluir as novas entidades.
- Ajustes em `app/src/lambda/screp_reclamacoes.py`.
- Atualização de `.gitignore`.

### 5) Visualização e documentação

- Inclusão de dashboard `dash/dash_ai_gold.lvdash.json` para visualização de resultados IA (camada gold).
- Revisão ampla em `docs/ARCHITECTURE.md` refletindo a nova arquitetura e os novos componentes.

## Impacto esperado

- Melhoria da capacidade analítica com classificações por IA em fluxo diário.
- Aumento de cobertura do pipeline (ingestão -> enriquecimento -> consumo em dashboard).
- Maior formalização de arquitetura e operação via documentação e IaC.

## Estatísticas consolidadas do diff

- **17 arquivos alterados**
- **1927 inserções**
- **126 deleções**

## Lista de commits incluídos (ordem cronológica na branch de origem)

1. `0de28f2` - criação bronze screp diario
2. `f2551e6` - silver classificação com IA
3. `64164af` - criação tabela silver ai classificação relato
4. `683f7e9` - gold diário ai
5. `7008d07` - dash ai gold
6. `30fe3ba` - atualização ARCHITECTURE.md
7. `62e216d` - melhorias
8. `3ba843c` - atualização ARCHITECTURE.md
9. `af3bc20` - atualização ARCHITECTURE.md

## Sugestão de título de PR

`feat(data-platform): pipeline diário bronze/silver/gold com classificação IA + dashboard e atualização de arquitetura`

## Sugestão de descrição curta para o PR

Este PR promove para a `main` a evolução da `develop` com o pipeline diário de dados de reclamações, incluindo classificação de relatos com IA (silver), tabelas gold derivadas (nota, macro-categoria e status), ajustes de orquestração/IaC no Databricks, inclusão de dashboard analítico e atualização da documentação de arquitetura.
