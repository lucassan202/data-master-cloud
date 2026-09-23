# Databricks notebook source
"""Carga mensal do histórico Kaggle para a Bronze histórica."""

import logging

from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bronze_kaggle_historico")


def run(log, dat_ref_carga, env, s3_key):
    if not dat_ref_carga or len(dat_ref_carga) != 7 or dat_ref_carga[4] != "-":
        raise ValueError("datRefCarga deve estar no formato YYYY-MM.")

    bucket = f"{env}-us-east-2-data-master"
    source_path = f"s3://{bucket}/{s3_key.lstrip('/')}"
    target_table = "b_consumidor.consumidor_historico"

    schema = StructType(
        [
            StructField("id", LongType(), True),
            StructField("empresa", StringType(), True),
            StructField("data", StringType(), True),
            StructField("local", StringType(), True),
            StructField("status", StringType(), True),
            StructField("nota", StringType(), True),
            StructField("relato", StringType(), True),
            StructField("resposta", StringType(), True),
            StructField("comentario", StringType(), True),
        ]
    )

    log.info("Lendo histórico Kaggle: %s", source_path)
    source = (
        spark.read  # noqa: F821
        .schema(schema)
        .option("multiLine", True)
        .json(source_path)
    )

    data_parseada = F.to_date(F.col("data"), "yyyy-MM-dd")
    local_parts = F.split(F.col("local"), r"\s*-\s*")
    month_filter = F.date_format(data_parseada, "yyyy-MM") == F.lit(dat_ref_carga)

    current_month = (
        source.filter(month_filter)
        .filter(F.lower(F.trim(F.col("empresa"))) == F.lit("banco santander"))
        .filter(F.lower(F.trim(F.col("status"))) == F.lit("não resolvido"))
        .select(
            F.col("empresa").alias("nomeempresa"),
            F.col("status"),
            F.lit(None).cast("string").alias("temporesposta"),
            F.col("data").alias("dataocorrido"),
            F.trim(F.element_at(local_parts, 1)).alias("cidade"),
            F.upper(F.trim(F.element_at(local_parts, 2))).alias("uf"),
            F.col("relato"),
            F.col("resposta"),
            F.col("nota"),
            F.col("comentario"),
            F.lit(dat_ref_carga).alias("datrefcarga"),
            F.lit("kaggle").alias("fonte"),
            F.col("id").cast("long").alias("source_record_id"),
        )
        .dropDuplicates(["fonte", "source_record_id"])
    )

    if current_month.limit(1).count() == 0:
        log.warning("Nenhum Banco Santander não resolvido encontrado em %s.", dat_ref_carga)
        return 0

    existing = (
        spark.table(target_table)  # noqa: F821
        .filter(F.col("datrefcarga") == dat_ref_carga)
        .select("fonte", "source_record_id")
        .dropDuplicates()
    )
    new_records = current_month.join(
        existing,
        on=["fonte", "source_record_id"],
        how="leftanti",
    )
    new_count = new_records.count()

    if new_count == 0:
        log.info("Mês %s já está carregado na Bronze histórica.", dat_ref_carga)
        return 0

    (
        new_records.write
        .mode("append")
        .saveAsTable(target_table)
    )
    log.info("Bronze histórica carregada: %d registros em %s.", new_count, dat_ref_carga)
    return new_count


if __name__ == "__main__":
    dbutils.widgets.text("datRefCarga", "")  # noqa: F821
    dbutils.widgets.text("env", "dev")  # noqa: F821
    dbutils.widgets.text("s3_key", "screp/historico/kaggle/dados2025.json")  # noqa: F821

    dat_ref_carga = dbutils.widgets.get("datRefCarga")  # noqa: F821
    env = dbutils.widgets.get("env")  # noqa: F821
    s3_key = dbutils.widgets.get("s3_key")  # noqa: F821
    run(log, dat_ref_carga, env, s3_key)
