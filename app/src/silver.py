import logging
from pyspark.sql.functions import col, lit, when, from_unixtime, unix_timestamp
from pyspark.sql.types import DateType, BooleanType, IntegerType


# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("silver")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class Silver:

    @staticmethod
    def run(log, datRefCarga):

        columns = [
            "dataAbertura",
            "dataResposta",
            "dataAnalise",
            "dataRecusa",
            "prazoResposta",
            "procurouEmpresa",
            "respondida",
            "anoAbertura",
            "mesAbertura",
            "dataFinalizacao",
            "prazoAnaliseGestor",
            "tempoResposta",
            "notaConsumidor",
        ]

        expressions = [
            from_unixtime(unix_timestamp(col("dataAbertura"), "dd/MM/yyyy")).cast(DateType()),
            from_unixtime(unix_timestamp(col("dataResposta"), "dd/MM/yyyy")).cast(DateType()),
            from_unixtime(unix_timestamp(col("dataAnalise"), "dd/MM/yyyy")).cast(DateType()),
            from_unixtime(unix_timestamp(col("dataRecusa"), "dd/MM/yyyy")).cast(DateType()),
            from_unixtime(unix_timestamp(col("prazoResposta"), "dd/MM/yyyy")).cast(DateType()),
            when(col("procurouEmpresa") == "S", lit(1)).otherwise(lit(0)).cast(BooleanType()),
            when(col("respondida") == "S", lit(1)).otherwise(lit(0)).cast(BooleanType()),
            col("anoAbertura").cast(IntegerType()),
            col("mesAbertura").cast(IntegerType()),
            col("dataFinalizacao").cast(DateType()),
            col("prazoAnaliseGestor").cast(IntegerType()),
            col("tempoResposta").cast(IntegerType()),
            col("notaConsumidor").cast(IntegerType()),
        ]

        try:
            log.info(f"Iniciando job Silver — datRefCarga: {datRefCarga}")

            consumidor = spark.table("b_consumidor.consumidor").filter(col('datRefCarga') == datRefCarga)

            log.info("Aplicando conversão de tipos nas colunas")
            consumidor = Silver.qualifyTypeColumn(consumidor, columns, expressions, log)

            log.info("Aplicando filtro: nomefantasia LIKE 'Banco%' AND area = 'Serviços Financeiros'")
            consumidor = consumidor.filter(
                (col("nomefantasia").like("Banco%")) & (col("area") == "Serviços Financeiros")
            )

            spark.sql(f"DELETE FROM s_consumidor.consumidorservicosfinanceiros WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            consumidor.write.mode("append").insertInto("s_consumidor.consumidorservicosfinanceiros")
            log.info("Silver — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job Silver: {e}", exc_info=True)
            raise

    def qualifyTypeColumn(df, columns, expressions, logger=None):
        _log = logger or log
        try:
            _log.info(f"Iniciando conversão de tipos para as colunas: {columns}")
            for column, expression in zip(columns, expressions):
                _log.info(f"Convertendo coluna: {column}")
                df = df.withColumn(column, expression)
            _log.info("Conversão de tipos concluída com sucesso")
            return df
        except Exception as e:
            _log.error(f"Erro ao converter tipos das colunas: {e}", exc_info=True)
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
        Silver.run(log, datRefCarga)
    except Exception as e:
        log.error(f"Job Silver encerrado com falha: {e}", exc_info=True)
        raise
