#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/airflow/.local/bin:${PATH}"

AIRFLOW_DIRS=(/opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins /opt/airflow/config)
if [ "$(id -u)" -eq 0 ]; then
  mkdir -p "${AIRFLOW_DIRS[@]}"
  chown -R 50000:0 "${AIRFLOW_DIRS[@]}"
  exec su airflow -s /bin/bash -c "exec $0"
fi

AIRFLOW_BIN="$(command -v airflow)"

required_smtp_vars=(
  AIRFLOW__SMTP__SMTP_HOST
  AIRFLOW__SMTP__SMTP_PORT
  AIRFLOW__SMTP__SMTP_MAIL_FROM
)
for variable_name in "${required_smtp_vars[@]}"; do
  if [ -z "${!variable_name:-}" ]; then
    echo "ERRO: variável SMTP obrigatória não configurada: ${variable_name}" >&2
    exit 1
  fi
done

AIRFLOW_NOTIFICATION_EMAILS="${AIRFLOW_NOTIFICATION_EMAILS:-lucas_san20@hotmail.com}"
KAGGLE_BACKFILL_MES="${KAGGLE_BACKFILL_MES:-2022-07}"

"$AIRFLOW_BIN" db migrate
"$AIRFLOW_BIN" users create --username "$AIRFLOW_ADMIN_USERNAME" --firstname Admin --lastname User \
  --role Admin --email "$AIRFLOW_ADMIN_EMAIL" --password "$AIRFLOW_ADMIN_PASSWORD" || true

python - <<'PY'
import os
import json
from airflow.models import Connection, Variable
from airflow.settings import Session

session = Session()
def upsert_conn(conn):
    current = session.query(Connection).filter(Connection.conn_id == conn.conn_id).one_or_none()
    if current:
        current.conn_type, current.host, current.login, current.password = conn.conn_type, conn.host, conn.login, conn.password
        current.extra = conn.extra
    else:
        session.add(conn)

upsert_conn(Connection(
    conn_id="aws_default",
    conn_type="aws",
    extra=json.dumps({
        "region_name": os.environ["AWS_REGION"],
        "config_kwargs": {
            "connect_timeout": 900,
            "read_timeout": 900,
            "tcp_keepalive": True,
        },
    }),
))
upsert_conn(Connection(conn_id="databricks_default", conn_type="databricks", host=os.environ["DATABRICKS_HOST"], password=os.environ["DATABRICKS_TOKEN"]))

env = os.environ.get("AIRFLOW_ENV", "dev")
values = {
    "env": env, "environment": env,
    "dat_ref_carga": os.environ.get("DAT_REF_CARGA", ""),
    "dat_ref_carga_m": os.environ.get("DAT_REF_CARGA_M", ""),
    "kaggle_backfill_mes": os.environ.get("KAGGLE_BACKFILL_MES", "2022-07"),
    "aws_region": os.environ.get("AWS_REGION", "us-east-2"),
    "project": os.environ.get("PROJECT", "data-master"),
    "ecs_cluster": os.environ.get("ECS_CLUSTER", f"data-master-{env}-cluster"),
    "ecs_service": os.environ.get("ECS_SERVICE", f"data-master-{env}-selenium-svc"),
    "lambda_screp": os.environ.get("LAMBDA_SCREP", f"data-master-{env}-screp"),
    "lambda_download": os.environ.get("LAMBDA_DOWNLOAD", f"download-csv-consumer-{env}"),
    "notification_emails": os.environ.get("AIRFLOW_NOTIFICATION_EMAILS", "lucas_san20@hotmail.com"),
}
for key, value in values.items():
    if key == "kaggle_backfill_mes":
        current = session.query(Variable).filter(Variable.key == key).one_or_none()
        if current is None:
            Variable.set(key, value)
    else:
        Variable.set(key, value)
session.commit()
session.close()
PY
