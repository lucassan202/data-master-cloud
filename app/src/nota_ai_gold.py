import logging
from pyspark.sql.functions import col, count, lit, upper, regexp_replace

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-ai-nota")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class NotaAiClassificacao:

    @staticmethod
    def run(log, datRefCarga):        

        try:
            log.info(f"Iniciando job NotaAiClassificacao — datRefCarga: {datRefCarga}")

            classificacao = spark.table('s_consumidor.ai_classificacao_relatos').filter(col('datrefcarga') == datRefCarga)

            log.info("Aplicando upper e replace no campo nota e agrupando por nota e dataocorrido")
            classificacao = (
                classificacao.withColumn("nota", regexp_replace(upper(col("nota")), r"[^0-9]", ""))
                .groupBy(col("nota"), col("dataocorrido"))
                .agg(count("*").alias("qtd"))
                .withColumn("datrefcarga", lit(datRefCarga))
                .select("nota", "dataocorrido", "datrefcarga", "qtd")
            )

            spark.sql(f"DELETE FROM g_consumidor.ai_nota WHERE datrefcarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            classificacao.write.mode("append").insertInto("g_consumidor.ai_nota")
            log.info("NotaAiClassificacao — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job NotaAiClassificacao: {e}", exc_info=True)
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
        NotaAiClassificacao.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job NotaAiClassificacao encerrado com falha: {e}", exc_info=True)
        raise
