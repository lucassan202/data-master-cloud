# Busca o SQL Warehouse pelo nome
data "databricks_sql_warehouses" "by_name" {
  warehouse_name_contains = var.warehouse_name
}

resource "databricks_dashboard" "consumidor" {
  display_name         = "Consumidor"
  warehouse_id         = tolist(data.databricks_sql_warehouses.by_name.ids)[0]
  serialized_dashboard = file("../dash/dash_consumidor.lvdash.json")
  parent_path          = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}"
  embed_credentials    = false
}

resource "databricks_dashboard" "ai_gold" {
  display_name         = "Análise IA Gold"
  warehouse_id         = tolist(data.databricks_sql_warehouses.by_name.ids)[0]
  serialized_dashboard = file("../dash/dash_ai_gold.lvdash.json")
  parent_path          = "${data.databricks_current_user.me.home}/${var.notebook_subdirectory}"
  embed_credentials    = false
}
