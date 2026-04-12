import logging
from pyspark.sql.functions import col, count, lit

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-ai-status")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class StatusAiClassificacao:

    @staticmethod
    def run(log, datRefCarga):        

        try:
            log.info(f"Iniciando job StatusAiClassificacao — datRefCarga: {datRefCarga}")

            classificacao = spark.table('s_consumidor.ai_classificacao_relatos').filter(col('datrefcarga') == datRefCarga)

            log.info("Agrupando dados por status e dataocorrido")
            classificacao = (
                classificacao.groupBy(col("status"), col("dataocorrido"))
                .agg(count("*").alias("qtd"))
                .withColumn("datrefcarga", lit(datRefCarga))
                .select("status", "dataocorrido", "datrefcarga", "qtd")
            )

            spark.sql(f"DELETE FROM g_consumidor.ai_status WHERE datrefcarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            classificacao.write.mode("append").insertInto("g_consumidor.ai_status")
            log.info("StatusAiClassificacao — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job StatusAiClassificacao: {e}", exc_info=True)
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
        StatusAiClassificacao.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job StatusAiClassificacao encerrado com falha: {e}", exc_info=True)
        raise
