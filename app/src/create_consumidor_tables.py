# pylint: disable=no-member
"""
Script para criação das tabelas Consumer (Bronze, Silver, Gold)
Executa via spark.sql os DDLs dos scripts SQL convertidos
"""

import logging

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("CreateConsumerTables")

# Obter parâmetro de ambiente
dbutils.widgets.text("env", "")  # noqa: F821
env = dbutils.widgets.get("env")

logger.info(f"Iniciando criação das tabelas - Ambiente: {env}")

# Função para determinar o location basedo no ambiente
def get_location(path_complementar: str) -> str:
    """
    Retorna o location S3 baseado no ambiente
    """
    if env == 'dev':
        return f"s3://besga/{path_complementar}"
    else:
        return f"s3://{env}-us-east-2-data-master/{path_complementar}"


def create_database(database_name: str) -> bool:
    """
    Cria o database se não existir
    """
    try:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        logger.info(f"Database {database_name} verificada/criada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar database {database_name}: {str(e)}")
        return False


def create_bronze_tables() -> bool:
    """
    Cria tabelas Bronze - b_consumidor.consumidor
    """
    try:
        logger.info("Iniciando criação das tabelas Bronze")
        
        # Cria database
        if not create_database("b_consumidor"):
            return False
        
        location = get_location("data/b_consumidor/consumidor")
        
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS b_consumidor.consumidor(
          gestor string, 
          canalorigem string, 
          regiao string, 
          uf string, 
          cidade string, 
          sexo string, 
          faixaetaria string, 
          anoabertura string, 
          mesabertura string, 
          dataabertura string, 
          dataresposta string, 
          dataanalise string, 
          datarecusa string, 
          datafinalizacao string, 
          prazoresposta string, 
          prazoanalisegestor string, 
          temporesposta string, 
          nomefantasia string, 
          segmentomercado string, 
          area string, 
          assunto string, 
          grupoproblema string, 
          problema string, 
          comocontratou string, 
          procurouempresa string, 
          respondida string, 
          situacao string, 
          avaliacaoreclamacao string, 
          notaconsumidor string, 
          analiserecusa string,
          datrefcarga string)
        LOCATION
          '{location}'
        """
        
        spark.sql(ddl)
        logger.info(f"Tabela b_consumidor.consumidor criada com sucesso - Location: {location}")
        
        # Grant (opcional - pode falhar em alguns ambientes)
        try:
            spark.sql("GRANT SELECT ON TABLE b_consumidor.consumidor TO `lucas_san20@hotmail.com`")
            logger.info("Grant aplicado na tabela bronze.consumidor")
        except Exception as e:
            logger.warn(f"Grant não aplicado (pode não ser necessário neste ambiente): {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas Bronze: {str(e)}")
        return False


def create_silver_tables() -> bool:
    """
    Cria tabelas Silver - s_consumidor.consumidorservicosfinanceiros
    """
    try:
        logger.info("Iniciando criação das tabelas Silver")
        
        # Cria database
        if not create_database("s_consumidor"):
            return False
        
        location = get_location("data/s_consumidor/consumidorservicosfinanceiros")
        
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS s_consumidor.consumidorservicosfinanceiros(
          gestor string, 
          canalorigem string, 
          regiao string, 
          uf string, 
          cidade string, 
          sexo string, 
          faixaetaria string, 
          anoabertura int, 
          mesabertura int, 
          dataabertura date, 
          dataresposta date, 
          dataanalise date, 
          datarecusa date, 
          datafinalizacao date, 
          prazoresposta date, 
          prazoanalisegestor int, 
          temporesposta int, 
          nomefantasia string, 
          segmentomercado string, 
          area string, 
          assunto string, 
          grupoproblema string, 
          problema string, 
          comocontratou string, 
          procurouempresa boolean, 
          respondida boolean, 
          situacao string, 
          avaliacaoreclamacao string, 
          notaconsumidor int, 
          analiserecusa string,
          datrefcarga string)
        LOCATION
          '{location}'
        """
        
        spark.sql(ddl)
        logger.info(f"Tabela s_consumidor.consumidorservicosfinanceiros criada com sucesso - Location: {location}")
        
        # Grant (opcional)
        try:
            spark.sql("GRANT SELECT ON TABLE s_consumidor.consumidorservicosfinanceiros TO `lucas_san20@hotmail.com`")
            logger.info("Grant aplicado na tabela silver.consumidorservicosfinanceiros")
        except Exception as e:
            logger.warn(f"Grant não aplicado (pode não ser necessário neste ambiente): {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas Silver: {str(e)}")
        return False


