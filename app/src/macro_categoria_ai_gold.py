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
log = logging.getLogger("gold-ai-macro-categoria")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class MacroCategoriaAiClassificacao:

    @staticmethod
    def _write_historical(classificacao, output_table, dat_ref_carga):
        """Atualiza o lote histórico sem duplicar resultados em reprocessamentos."""
        target = DeltaTable.forName(spark, output_table)  # noqa: F821
        target.delete(f"datrefcarga = '{dat_ref_carga}'")

        target.alias("target").merge(
            classificacao.alias("source"),
            "target.macro_categoria <=> source.macro_categoria "
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
            "g_consumidor.ai_macro_categoria"
        )

        try:
            log.info(f"Iniciando job MacroCategoriaAiClassificacao — datRefCarga: {datRefCarga}")

            classificacao = spark.table(input_table).filter(col('datrefcarga') == datRefCarga)

            log.info("Agrupando dados por macro_categoria e dataocorrido")
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
                classificacao.groupBy(
                    col("macro_categoria"), dataocorrido.alias("dataocorrido")
                )
                .agg(count("*").alias("qtd"))
                .withColumn("datrefcarga", lit(output_datrefcarga))
                .select("macro_categoria", "dataocorrido", "datrefcarga", "qtd")
            )

            if classificacao.limit(1).count() == 0 and modo == "diario":
                raise ValueError(
                    f"Nenhum dado encontrado para datRefCarga: {datRefCarga}"
                )

            if classificacao.limit(1).count() == 0:
                log.info("Nenhum dado histórico para %s.", datRefCarga)
                return

            if modo == "historico":
                MacroCategoriaAiClassificacao._write_historical(
                    classificacao, output_table, datRefCarga
                )
            else:
                classificacao.write.mode("overwrite").option(
                    "replaceWhere", f"datrefcarga = '{datRefCarga}'"
                ).saveAsTable(output_table)
            log.info("MacroCategoriaAiClassificacao — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job MacroCategoriaAiClassificacao: {e}", exc_info=True)
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
        MacroCategoriaAiClassificacao.run(log, datRefCarga, modo)
    except Exception as e:
        log.error(f"Job MacroCategoriaAiClassificacao encerrado com falha: {e}", exc_info=True)
        raise
