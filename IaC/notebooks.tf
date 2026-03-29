# Obtém detalhes sobre o usuário
data "databricks_current_user" "me" {}

resource "databricks_notebook" "bronze_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/bronze.py"
  language = var.notebook_language
  source   = "../app/src/bronze.py"
}

resource "databricks_notebook" "bronze_screp_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/bronze_screp.py"
  language = var.notebook_language
  source   = "../app/src/bronze_screp.py"
}

output "notebook_url" {
 value = databricks_notebook.bronze_notebook.url
}

resource "databricks_notebook" "silver_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/silver.py"
  language = var.notebook_language
  source   = "../app/src/silver.py"
}

resource "databricks_notebook" "problema_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/problema_gold.py"
  language = var.notebook_language
  source   = "../app/src/problema_gold.py"
}

resource "databricks_notebook" "reclamacao_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/reclamacao_gold.py"
  language = var.notebook_language
  source   = "../app/src/reclamacao_gold.py"
}

resource "databricks_notebook" "resposta_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/resposta_gold.py"
  language = var.notebook_language
  source   = "../app/src/resposta_gold.py"
}

resource "databricks_notebook" "uf_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/uf_gold.py"
  language = var.notebook_language
  source   = "../app/src/uf_gold.py"
}

resource "databricks_notebook" "avaliacao_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/avaliacao_gold.py"
  language = var.notebook_language
  source   = "../app/src/avaliacao_gold.py"
}

resource "databricks_notebook" "silver_ai_classificacao_relatos_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/silver_ai_classificacao_relatos.py"
  language = var.notebook_language
  source   = "../app/src/silver_ai_classificacao_relatos.py"
}

resource "databricks_notebook" "status_ai_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/status_ai_gold.py"
  language = var.notebook_language
  source   = "../app/src/status_ai_gold.py"
}

resource "databricks_notebook" "nota_ai_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/nota_ai_gold.py"
  language = var.notebook_language
  source   = "../app/src/nota_ai_gold.py"
}

resource "databricks_notebook" "macro_categoria_ai_gold_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/macro_categoria_ai_gold.py"
  language = var.notebook_language
  source   = "../app/src/macro_categoria_ai_gold.py"
}

# Notebooks SQL para criação de databases e tabelas
resource "databricks_notebook" "create_consumidor_tables_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/create_consumidor_tables.py"
  language = var.notebook_language
  source   = "../app/src/create_consumidor_tables.py"
}

# Notebooks SQL para drop de databases e tabelas
resource "databricks_notebook" "drop_consumidor_tables_notebook" {
  path     = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}/drop_consumidor_tables.py"
  language = var.notebook_language
  source   = "../app/src/drop_consumidor_tables.py"
}