def create_gold_tables() -> bool:
    """
    Cria tabelas Gold - g_consumidor (5 tabelas)
    """
    try:
        logger.info("Iniciando criação das tabelas Gold")
        
        # Cria database
        if not create_database("g_consumidor"):
            return False
        
        tables = [
            ("grupoProblema", "data/g_consumidor/grupoproblema"),
            ("mediaavaliacao", "data/g_consumidor/mediaavaliacao"),
            ("mediaresposta", "data/g_consumidor/mediaresposta"),
            ("reclamacaotopten", "data/g_consumidor/reclamacaotopten"),
            ("reclamacaouf", "data/g_consumidor/reclamacaouf"),
        ]
        
        # Definições das colunas para cada tabela Gold
        columns_def = {
            "grupoProblema": "nomefantasia string, grupoproblema string, datrefcarga string, qtdreclamcoes bigint",
            "mediaavaliacao": "nomefantasia string, datrefcarga string, mediaAvaliacao double",
            "mediaresposta": "nomefantasia string, datrefcarga string, mediaRespostaDias double",
            "reclamacaotopten": "nomefantasia string, datrefcarga string, qtdreclamcoes bigint",
            "reclamacaouf": "nomefantasia string, uf string, datrefcarga string, qtdReclamcoesUf bigint",
        }
        
        for table_name, path_complementar in tables:
            try:
                location = get_location(path_complementar)
                columns = columns_def[table_name]
                
                ddl = f"""
                CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.{table_name}(
                  {columns})
                LOCATION
                  '{location}'
                """
                
                spark.sql(ddl)
                logger.info(f"Tabela g_consumidor.{table_name} criada com sucesso - Location: {location}")
                
                # Grant (opcional)
                try:
                    spark.sql(f"GRANT SELECT ON TABLE g_consumidor.{table_name} TO `lucas_san20@hotmail.com`")
                    logger.info(f"Grant aplicado na tabela gold.{table_name}")
                except Exception as e:
                    logger.warn(f"Grant não aplicado: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Erro ao criar tabela g_consumidor.{table_name}: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas Gold: {str(e)}")
        return False


def main():
    """
    Função principal que executa a criação de todas as tabelas
    """
    logger.info("=" * 60)
    logger.info(f"Início da execução - Ambiente: {env}")
    logger.info("=" * 60)
    
    results = {
        "Bronze": False,
        "Silver": False,
        "Gold": False
    }
    
    # Executa criação das tabelas Bronze
    logger.info("--- Fase 1: Criando tabelas Bronze ---")
    results["Bronze"] = create_bronze_tables()
    
    # Executa criação das tabelas Silver
    logger.info("--- Fase 2: Criando tabelas Silver ---")
    results["Silver"] = create_silver_tables()
    
    # Executa criação das tabelas Gold
    logger.info("--- Fase 3: Criando tabelas Gold ---")
    results["Gold"] = create_gold_tables()
    
    # Resumo final
    logger.info("=" * 60)
    logger.info("RESUMO DA EXECUÇÃO:")
    logger.info(f"  Bronze: {'SUCESSO' if results['Bronze'] else 'FALHA'}")
    logger.info(f"  Silver: {'SUCESSO' if results['Silver'] else 'FALHA'}")
    logger.info(f"  Gold:   {'SUCESSO' if results['Gold'] else 'FALHA'}")
    logger.info("=" * 60)
    
    if all(results.values()):
        logger.info("EXECUTION_COMPLETED_SUCCESSFULLY")
    else:
        logger.error("EXECUTION_COMPLETED_WITH_ERRORS")
        raise Exception("Falha na criação de uma ou mais camadas de tabelas")


if __name__ == "__main__":
    main()