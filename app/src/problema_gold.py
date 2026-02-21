import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-grupo-problema")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class GrupoProblema:

    @staticmethod
    def run(log, datRefCarga):        

        try:
            log.info(f"Iniciando job GrupoProblema — datRefCarga: {datRefCarga}")

            consumidor = spark.table('s_consumidor.consumidorservicosfinanceiros').filter(col('datRefCarga') == datRefCarga)

            log.info("Agrupando dados por nomefantasia e grupoProblema")
            consumidor = (
                consumidor.groupBy(col("nomefantasia"), col("grupoProblema"), col("datRefCarga"))
                .agg(count(col("nomefantasia")).alias("qtdReclamcoes"))
                .select("nomefantasia", "grupoProblema", "datRefCarga", "qtdReclamcoes")
            )

            spark.sql(f"DELETE FROM g_consumidor.grupoProblema WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("g_consumidor.grupoProblema")
            log.info("GrupoProblema — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job GrupoProblema: {e}", exc_info=True)
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
        GrupoProblema.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job GrupoProblema encerrado com falha: {e}", exc_info=True)
        raise
