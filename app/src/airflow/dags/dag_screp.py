import json
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.sensors.python import PythonSensor
from airflow.utils.trigger_rule import TriggerRule

ENV = Variable.get("env", default_var="dev")
PROJECT = "data-master"
REGION = "us-east-2"
AWS_CONN_ID = "aws_default"

CLUSTER_NAME = f"{PROJECT}-{ENV}-cluster"
SERVICE_NAME = f"{PROJECT}-{ENV}-selenium-svc"
LAMBDA_NAME = f"{PROJECT}-{ENV}-screp"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def get_dat_ref_carga():
    """
    Define a data de referência para carga.
    Se a variável 'dat_ref_carga' estiver vazia, usa a data atual.
    Formato de saída: YYYY-MM-DD
    """
    if Variable.get('dat_ref_carga').strip() == "":
        dat_ref_carga = datetime.now()
        dat_ref_carga = dat_ref_carga.strftime("%Y%m%d")
    else:    
        dat_ref_carga = Variable.get('dat_ref_carga')
    
    return dat_ref_carga

def _update_ecs_service(desired_count: int):
    from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook

    hook = AwsBaseHook(aws_conn_id=AWS_CONN_ID, client_type="ecs")
    client = hook.get_client_type(region_name=REGION)
    client.update_service(
        cluster=CLUSTER_NAME,
        service=SERVICE_NAME,
        desiredCount=desired_count,
    )


def _check_selenium_ready():
    from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook

    hook = AwsBaseHook(aws_conn_id=AWS_CONN_ID, client_type="ecs")
    client = hook.get_client_type(region_name=REGION)
    response = client.describe_services(cluster=CLUSTER_NAME, services=[SERVICE_NAME])
    service = response["services"][0]
    return service["runningCount"] >= 1 and service["pendingCount"] == 0


with DAG(
    dag_id="screp_daily",
    description="Coleta diária de reclamações - consumidor.gov.br",
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["screp", "data-master"],
) as dag:

    start_selenium = PythonOperator(
        task_id="start_selenium_service",
        python_callable=_update_ecs_service,
        op_kwargs={"desired_count": 1},
    )

    wait_selenium = PythonSensor(
        task_id="wait_selenium_ready",
        python_callable=_check_selenium_ready,
        poke_interval=30,
        timeout=600,
        mode="poke",
    )

    invoke_lambda = LambdaInvokeFunctionOperator(
        task_id="invoke_lambda_screp",
        function_name=LAMBDA_NAME,
        payload=json.dumps({"env": ENV}),
        invocation_type="RequestResponse",
        region_name=REGION,
        aws_conn_id=AWS_CONN_ID,
        botocore_config={"read_timeout": 900, "connect_timeout": 30},
    )

    stop_selenium = PythonOperator(
        task_id="stop_selenium_service",
        python_callable=_update_ecs_service,
        op_kwargs={"desired_count": 0},
        trigger_rule=TriggerRule.ALL_DONE,
    )

    bronze_screp_task = DatabricksRunNowOperator(
        task_id="run_bronze_screp_job",
        job_name="Bronze Screp Job",
        notebook_params={
            "datRefCarga": get_dat_ref_carga(),
            "env": ENV,
        },
        databricks_conn_id="databricks_default",
    )

    silver_ai_classificacao_relatos_task = DatabricksRunNowOperator(
        task_id="run_silver_ai_classificacao_relatos_job",
        job_name="Silver AI Classificacao Relatos Job",
        notebook_params={
            "datRefCarga": get_dat_ref_carga(),
            "llm_model": "databricks-gpt-5-2",
        },
        databricks_conn_id="databricks_default",
    )

    status_ai_gold_task = DatabricksRunNowOperator(
        task_id="run_status_ai_gold_job",
        job_name="Status AI Gold Job",
        notebook_params={
            "datRefCarga": get_dat_ref_carga(),
        },
        databricks_conn_id="databricks_default",
    )

    nota_ai_gold_task = DatabricksRunNowOperator(
        task_id="run_nota_ai_gold_job",
        job_name="Nota AI Gold Job",
        notebook_params={
            "datRefCarga": get_dat_ref_carga(),
        },
        databricks_conn_id="databricks_default",
    )

    macro_categoria_ai_gold_task = DatabricksRunNowOperator(
        task_id="run_macro_categoria_ai_gold_job",
        job_name="Macro Categoria AI Gold Job",
        notebook_params={
            "datRefCarga": get_dat_ref_carga(),
        },
        databricks_conn_id="databricks_default",
    )

    # invoke_lambda é upstream de stop_selenium (cleanup) e de bronze_screp_task.
    # bronze_screp_task aguarda ambos: garante cleanup antes de iniciar a carga
    # e falha se o lambda não tiver gerado o arquivo.
    start_selenium >> wait_selenium >> invoke_lambda >> [stop_selenium, bronze_screp_task]
    stop_selenium >> bronze_screp_task
    bronze_screp_task >> silver_ai_classificacao_relatos_task
    silver_ai_classificacao_relatos_task >> [status_ai_gold_task, nota_ai_gold_task, macro_categoria_ai_gold_task]
