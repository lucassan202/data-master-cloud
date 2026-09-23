import logging
from datetime import datetime

from delta.tables import DeltaTable
from pyspark.sql.functions import col, coalesce, count, date_format, lit, to_date

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
    def _write_historical(classificacao, output_table, dat_ref_carga):
        """Atualiza o lote histórico sem duplicar resultados em reprocessamentos."""
        target = DeltaTable.forName(spark, output_table)  # noqa: F821

        # Limpa resultados gerados pela implementação anterior, que usava
        # YYYY-MM como datrefcarga para o mesmo lote histórico.
        target.delete(f"datrefcarga = '{dat_ref_carga}'")

        target.alias("target").merge(
            classificacao.alias("source"),
            "target.status <=> source.status "
            "AND target.dataocorrido <=> source.dataocorrido",
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

    @staticmethod
    def run(log, datRefCarga, modo="diario"):

        if modo not in {"diario", "historico"}:
            raise ValueError("modo deve ser 'diario' ou 'historico'.")
        input_table = (
            "s_consumidor.ai_classificacao_relatos_historico"
            if modo == "historico"
            else "s_consumidor.ai_classificacao_relatos"
        )
        output_table = (
            "g_consumidor.ai_status"
        )

        try:
            log.info(f"Iniciando job StatusAiClassificacao — datRefCarga: {datRefCarga}")

            classificacao = spark.table(input_table).filter(col('datrefcarga') == datRefCarga)

            log.info("Agrupando dados por status e dataocorrido")
            dataocorrido = col("dataocorrido")
            if modo == "historico":
                dataocorrido = date_format(
                    coalesce(
                        to_date(dataocorrido, "yyyy-MM-dd"),
                        to_date(dataocorrido, "dd/MM/yyyy"),
                    ),
                    "dd/MM/yyyy",
                )

            output_datrefcarga = (
                datetime.now().strftime("%Y%m%d")
                if modo == "historico"
                else datRefCarga
            )
            classificacao = (
                classificacao.groupBy(col("status"), dataocorrido.alias("dataocorrido"))
                .agg(count("*").alias("qtd"))
                .withColumn("datrefcarga", lit(output_datrefcarga))
                .select("status", "dataocorrido", "datrefcarga", "qtd")
            )

            if classificacao.limit(1).count() == 0 and modo == "diario":
                raise ValueError(
                    f"Nenhum dado encontrado para datRefCarga: {datRefCarga}"
                )

            if classificacao.limit(1).count() == 0:
                log.info("Nenhum dado histórico para %s.", datRefCarga)
                return

            if modo == "historico":
                StatusAiClassificacao._write_historical(
                    classificacao, output_table, datRefCarga
                )
            else:
                classificacao.write.mode("overwrite").option(
                    "replaceWhere", f"datrefcarga = '{datRefCarga}'"
                ).saveAsTable(output_table)
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
    dbutils.widgets.text("modo", "diario")  # noqa: F821
    datRefCarga = dbutils.widgets.get("datRefCarga")  # noqa: F821
    modo = dbutils.widgets.get("modo")  # noqa: F821

    if not datRefCarga:
        raise ValueError("O parâmetro 'datRefCarga' é obrigatório e não foi informado.")    

    log.info(f"Parâmetros recebidos — datRefCarga: {datRefCarga}")

    try:
        StatusAiClassificacao.run(log, datRefCarga, modo)
    except Exception as e:
        log.error(f"Job StatusAiClassificacao encerrado com falha: {e}", exc_info=True)
        raise
