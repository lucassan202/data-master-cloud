# Obtém detalhes sobre o usuário
data "databricks_current_user" "me" {}

variable "notebook_subdirectory" {
  description = "Nome para diretório onde armazenar o notebook."
  type        = string
  default     = "Consumidor"
}
variable "notebook_language" {
  description = "Linguagem de programação do notebook."
  type        = string
}

resource "databricks_notebook" "bronze_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/bronze.py"
  language = var.notebook_language
  source   = "../app/src/bronze.py"
}

output "notebook_url" {
 value = databricks_notebook.bronze_notebook.url
}

resource "databricks_notebook" "silver_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/silver.py"
  language = var.notebook_language
  source   = "../app/src/silver.py"
}

resource "databricks_notebook" "problema_gold_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/problema_gold.py"
  language = var.notebook_language
  source   = "../app/src/problema_gold.py"
}

resource "databricks_notebook" "reclamacao_gold_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/reclamacao_gold.py"
  language = var.notebook_language
  source   = "../app/src/reclamacao_gold.py"
}

resource "databricks_notebook" "resposta_gold_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/resposta_gold.py"
  language = var.notebook_language
  source   = "../app/src/resposta_gold.py"
}

resource "databricks_notebook" "uf_gold_notebook" {
  path     = "/lucas_san20@hotmail.com/${var.notebook_subdirectory}/uf_gold.py"
  language = var.notebook_language
  source   = "../app/src/uf_gold.py"
}

