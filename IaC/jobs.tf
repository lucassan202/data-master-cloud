variable "datrefcarga" {
  description = "Data de referência para carga no formato string."
  type        = string  
}

variable "environment_key" {
  description = "Chave do ambiente"
  type        = string
}

variable "environment_version" {
  description = "Versão do ambiente"
  type        = string 
}

variable "emails" {
  description = "Lista de e-mails para notificação de sucesso ou falha"
  type        = list(string)  
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
      }
    }
  }

  email_notifications {
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
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
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
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
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
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
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
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
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
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
    on_success = [ var.emails ]
    on_failure = [ var.emails ]
  }
}
