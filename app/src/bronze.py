import logging
import re
import unicodedata

from pyspark.sql.functions import col, lit
from pyspark.sql.types import StructType

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger("bronze")


def normalize_column_name(name):
    """Normaliza cabeçalhos para permitir variações de acentos e separadores."""
    without_accents = unicodedata.normalize("NFKD", name)
    without_accents = "".join(
        char for char in without_accents
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]", "", without_accents.lower())


def build_source_column_mapping(source_columns):
    """Cria o mapa normalizado -> nome original e rejeita duplicidades."""
    mapping = {}
    for source_column in source_columns:
        normalized = normalize_column_name(source_column)
        if not normalized:
            raise ValueError(
                f"Cabeçalho inválido: '{source_column}' não possui caracteres válidos"
            )
        if normalized in mapping:
            raise ValueError(
                "Cabeçalhos duplicados após normalização: "
                f"'{mapping[normalized]}' e '{source_column}'"
            )
        mapping[normalized] = source_column
    return mapping


def select_bronze_columns(df, schema):
    """Seleciona colunas pelo nome, preenchendo ausentes com NULL."""
    source_columns = build_source_column_mapping(df.columns)
    selected_columns = []

    for field in schema.fields:
        source_column = source_columns.get(normalize_column_name(field.name))
        if source_column is None:
            selected_columns.append(lit(None).cast(field.dataType).alias(field.name))
            log.warning("Coluna '%s' ausente no CSV; preenchendo com NULL", field.name)
        else:
            selected_columns.append(col(source_column).cast(field.dataType).alias(field.name))

    return df.select(*selected_columns)


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class Bronze:

    @staticmethod
    def run(log, datRefCarga, env):        

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
            pathCsv = f"s3://{env}-us-east-2-data-master/tmp/basecompleta{datRefCarga}*.csv"
            raw_df = (
                spark.read
                .option("header", True)
                .option("inferSchema", False)
                .option("sep", ";")
                .csv(pathCsv)
            )
            df = select_bronze_columns(raw_df, schema)
            log.info("Leitura do CSV concluída com sucesso")

            df = df.withColumn("datRefCarga", lit(datRefCarga))

            if df.limit(1).count() == 0:
                raise ValueError(
                    f"Nenhum dado encontrado para datRefCarga: {datRefCarga}"
                )

            (
                df.write
                .mode("overwrite")
                .option("replaceWhere", f"datRefCarga = '{datRefCarga}'")
                .saveAsTable("b_consumidor.consumidor")
            )
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
