# Job para criação de databases e tabelas (deve ser executado antes dos jobs de carga)
resource "databricks_job" "create_databases_job" {

  name = "Create Databases and Tables Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "create_tables_db_task"

    notebook_task {
      notebook_path = databricks_notebook.create_consumidor_tables_notebook.path
      base_parameters = {
        "env"                        = var.environment
        # "databricks_grant_principal" = var.databricks_grant_principal
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

output "create_databases_job_url" {
  value = databricks_job.create_databases_job.url
}

# Job para drop de databases e tabelas (executado de forma independente)
resource "databricks_job" "drop_databases_job" {

  name = "Drop Databases and Tables Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "drop_tables_db_task"

    notebook_task {
      notebook_path = databricks_notebook.drop_consumidor_tables_notebook.path
      base_parameters = {
        "env" = var.environment
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

output "drop_databases_job_url" {
  value = databricks_job.drop_databases_job.url
}

resource "databricks_job" "silver_ai_classificacao_relatos_job" {

  name = "Silver AI Classificacao Relatos Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "silver_ai_classificacao_relatos_task"

    notebook_task {
      notebook_path = databricks_notebook.silver_ai_classificacao_relatos_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "llm_model"   = "databricks-qwen3-next-80b-a3b-instruct"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

output "silver_ai_classificacao_relatos_job_url" {
  value = databricks_job.silver_ai_classificacao_relatos_job.url
}

resource "databricks_job" "bronze_screp_job" {

  name = "Bronze Screp Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "bronze_screp_task"

    notebook_task {
      notebook_path = databricks_notebook.bronze_screp_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "env"         = var.environment
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "kaggle_backfill_bronze_job" {

  name = "Kaggle Backfill Bronze Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "kaggle_backfill_bronze_task"

    notebook_task {
      notebook_path = databricks_notebook.bronze_kaggle_historico_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "env"         = var.environment
        "s3_key"      = "screp/historico/kaggle/dados2025.json"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "kaggle_backfill_silver_ai_job" {

  name = "Kaggle Backfill Silver AI Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "kaggle_backfill_silver_ai_task"

    notebook_task {
      notebook_path = databricks_notebook.silver_ai_classificacao_relatos_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "llm_model"   = "databricks-qwen3-next-80b-a3b-instruct"
        "modo"        = "historico"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "kaggle_backfill_status_gold_job" {

  name = "Kaggle Backfill Status Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "kaggle_backfill_status_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.status_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "modo"        = "historico"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "kaggle_backfill_nota_gold_job" {

  name = "Kaggle Backfill Nota Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "kaggle_backfill_nota_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.nota_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "modo"        = "historico"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "kaggle_backfill_macro_gold_job" {

  name = "Kaggle Backfill Macro Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "kaggle_backfill_macro_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.macro_categoria_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "modo"        = "historico"
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

output "bronze_screp_job_url" {
  value = databricks_job.bronze_screp_job.url
}

resource "databricks_job" "bronze_job" {

  name = "Bronze Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "bronze_task"

    notebook_task {
      notebook_path = databricks_notebook.bronze_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
        "env"         = var.environment
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

output "job_url" {
  value = databricks_job.bronze_job.url
}

resource "databricks_job" "silver_job" {

  name = "Silver Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "silver_task"

    notebook_task {
      notebook_path = databricks_notebook.silver_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "problema_gold_job" {

  name = "Problema Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "problema_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.problema_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "reclamacao_gold_job" {

  name = "Reclamacao Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "reclamacao_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.reclamacao_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "resposta_gold_job" {

  name = "Resposta Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "resposta_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.resposta_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "uf_gold_job" {

  name = "UF Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "uf_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.uf_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "avaliacao_gold_job" {

  name = "Avaliacao Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "avaliacao_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.avaliacao_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "status_ai_gold_job" {

  name = "Status AI Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "status_ai_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.status_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "nota_ai_gold_job" {

  name = "Nota AI Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "nota_ai_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.nota_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}

resource "databricks_job" "macro_categoria_ai_gold_job" {

  name = "Macro Categoria AI Gold Job"

  environment {
    environment_key = var.environment_key

    spec {
      environment_version = var.environment_version
    }
  }

  task {
    task_key = "macro_categoria_ai_gold_task"

    notebook_task {
      notebook_path = databricks_notebook.macro_categoria_ai_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }

  email_notifications {
    on_failure = var.notification_emails
  }
}
