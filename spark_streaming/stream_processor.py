from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType
from pyspark.sql.functions import from_json, col, when, lit
from influx_sink import write_to_influx
import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_TOPIC",  "water_stream")

WATER_SCHEMA = StructType([
    StructField("timestamp", StringType(), True),
    # Tank levels
    StructField("L_T1",  FloatType(), True),
    StructField("L_T2",  FloatType(), True),
    StructField("L_T3",  FloatType(), True),
    StructField("L_T4",  FloatType(), True),
    StructField("L_T5",  FloatType(), True),
    StructField("L_T6",  FloatType(), True),
    StructField("L_T7",  FloatType(), True),
    # Pump flows & statuses
    StructField("F_PU1",  FloatType(),   True),
    StructField("S_PU1",  IntegerType(), True),
    StructField("F_PU2",  FloatType(),   True),
    StructField("S_PU2",  IntegerType(), True),
    StructField("F_PU3",  FloatType(),   True),
    StructField("S_PU3",  IntegerType(), True),
    StructField("F_PU4",  FloatType(),   True),
    StructField("S_PU4",  IntegerType(), True),
    StructField("F_PU5",  FloatType(),   True),
    StructField("S_PU5",  IntegerType(), True),
    StructField("F_PU6",  FloatType(),   True),
    StructField("S_PU6",  IntegerType(), True),
    StructField("F_PU7",  FloatType(),   True),
    StructField("S_PU7",  IntegerType(), True),
    StructField("F_PU8",  FloatType(),   True),
    StructField("S_PU8",  IntegerType(), True),
    StructField("F_PU9",  FloatType(),   True),
    StructField("S_PU9",  IntegerType(), True),
    StructField("F_PU10", FloatType(),   True),
    StructField("S_PU10", IntegerType(), True),
    StructField("F_PU11", FloatType(),   True),
    StructField("S_PU11", IntegerType(), True),
    # Valve flow & status
    StructField("F_V2", FloatType(),   True),
    StructField("S_V2", IntegerType(), True),
    # Junction pressures
    StructField("P_J280", FloatType(), True),
    StructField("P_J269", FloatType(), True),
    StructField("P_J300", FloatType(), True),
    StructField("P_J256", FloatType(), True),
    StructField("P_J289", FloatType(), True),
    StructField("P_J415", FloatType(), True),
    StructField("P_J302", FloatType(), True),
    StructField("P_J306", FloatType(), True),
    StructField("P_J307", FloatType(), True),
    StructField("P_J317", FloatType(), True),
    StructField("P_J14",  FloatType(), True),
    StructField("P_J422", FloatType(), True),
    # Label
    StructField("ATT_FLAG", IntegerType(), True),
])

spark = SparkSession.builder \
    .appName("WaterGridStreaming") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

df_parsed = df_raw \
    .select(from_json(col("value").cast("string"), WATER_SCHEMA).alias("data")) \
    .select("data.*")

df_clean = df_parsed.filter(col("L_T1").isNotNull())

df_flagged = df_clean.withColumn(
    "alert_type",
    when(
        # PU1 đang ON nhưng T1 > 6.3 (đáng lẽ phải tắt)
        (col("S_PU1") == 1) & (col("L_T1") > 6.3), lit("PU1_STUCK_ON")
    ).when(
        # PU1 đang OFF nhưng T1 < 4.0 (đáng lẽ phải bật)
        (col("S_PU1") == 0) & (col("L_T1") < 4.0), lit("PU1_STUCK_OFF")
    ).otherwise(lit("NORMAL"))
    # ATT_FLAG được giữ lại như field riêng trong InfluxDB để đánh giá sau,
    # KHÔNG dùng làm điều kiện detection — tránh data leakage.
)

query = df_flagged.writeStream \
    .foreachBatch(write_to_influx) \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .start()

query.awaitTermination()