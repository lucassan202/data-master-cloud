"""
AWS Lambda Function para download de CSV do site dados.mj.gov.br
e armazenamento no bucket S3

Handler: lambda_handler(event, context)
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import time
import zipfile
from urllib.parse import quote

import boto3
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

logger = logging.getLogger()
log_level = os.getenv("LAMBDA_LOG_LEVEL", "INFO")
logger.setLevel(logging.getLevelName(log_level))

# Cliente S3
s3_client = boto3.client('s3')

CKAN_URL = "https://dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br"
CONSUMIDOR_PAGE_URL = "https://consumidor.gov.br/pages/dadosabertos/externo/"
CONSUMIDOR_PUBLICATIONS_PATH = (
    "/pages/publicacao/externo/publicacoes.json"
)
CONSUMIDOR_DOWNLOAD_URL = (
    "https://consumidor.gov.br/pages/publicacao/externo/{codigo}/download"
)
REQUEST_TIMEOUT = (10, 60)
REQUEST_RETRIES = 3
MONTH_NAMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def _get_with_retries(session, url: str, **kwargs):
    """Executa GET com poucas tentativas e backoff para falhas transitórias."""
    last_error = None
    for attempt in range(REQUEST_RETRIES):
        try:
            response = session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as error:
            last_error = error
            if attempt + 1 < REQUEST_RETRIES:
                delay = 2 ** attempt
                logger.warning(
                    "GET falhou (%d/%d) para %s; tentando novamente em %ds",
                    attempt + 1, REQUEST_RETRIES, url, delay,
                )
                time.sleep(delay)
    raise last_error


def upload_csv(content: bytes, destination_path: str, bucket_name: str) -> None:
    """Envia o conteúdo CSV para o S3."""
    logger.info("Enviando para S3: s3://%s/%s", bucket_name, destination_path)
    s3_client.put_object(
        Bucket=bucket_name,
        Key=destination_path,
        Body=content,
        ContentType='text/csv',
    )
    logger.info("Arquivo salvo com sucesso: s3://%s/%s", bucket_name, destination_path)


def download_csv(url: str, destination_path: str, bucket_name: str) -> bool:
    """
    Faz o download do arquivo CSV e salva no S3
    
    Args:
        url: URL do arquivo para download
        destination_path: Path/key no S3
        bucket_name: Nome do bucket S3
    
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        logger.info(f"Baixando arquivo de: {url}")
        
        response = _get_with_retries(requests, url, timeout=REQUEST_TIMEOUT)
        upload_csv(response.content, destination_path, bucket_name)
        return True
        
    except requests.exceptions.RequestException as e:
        logger.exception(f"Erro ao baixar arquivo: {url}")
        return False
    except ClientError as e:
        logger.exception(f"Erro ao salvar no S3: s3://{bucket_name}/{destination_path}")
        return False


def find_csv_links(dat_ref_carga: str) -> list:
    """
    Faz scraping do site dados.mj.gov.br para encontrar links de CSV
    
    Args:
        dat_ref_carga: Data de referência para filtrar os arquivos
    
    Returns:
        Lista de URLs encontradas
    """
    try:
        response = _get_with_retries(requests, CKAN_URL, timeout=REQUEST_TIMEOUT)
        bs = BeautifulSoup(response.content, 'html.parser')
        
        linhas = bs.find_all('a', {'class': 'resource-url-analytics'})
        
        links = []
        for link in linhas:
            href = link.get('href')
            if href:
                links.append(href)
        
        logger.info(f"Total de links encontrados: {len(links)}")
        
        # Filtra pela data de referência
        filtered_links = [url for url in links if dat_ref_carga in url]
        logger.info(f"Links filtrados pela data {dat_ref_carga}: {len(filtered_links)}")
        
        return filtered_links
        
    except Exception as e:
        logger.exception("Erro ao buscar links para download")
        # A exceção precisa chegar ao runtime da Lambda para que o
        # LambdaInvokeFunctionOperator marque a task do Airflow como falha.
        raise RuntimeError("Não foi possível buscar os links para download") from e


def monthly_title(dat_ref_carga: str) -> str:
    """Converte YYYY-MM no título usado pelo portal de dados abertos."""
    match = re.fullmatch(r"(\d{4})-(0[1-9]|1[0-2])", dat_ref_carga)
    if not match:
        raise ValueError("datRefCarga deve estar no formato YYYY-MM")
    year, month = match.groups()
    return f"Dados - {MONTH_NAMES[int(month)]}/{year}"


