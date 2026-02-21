import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, concat, lit

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-reclamacao-uf")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class UfProblema:

    @staticmethod
    def run(log, datRefCarga):        

        try:
            log.info(f"Iniciando job UfProblema — datRefCarga: {datRefCarga}")

            consumidor = spark.table('s_consumidor.consumidorservicosfinanceiros').filter(col('datRefCarga') == datRefCarga)

            log.info("Agrupando reclamações por nomefantasia e UF")
            consumidor = (
                consumidor.groupBy(
                    col("nomefantasia"),
                    concat(lit("Brasil - "), col("uf")).alias("uf"),
                    col("datRefCarga"),
                )
                .agg(count(col("nomefantasia")).alias("qtdReclamcoesUf"))
                .select("nomefantasia", "uf", "datRefCarga", "qtdReclamcoesUf")
            )
            
            spark.sql(f"DELETE FROM g_consumidor.reclamacaouf WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("g_consumidor.reclamacaouf")
            log.info("UfProblema — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job UfProblema: {e}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Entry point — Databricks Job / Notebook
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Parâmetros recebidos via Databricks Widgets
    dbutils.widgets.text("datRefCarga", "")  # noqa: F821
    datRefCarga = dbutils.widgets.get("datRefCarga")  # noqa: F821

    if not datRefCarga:
        raise ValueError("O parâmetro 'datRefCarga' é obrigatório e não foi informado.")    

    log.info(f"Parâmetros recebidos — datRefCarga: {datRefCarga}")

    try:
        UfProblema.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job UfProblema encerrado com falha: {e}", exc_info=True)
        raise
