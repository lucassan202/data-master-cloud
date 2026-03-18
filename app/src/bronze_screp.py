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
log = logging.getLogger("bronze_screp")


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class BronzeScrep:

    @staticmethod
    def run(log, datRefCarga, env):

        schema = (
            StructType()
            .add("nomeEmpresa", "string")
            .add("status", "string")
            .add("tempoResposta", "string")
            .add("dataOcorrido", "string")
            .add("Cidade", "string")
            .add("UF", "string")
            .add("Relato", "string")
            .add("Resposta", "string")
            .add("Nota", "string")
            .add("Comentario", "string")
        )

        try:
            log.info(f"Iniciando leitura do CSV screp — datRefCarga: {datRefCarga}")
            pathCsv = f"s3://{env}-us-east-2-data-master/screp/reclamacoes_{datRefCarga}.csv"
            df = (
                spark.read.schema(schema)  # noqa: F821
                .option("header", True)
                .option("sep", "|")
                .csv(pathCsv)
            )
            log.info("Leitura do CSV concluída com sucesso")

            df = df.withColumn("datRefCarga", lit(datRefCarga))

            spark.sql(f"DELETE FROM b_consumidor.consumidor_dia WHERE datRefCarga = '{datRefCarga}'")  # noqa: F821
            log.info(f"Dados anteriores removidos para datRefCarga: {datRefCarga}")

            df.write.mode("append").insertInto("b_consumidor.consumidor_dia")
            log.info("Bronze Screp — job finalizado com sucesso")

        except Exception as e:
            log.error(f"Erro durante a execução do job Bronze Screp: {e}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Entry point — Databricks Job / Notebook
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Parâmetros recebidos via Databricks Widgets
    dbutils.widgets.text("datRefCarga", "")  # noqa: F821
    dbutils.widgets.text("env", "")  # noqa: F821

    datRefCarga = dbutils.widgets.get("datRefCarga")  # noqa: F821
    env = dbutils.widgets.get("env")  # noqa: F821

    if not datRefCarga:
        raise ValueError("O parâmetro 'datRefCarga' é obrigatório e não foi informado.")

    log.info(f"Parâmetros recebidos — datRefCarga: {datRefCarga}, env: {env}")

    try:
        BronzeScrep.run(log, datRefCarga, env)
    except Exception as e:
        log.error(f"Job Bronze Screp encerrado com falha: {e}", exc_info=True)