def find_monthly_publication(dat_ref_carga: str, session=None) -> dict:
    """Busca no portal alternativo a publicação mensal do período informado."""
    session = session or requests.Session()
    _get_with_retries(session, CONSUMIDOR_PAGE_URL, timeout=REQUEST_TIMEOUT)

    # O portal usa acoesSessaoCookie como parâmetro de matriz na URL do JSON.
    # A sessão também é mantida para enviar os demais cookies de balanceamento.
    session_cookie = session.cookies.get("acoesSessaoCookie")
    endpoint = f"{CONSUMIDOR_PUBLICATIONS_PATH}?indicadorTipoPublicacao=2"
    if session_cookie:
        endpoint = (
            f"{CONSUMIDOR_PUBLICATIONS_PATH};acoesSessaoCookie="
            f"{quote(session_cookie, safe='')}?indicadorTipoPublicacao=2"
        )
    endpoint = f"https://consumidor.gov.br{endpoint}"
    response = _get_with_retries(session, endpoint, timeout=REQUEST_TIMEOUT)
    try:
        publications = response.json()
    except (ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("Resposta inválida do catálogo do consumidor.gov.br") from error

    title = monthly_title(dat_ref_carga)
    matches = [
        item for item in publications
        if item.get("titulo") == title
        and item.get("codigo")
        and str(item.get("nomeArquivo", "")).lower().endswith(".zip")
    ]
    if not matches:
        raise FileNotFoundError(
            f"Nenhuma publicação mensal encontrada para {dat_ref_carga}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Mais de uma publicação mensal encontrada para {dat_ref_carga}"
        )
    publication = matches[0]
    logger.info(
        "Publicação mensal encontrada: título=%s, código=%s, arquivo=%s",
        publication["titulo"], publication["codigo"], publication["nomeArquivo"],
    )
    return publication


def extract_csv_from_zip(content: bytes, expected_period: str) -> tuple[str, bytes]:
    """Extrai o único CSV do ZIP e rejeita entradas com path traversal."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as error:
        raise ValueError("O download do portal não é um ZIP válido") from error

    with archive:
        members = archive.infolist()
        for member in members:
            normalized_name = member.filename.replace("\\", "/")
            if member.filename.startswith(("/", "\\")) or ".." in normalized_name.split("/"):
                raise ValueError(f"Entrada insegura no ZIP: {member.filename}")
        csv_members = [
            member for member in members
            if not member.is_dir() and member.filename.lower().endswith(".csv")
        ]
        if len(csv_members) != 1:
            raise ValueError(
                f"Esperado exatamente um CSV no ZIP de {expected_period}; "
                f"encontrados {len(csv_members)}"
            )
        member = csv_members[0]
        logger.info("CSV extraído do ZIP: %s (%d bytes)", member.filename, member.file_size)
        return os.path.basename(member.filename), archive.read(member)


def download_monthly_fallback(
    dat_ref_carga: str, destination_path: str, bucket_name: str
) -> None:
    """Baixa, descompacta e envia o arquivo mensal do portal alternativo."""
    session = requests.Session()
    publication = find_monthly_publication(dat_ref_carga, session)
    url = CONSUMIDOR_DOWNLOAD_URL.format(codigo=publication["codigo"])
    response = _get_with_retries(session, url, timeout=REQUEST_TIMEOUT)
    filename, csv_content = extract_csv_from_zip(response.content, dat_ref_carga)
    logger.info("Fallback consumidor.gov.br: %s (%d bytes)", filename, len(csv_content))
    upload_csv(csv_content, destination_path, bucket_name)


def lambda_handler(event, context):
    """
    Handler principal da AWS Lambda
    
    Args:
        event: Evento contendo parâmetros (datRefCarga, env)
        context: Contexto da Lambda
    
    Returns:
        Dict com status e mensagem
    """
    # Obtém parâmetros do evento ou environment
    # Priority: event > environment variables > default
    
    env = event.get('env', os.environ.get('ENV', 'dev'))
    dat_ref_carga = event.get('datRefCarga', os.environ.get('DAT_REF_CARGA'))
    
    logger.info(f"Iniciando Lambda - Ambiente: {env}, DataRefCarga: {dat_ref_carga}")
    
    # Valida parâmetros obrigatórios
    if not dat_ref_carga:
        logger.error("Parâmetro 'datRefCarga' não fornecido")
        raise ValueError('Parâmetro "datRefCarga" é obrigatório')
    
    # Define bucket name
    bucket_name = f"{env}-us-east-2-data-master"
    
    s3_key = f"tmp/basecompleta{dat_ref_carga}.csv"
    try:
        links = find_csv_links(dat_ref_carga)
        if not links:
            raise FileNotFoundError(
                f"Nenhum arquivo encontrado no CKAN para a data {dat_ref_carga}"
            )
        if len(links) > 1:
            raise RuntimeError(
                f"Mais de um arquivo encontrado no CKAN para {dat_ref_carga}"
            )
        if not download_csv(links[0], s3_key, bucket_name):
            raise RuntimeError("Falha ao baixar o arquivo do CKAN")
        source = "CKAN"
    except Exception as ckan_error:
        logger.warning("CKAN indisponível ou sem arquivo: %s", ckan_error)
        download_monthly_fallback(dat_ref_carga, s3_key, bucket_name)
        source = "consumidor.gov.br"

    logger.info("Download concluído com sucesso usando %s", source)

    return {
        'statusCode': 200,
        'body': f"Download concluído com sucesso via {source}: {s3_key}"
    }
