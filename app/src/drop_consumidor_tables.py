# pylint: disable=no-member
"""
Script para drop das tabelas e databases do Consumer (Bronze, Silver, Gold)
Executa via spark.sql os DDLs de drop
"""

import logging

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("DropConsumerTables")

# Obter parâmetro de ambiente
dbutils.widgets.text("env", "")  # noqa: F821
env = dbutils.widgets.get("env")

logger.info(f"Iniciando drop das tabelas - Ambiente: {env}")


def drop_tables_in_database(database_name: str, table_names: list) -> bool:
    """
    Drop todas as tabelas de um database específico
    """
    try:
        # Seleciona o database
        spark.sql(f"USE {database_name}")
        logger.info(f"Database {database_name} selecionado")
        
        for table_name in table_names:
            try:
                # Tenta fazer drop da tabela (IF EXISTS para não falhar se não existir)
                spark.sql(f"DROP TABLE IF EXISTS {database_name}.{table_name}")
                logger.info(f"Tabela {database_name}.{table_name} removida com sucesso")
            except Exception as e:
                logger.warn(f"Erro ao dropar tabela {database_name}.{table_name}: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao processar database {database_name}: {str(e)}")
        return False


def drop_database(database_name: str) -> bool:
    """
    Drop o database se existir
    """
    try:
        spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
        logger.info(f"Database {database_name} removido com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao dropar database {database_name}: {str(e)}")
        return False


def drop_bronze_tables() -> bool:
    """
    Drop tabelas e database Bronze - b_consumidor
    """
    try:
        logger.info("Iniciando drop das tabelas Bronze")
        
        # Tabelas do database Bronze
        tables = ["consumidor", "consumidor_dia"]
        
        if not drop_tables_in_database("b_consumidor", tables):
            return False
        
        # Drop do database
        if not drop_database("b_consumidor"):
            return False
        
        logger.info("Drop Bronze concluído com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao dropar tabelas Bronze: {str(e)}")
        return False


def drop_silver_tables() -> bool:
    """
    Drop tabelas e database Silver - s_consumidor
    """
    try:
        logger.info("Iniciando drop das tabelas Silver")
        
        # Tabelas do database Silver
        tables = ["consumidorservicosfinanceiros"]
        
        if not drop_tables_in_database("s_consumidor", tables):
            return False
        
        # Drop do database
        if not drop_database("s_consumidor"):
            return False
        
        logger.info("Drop Silver concluído com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao dropar tabelas Silver: {str(e)}")
        return False


def drop_gold_tables() -> bool:
    """
    Drop tabelas e database Gold - g_consumidor
    """
    try:
        logger.info("Iniciando drop das tabelas Gold")
        
        # Tabelas do database Gold (5 tabelas)
        tables = [
            "grupoProblema",
            "mediaavaliacao",
            "mediaresposta",
            "reclamacaotopten",
            "reclamacaouf"
        ]
        
        if not drop_tables_in_database("g_consumidor", tables):
            return False
        
        # Drop do database
        if not drop_database("g_consumidor"):
            return False
        
        logger.info("Drop Gold concluído com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao dropar tabelas Gold: {str(e)}")
        return False


def main():
    """
    Função principal que executa o drop de todas as tabelas
    """
    logger.info("=" * 60)
    logger.info(f"Início da execução - Ambiente: {env}")
    logger.info("=" * 60)
    
    results = {
        "Bronze": False,
        "Silver": False,
        "Gold": False
    }
    
    # Executa drop das tabelas Gold primeiro (dependência)
    logger.info("--- Fase 1: Drop das tabelas Gold ---")
    results["Gold"] = drop_gold_tables()
    
    # Executa drop das tabelas Silver
    logger.info("--- Fase 2: Drop das tabelas Silver ---")
    results["Silver"] = drop_silver_tables()
    
    # Executa drop das tabelas Bronze
    logger.info("--- Fase 3: Drop das tabelas Bronze ---")
    results["Bronze"] = drop_bronze_tables()
    
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
        raise Exception("Falha no drop de uma ou mais camadas de tabelas")


if __name__ == "__main__":
    main()
