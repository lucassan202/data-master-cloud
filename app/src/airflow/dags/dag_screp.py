import json
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
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
        botocore_config={"read_timeout": 620, "connect_timeout": 30},
    )

    stop_selenium = PythonOperator(
        task_id="stop_selenium_service",
        python_callable=_update_ecs_service,
        op_kwargs={"desired_count": 0},
        trigger_rule=TriggerRule.ALL_DONE,
    )

    start_selenium >> wait_selenium >> invoke_lambda >> stop_selenium
