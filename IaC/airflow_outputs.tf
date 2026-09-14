output "airflow_url" {
  description = "URL do Airflow em produção"
  value       = local.airflow_enabled ? "http://${aws_instance.airflow[0].public_ip}:8080" : null
}

output "airflow_public_ip" {
  value = local.airflow_enabled ? aws_instance.airflow[0].public_ip : null
}

output "airflow_ssh_command" {
  value = local.airflow_enabled ? "ssh -i ${local_sensitive_file.airflow_private_key[0].filename} ubuntu@${aws_instance.airflow[0].public_ip}" : null
}

output "airflow_rds_endpoint" {
  value = local.airflow_enabled ? aws_db_instance.airflow[0].endpoint : null
}

output "airflow_private_key_path" {
  value = local.airflow_enabled ? local_sensitive_file.airflow_private_key[0].filename : null
}
