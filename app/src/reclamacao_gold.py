import logging
from pyspark.sql.functions import col, count

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("gold-reclamacao-top-ten")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class ReclamacaoTopTen:

    @staticmethod
    def run(log, datRefCarga):        
        try:
            log.info(f"Iniciando job ReclamacaoTopTen — datRefCarga: {datRefCarga}")

            consumidor = spark.table('s_consumidor.consumidorservicosfinanceiros').filter(col('datRefCarga') == datRefCarga)

            log.info("Agrupando e ordenando top 10 reclamações por nomefantasia")
            consumidor = (
                consumidor.groupBy(col("nomefantasia"), col("datRefCarga"))
                .agg(count(col("nomefantasia")).alias("qtdReclamcoes"))
                .orderBy(col("qtdReclamcoes"), ascending=False)
                .select("nomefantasia", "datRefCarga", "qtdReclamcoes")
                .limit(10)
            )

            spark.sql(f"DELETE FROM g_consumidor.reclamacaotopten WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("g_consumidor.reclamacaotopten")
            log.info("ReclamacaoTopTen — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job ReclamacaoTopTen: {e}", exc_info=True)
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
        ReclamacaoTopTen.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job ReclamacaoTopTen encerrado com falha: {e}", exc_info=True)
        raise
