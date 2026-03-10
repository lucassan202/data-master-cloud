import io
import csv
import logging
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# O AWS Lambda encaminha automaticamente os logs do módulo `logging` para o
# CloudWatch Logs do grupo /aws/lambda/<nome-da-funcao>.
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Em execução local não há handler pré-configurado; no Lambda o runtime injeta o seu próprio.
if not logger.handlers:
    logging.basicConfig(format="%(levelname)s - %(message)s")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BUCKET_TEMPLATE = "{env}-us-east-2-data-master"
S3_PREFIX = "screp"
BST_KEY = f"{S3_PREFIX}/data_hora.bst"
DATE_FMT = "%d/%m/%Y %H:%M:%S"

# URL do servidor Selenium configurável por variável de ambiente,
# facilitando troca entre ambientes sem alteração de código.
SELENIUM_URL = os.environ.get("SELENIUM_URL", "http://localhost:4444")

# Colunas do CSV de saída (mantém ordem de campos do scraping original)
CSV_FIELDS = [
    "nomeEmpresa", "status", "tempoResposta", "dataOcorrido",
    "Cidade", "UF", "Relato", "Resposta", "Nota", "Comentario",
]


# ---------------------------------------------------------------------------
# Funções auxiliares S3
# ---------------------------------------------------------------------------

def get_bst_from_s3(s3_client, bucket: str) -> datetime:
    """
    Lê o arquivo de controle (bastão) do S3.

    Retorna a data/hora da última execução bem-sucedida.
    Se o arquivo ainda não existir (primeira execução), retorna None.

    :param s3_client: cliente boto3 S3
    :param bucket: nome do bucket
    :return: datetime da última atualização registrada, ou None
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=BST_KEY)
        content = response["Body"].read().decode("utf-8").strip()
        logger.info("Bastão lido do S3: %s", content)
        return datetime.strptime(content, DATE_FMT)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("NoSuchKey", "404"):
            logger.info("Arquivo de bastão não encontrado no S3 (primeira execução).")
            return None
        # Qualquer outro erro S3 deve ser propagado
        logger.exception("Erro inesperado ao ler bastão do S3.")
        raise


def save_bst_to_s3(s3_client, bucket: str, data_hora: str) -> None:
    """
    Persiste a data/hora da atualização atual no arquivo de controle (bastão) no S3.

    :param s3_client: cliente boto3 S3
    :param bucket: nome do bucket
    :param data_hora: string de data/hora no formato DD/MM/YYYY HH:MM:SS
    """
    s3_client.put_object(
        Bucket=bucket,
        Key=BST_KEY,
        Body=data_hora.encode("utf-8"),
        ContentType="text/plain",
    )
    logger.info("Bastão atualizado no S3: %s", data_hora)


def save_csv_to_s3(s3_client, bucket: str, records: list) -> str:
    """
    Serializa a lista de dicionários em CSV e faz upload para o S3.

    O nome do arquivo inclui o timestamp da execução para evitar sobrescrita.

    :param s3_client: cliente boto3 S3
    :param bucket: nome do bucket
    :param records: lista de dicts com os campos definidos em CSV_FIELDS
    :return: chave S3 do arquivo gerado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"{S3_PREFIX}/reclamacoes_{timestamp}.csv"

    # Monta o CSV inteiramente em memória para evitar I/O em disco
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)

    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
    logger.info("CSV gravado no S3: s3://%s/%s (%d registros)", bucket, key, len(records))
    return key


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def _init_driver() -> webdriver.Remote:
    """
    Instancia e retorna o WebDriver remoto (Firefox).

    :return: instância do WebDriver conectada ao servidor Selenium
    """
    options = Options()
    options.set_capability("se:name", "Screp Reclamacoes")
    logger.info("Conectando ao servidor Selenium em %s", SELENIUM_URL)
    driver = webdriver.Remote(options=options, command_executor=SELENIUM_URL)
    logger.info("WebDriver inicializado com sucesso.")
    return driver


