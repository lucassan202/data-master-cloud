"""
AWS Lambda Function para download de CSV do site governamental
e armazenamento no bucket S3

Handler: lambda_handler(event, context)
"""

import os
import logging
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("LambdaDownloadCsv")

# Cliente S3
s3_client = boto3.client('s3')


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
        
        response = requests.get(url)
        response.raise_for_status()
        
        # Upload para S3
        logger.info(f"Enviando para S3: s3://{bucket_name}/{destination_path}")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=destination_path,
            Body=response.content,
            ContentType='text/csv'
        )
        
        logger.info(f"Arquivo salvo com sucesso: s3://{bucket_name}/{destination_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao baixar arquivo: {str(e)}")
        return False
    except ClientError as e:
        logger.error(f"Erro ao salvar no S3: {str(e)}")
        return False


def find_csv_links(dat_ref_carga: str) -> list:
    """
    Faz scraping do site governamental para encontrar links de CSV
    
    Args:
        dat_ref_carga: Data de referência para filtrar os arquivos
    
    Returns:
        Lista de URLs encontradas
    """
    try:
        html = urlopen("https://dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br")
        bs = BeautifulSoup(html, 'html.parser')
        
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
        logger.error(f"Erro ao buscar links: {str(e)}")
        return []


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
        return {
            'statusCode': 400,
            'body': 'Parâmetro "datRefCarga" é obrigatório'
        }
    
    # Define bucket name
    bucket_name = f"{env}-us-east-2-data-master"
    
    # Busca links CSV
    links = find_csv_links(dat_ref_carga)
    
    if not links:
        logger.warning(f"Nenhum arquivo encontrado para a data {dat_ref_carga}")
        return {
            'statusCode': 200,
            'body': f"Nenhum arquivo encontrado para a data {dat_ref_carga}"
        }
    
    # Download e upload de cada arquivo
    success_count = 0
    error_count = 0
    
    for url in links:
        # Converte https para http
        url = url.replace('https', 'http')
        
        # Extrai nome do arquivo da URL
        filename = url[url.rfind("/") + 1:]
        if filename.endswith('csv'):
            filename = filename + 'v'  # Adiciona extensão se necessário
            
        # Define path no S3
        s3_key = f"download/{dat_ref_carga}/{filename}"
        
        # Executa download e upload
        if download_csv(url, s3_key, bucket_name):
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"Download concluído - Sucesso: {success_count}, Erros: {error_count}")
    
    return {
        'statusCode': 200 if error_count == 0 else 500,
        'body': f"Download concluído - Sucesso: {success_count}, Erros: {error_count}"
    }


if __name__ == "__main__":
    # Teste local
    test_event = {
        'env': 'dev',
        'datRefCarga': '2026-01'
    }
    
    # Executar localmente (precisa de credenciais AWS)
    # result = lambda_handler(test_event, None)
    # print(result)
    print("Lambda function ready. Execute via AWS Lambda with test event.")
