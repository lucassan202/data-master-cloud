import logging
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("bronze")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class Bronze:

    @staticmethod
    def run(log, datRefCarga, env='dev'):        

        schema = (
            StructType()
            .add("gestor", "string")
            .add("canalOrigem", "string")
            .add("regiao", "string")
            .add("uf", "string")
            .add("cidade", "string")
            .add("sexo", "string")
            .add("faixaEtaria", "string")
            .add("anoAbertura", "string")
            .add("mesAbertura", "string")
            .add("dataAbertura", "string")
            .add("dataResposta", "string")
            .add("dataAnalise", "string")
            .add("dataRecusa", "string")
            .add("dataFinalizacao", "string")
            .add("prazoResposta", "string")
            .add("prazoAnaliseGestor", "string")
            .add("tempoResposta", "string")
            .add("nomeFantasia", "string")
            .add("segmentoMercado", "string")
            .add("area", "string")
            .add("assunto", "string")
            .add("grupoProblema", "string")
            .add("problema", "string")
            .add("comoContratou", "string")
            .add("procurouEmpresa", "string")
            .add("respondida", "string")
            .add("situacao", "string")
            .add("avaliacaoReclamacao", "string")
            .add("notaConsumidor", "string")
            .add("analiseRecusa", "string")
        )

        try:
            log.info(f"Iniciando leitura do CSV basecompleta — datRefCarga: {datRefCarga}")
            df = (
                spark.read.schema(schema)
                .option("header", True)
                .option("sep", ";")
                .csv(f"s3://{env}-us-east-2-data-master/tmp/basecompleta{datRefCarga}*.csv")
            )
            log.info("Leitura do CSV concluída com sucesso")

            df = df.withColumn("datRefCarga", lit(datRefCarga))

            spark.sql(f"DELETE FROM b_consumidor.consumidor WHERE datRefCarga = '{datRefCarga}'")
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            df.write.mode("append").insertInto("b_consumidor.consumidor")
            log.info("Bronze — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job Bronze: {e}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Entry point — Databricks Job / Notebook
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Parâmetros recebidos via Databricks Widgets
    dbutils.widgets.text("datRefCarga", "")  # noqa: F821
    dbutils.widgets.text("env", "")  # noqa: F821

    datRefCarga = dbutils.widgets.get("datRefCarga")  # noqa: F821
    env = dbutils.widgets.get("env")

    if not datRefCarga:
        raise ValueError("O parâmetro 'datRefCarga' é obrigatório e não foi informado.")    

    log.info(f"Parâmetros recebidos — datRefCarga: {datRefCarga}")

    try:
        Bronze.run(log, datRefCarga, env)
    except Exception as e:
        log.error(f"Job Bronze encerrado com falha: {e}", exc_info=True)
        raise