def scrape_reclamacoes(driver: webdriver.Remote, data_pas: datetime | None) -> tuple:
    """
    Realiza o scraping do portal consumidor.gov.br e retorna os dados coletados.

    Navega para resultados anteriores clicando em 'btn-mais-resultados' até que
    a data exibida no contador seja menor ou igual ao bastão (data_pas), garantindo
    que todos os registros novos desde a última execução sejam capturados.

    :param driver: instância ativa do WebDriver
    :param data_pas: data/hora do bastão (última execução bem-sucedida), ou None na primeira execução
    :return: tupla (data_hora_str, lista_de_dicts_reclamacoes)
             onde data_hora_str é a data mais recente do portal no momento da execução
    """
    driver.get("https://consumidor.gov.br/pages/indicador/relatos/abrir")

    wait = WebDriverWait(driver, 60)

    # Aguarda o elemento de contador ser visível para capturar a data/hora
    wait.until(EC.visibility_of_element_located((By.ID, "contador")))
    contador = driver.find_element(By.ID, "contador")

    # Extrai a data exibida no formato "DD/MM/YYYY HH:MM:SS"
    data_hora = contador.text.split("desde")[1].strip().replace(",", "")
    logger.info("Data atual disponível no portal: %s", data_hora)

    # Navega para registros mais antigos até alcançar a fronteira do bastão
    if data_pas is not None:
        data_atu = datetime.strptime(data_hora, DATE_FMT)
        while data_atu > data_pas:
            logger.info(
                "Data portal (%s) > bastão (%s), navegando para resultados anteriores...",
                data_atu, data_pas,
            )
            wait.until(EC.element_to_be_clickable((By.ID, "btn-mais-resultados")))
            driver.find_element(By.ID, "btn-mais-resultados").click()
            wait.until(EC.visibility_of_element_located((By.ID, "contador")))
            contador = driver.find_element(By.ID, "contador")
            data_hora_l = contador.text.split("desde")[1].strip().replace(",", "")
            data_atu = datetime.strptime(data_hora_l, DATE_FMT)
            logger.info("Data após clique: %s", data_atu)

    return data_hora, _extract_records(driver, wait)


def _extract_records(driver: webdriver.Remote, wait: WebDriverWait) -> list:
    """
    Extrai os registros de reclamações da página já carregada.

    :param driver: instância ativa do WebDriver
    :param wait: instância de WebDriverWait configurada
    :return: lista de dicts com os campos de cada reclamação
    """
    resultados = driver.find_element(By.ID, "resultados")

    # Nomes das empresas
    logger.info("Extraindo nomes de empresas (class=relatos-nome-empresa).")
    nom_empresas = resultados.find_elements(By.CLASS_NAME, "relatos-nome-empresa")
    empresas = [e.find_element(By.TAG_NAME, "a").text for e in nom_empresas]

    # Status das reclamações
    logger.info("Extraindo status das reclamações (tag=h4).")
    lst_status = [s.text for s in resultados.find_elements(By.TAG_NAME, "h4")]

    # Data, cidade e UF
    logger.info("Extraindo data, cidade e UF (xpath=//div[3]/span).")
    datas, cidades, ufs = [], [], []
    for span in resultados.find_elements(By.XPATH, "//div[3]/span"):
        partes = span.text.split(",")
        datas.append(partes[0])
        local = partes[1].split("-")
        cidades.append(local[0].strip())
        ufs.append(local[1].strip())

    # Tempo de resposta
    logger.info("Extraindo tempo de resposta (xpath=//div[4]/span).")
    tempo_respostas = [
        d.text.replace("(", "").replace(")", "")
        for d in resultados.find_elements(By.XPATH, "//div[4]/span")
    ]

    # Textos: relato, resposta, nota e comentário do consumidor
    logger.info("Extraindo relatos do consumidor (xpath=//div[3]/p).")
    relatos = [r.text for r in resultados.find_elements(By.XPATH, "//div[3]/p")]

    logger.info("Extraindo respostas da empresa (xpath=//div[4]/p).")
    respostas = [r.text for r in resultados.find_elements(By.XPATH, "//div[4]/p")]

    logger.info("Extraindo notas e comentários do consumidor (xpath=//div[5]/p).")
    notas, comentarios = [], []
    for i, item in enumerate(resultados.find_elements(By.XPATH, "//div[5]/p"), start=1):
        # Itens ímpares = nota; pares = comentário
        (notas if i % 2 != 0 else comentarios).append(item.text)

    # Combina todos os campos em dicionários
    records = [
        dict(zip(CSV_FIELDS, row))
        for row in zip(
            empresas, lst_status, tempo_respostas,
            datas, cidades, ufs,
            relatos, respostas, notas, comentarios,
        )
    ]
    logger.info("%d reclamações extraídas.", len(records))
    return records


