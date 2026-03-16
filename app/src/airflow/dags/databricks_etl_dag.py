"""
DAG para orquestrar os jobs Databricks do pipeline ETL
Sequência: lambda >> bronze >> silver >> [problema_gold, top_ten, avaliacao_gold, resposta_gold, uf_gold]
Agendamento: Mensal no dia 15
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.models import Variable
import json

def get_dat_ref_carga():
    """
    Define a data de referência para carga.
    Se a variável 'dat_ref_carga' estiver vazia, usa a data atual - 30 dias.
    Formato de saída: YYYY-MM
    """
    if Variable.get('dat_ref_carga') == "":
        dat_ref_carga = datetime.now() - timedelta(days=30)
        dat_ref_carga = dat_ref_carga.strftime("%Y-%m")
    else:    
        dat_ref_carga = Variable.get('dat_ref_carga')
    
    return dat_ref_carga

# Configurações padrão da DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=1),
}

# Definição da DAG
with DAG(
    dag_id='databricks_etl_pipeline',
    default_args=default_args,
    description='DAG para executar jobs Databricks do pipeline ETL (bronze >> silver >> gold)',
    schedule_interval='0 0 15 * *',  # Executa no dia 15 de cada mês à meia-noite
    start_date=datetime(2026, 1, 15),
    catchup=False,
    tags=['databricks', 'etl', 'bronze', 'silver', 'gold'],
) as dag:

    # Task Lambda - Download dos arquivos CSV do dados.mj.gov.br para S3
    lambda_download_task = LambdaInvokeFunctionOperator(
        task_id='invoke_lambda_download_csv',
        function_name='download-csv-consumer',
        payload=json.dumps({"datRefCarga": get_dat_ref_carga(), "ENV": Variable.get('environment')}),
    )

    # Task Bronze - Extração e carga inicial
    bronze_task = DatabricksRunNowOperator(
        task_id='run_bronze_job',
        job_name='Bronze Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga(),
            'env': Variable.get('environment')
        },
        databricks_conn_id='databricks_default',
    )

    # Task Silver - Processamento e transformação
    silver_task = DatabricksRunNowOperator(
        task_id='run_silver_job',
        job_name='Silver Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Task Grupo Problema - Processamento Gold
    problema_gold_task = DatabricksRunNowOperator(
        task_id='run_problema_gold_job',
        job_name='Problema Gold Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Task Top Ten (Reclamação) - Processamento Gold
    top_ten_task = DatabricksRunNowOperator(
        task_id='run_top_ten_job',
        job_name='Reclamacao Gold Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Task Avaliação - Processamento Gold
    avaliacao_gold_task = DatabricksRunNowOperator(
        task_id='run_avaliacao_gold_job',
        job_name='Avaliacao Gold Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Task Resposta - Processamento Gold
    resposta_gold_task = DatabricksRunNowOperator(
        task_id='run_resposta_gold_job',
        job_name='Resposta Gold Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Task UF - Processamento Gold
    uf_gold_task = DatabricksRunNowOperator(
        task_id='run_uf_gold_job',
        job_name='UF Gold Job',
        notebook_params={
            'datRefCarga': get_dat_ref_carga()
        },
        databricks_conn_id='databricks_default',
    )

    # Definição das dependências
    # lambda >> bronze >> silver >> jobs gold (paralelos)
    lambda_download_task >> bronze_task >> silver_task >> [
        problema_gold_task,
        top_ten_task,
        avaliacao_gold_task,
        resposta_gold_task,
        uf_gold_task
    ]
