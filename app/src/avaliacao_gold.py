import logging
from pyspark.sql.functions import col, count, round, sum

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-media-avaliacao")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class MediaAvaliacao:

    @staticmethod
    def run(log, datRefCarga):

        try:
            log.info(f"Iniciando job MediaAvaliacao — datRefCarga: {datRefCarga}")

            consumidor = spark.table('s_consumidor.consumidorservicosfinanceiros').filter(col('datRefCarga') == datRefCarga)

            log.info("Filtrando consumidores com nota e calculando média por nomefantasia")
            consumidor = (
                consumidor.filter(~col('notaconsumidor').isNull())
                .groupBy(col('nomefantasia'), col('datRefCarga'))
                .agg(round(sum(col('notaconsumidor')) / count(col('nomefantasia')), 2).alias('mediaAvaliacao'))
                .select('nomefantasia', 'mediaAvaliacao', 'datRefCarga')
            )

            spark.sql(f"DELETE FROM g_consumidor.mediaavaliacao WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("g_consumidor.mediaavaliacao")
            log.info("MediaAvaliacao — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job MediaAvaliacao: {e}", exc_info=True)
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
        MediaAvaliacao.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job MediaAvaliacao encerrado com falha: {e}", exc_info=True)
        raise