# ---------------------------------------------------------------------------
# Entrypoint AWS Lambda
# ---------------------------------------------------------------------------

def lambda_handler(event: dict, context) -> dict:
    """
    Ponto de entrada da AWS Lambda.

    Parâmetros esperados no event:
        env (str): ambiente alvo (ex: "dev", "hml", "prd").
                   Usado para compor o nome do bucket S3.

    :param event: payload do evento Lambda
    :param context: contexto de execução Lambda (não utilizado diretamente)
    :return: dict com statusCode e body descritivo
    """
    # Valida parâmetro obrigatório
    env = event.get("env")
    if not env:
        raise ValueError("O parâmetro 'env' é obrigatório no payload do evento Lambda.")

    bucket = BUCKET_TEMPLATE.format(env=env)
    logger.info("Iniciando execução | env=%s | bucket=%s", env, bucket)

    s3_client = boto3.client("s3")
    driver = None

    try:
        # ----------------------------------------------------------------
        # 1. Lê o bastão (data da última execução processada)
        # ----------------------------------------------------------------
        data_pas = get_bst_from_s3(s3_client, bucket)

        # ----------------------------------------------------------------
        # 2. Inicia o WebDriver e obtém a data atual do portal
        # ----------------------------------------------------------------
        driver = _init_driver()
        data_hora_str, records = scrape_reclamacoes(driver, data_pas)
        data_atu = datetime.strptime(data_hora_str, DATE_FMT)

        # ----------------------------------------------------------------
        # 3. Verifica se há dados novos em relação ao bastão
        # ----------------------------------------------------------------
        if data_pas is None:
            # Primeira execução: registra bastão e processa normalmente
            logger.info("Primeira execução detectada. Registrando bastão inicial.")
            save_bst_to_s3(s3_client, bucket, data_hora_str)
            data_pas = data_atu

        if data_atu <= data_pas:
            msg = "Não há atualizações desde a última execução."
            logger.info(msg)
            return {"statusCode": 200, "body": msg}

        logger.info(
            "Novas atualizações detectadas | última=%s | atual=%s",
            data_pas, data_atu,
        )

        # ----------------------------------------------------------------
        # 4. Grava os dados como CSV no S3
        # ----------------------------------------------------------------
        csv_key = save_csv_to_s3(s3_client, bucket, records)

        # ----------------------------------------------------------------
        # 5. Atualiza o bastão com a data atual
        # ----------------------------------------------------------------
        save_bst_to_s3(s3_client, bucket, data_hora_str)

        msg = f"Execução concluída. CSV gravado em s3://{bucket}/{csv_key}."
        logger.info(msg)
        return {"statusCode": 200, "body": msg}

    except Exception as e:
        # logger.exception inclui o stack trace completo no CloudWatch
        logger.exception("Erro durante a execução do scraping: %s", e)
        return {"statusCode": 500, "body": str(e)}

    finally:
        # Garante que o WebDriver seja encerrado mesmo em caso de falha
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver encerrado.")
            except Exception:
                logger.warning("Falha ao encerrar o WebDriver.", exc_info=True)
