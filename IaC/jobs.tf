variable "datrefcarga" {
  description = "Data de referência para carga no formato string."
  type        = string
  default     = "2026-01"
}

resource "databricks_job" "bronze_job" {
  
  name = "Bronze Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "bronze_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.bronze_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}

output "job_url" {
  value = databricks_job.bronze_job.url
}

resource "databricks_job" "silver_job" {
  
  name = "Silver Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "silver_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.silver_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}

resource "databricks_job" "problema_gold_job" {
  
  name = "Problema Gold Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "problema_gold_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.problema_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}

resource "databricks_job" "reclamacao_gold_job" {
  
  name = "Reclamacao Gold Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "reclamacao_gold_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.reclamacao_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}

resource "databricks_job" "resposta_gold_job" {
  
  name = "Resposta Gold Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "resposta_gold_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.resposta_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}

resource "databricks_job" "uf_gold_job" {
  
  name = "UF Gold Job"
  

  environment {
    environment_key = "Default"

    spec {
      environment_version = "4"
    }
  }
  
  task {
    task_key = "uf_gold_task"

    environment_key = "Default"
    
    notebook_task {
      notebook_path = databricks_notebook.uf_gold_notebook.path
      base_parameters = {
        "datRefCarga" = var.datrefcarga
      }
    }
  }
  
  email_notifications {
    on_success = [ "lucas_san20@hotmail.com" ]
    on_failure = [ "lucas_san20@hotmail.com" ]
  }
}
