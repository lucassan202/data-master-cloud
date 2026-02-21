import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, round, sum

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-media-resposta")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class MediaResposta:

    @staticmethod
    def run(log, datRefCarga):        
        try:
            log.info(f"Iniciando job MediaResposta — datRefCarga: {datRefCarga}")

            consumidor = spark.table('s_consumidor.consumidorservicosfinanceiros').filter(col('datRefCarga') == datRefCarga)

            log.info("Calculando média de dias de resposta por nomefantasia (apenas respondidas)")
            consumidor = (
                consumidor.filter(col("respondida") == True)
                .groupBy(col("nomefantasia"), col("datRefCarga"))
                .agg(
                    round(
                        sum(col("temporesposta")) / count(col("nomefantasia")), 0
                    ).alias("mediaRespostaDias")
                )
                .select("nomefantasia", "datRefCarga", "mediaRespostaDias")
            )

            spark.sql(f"DELETE FROM g_consumidor.mediaresposta WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("g_consumidor.mediaresposta")
            log.info("MediaResposta — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job MediaResposta: {e}", exc_info=True)
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
        MediaResposta.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job MediaResposta encerrado com falha: {e}", exc_info=True)
        raise
