from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType
from pyspark.sql.functions import from_json, col, when, lit
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import IntegerType as IntType
from influx_sink import write_to_influx
import os
import pickle

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_TOPIC",  "water_stream")

# ML model features (must match train_model.py ML_FEATURES order)
_ML_FEATURES = [
    "L_T1","L_T2","L_T3","L_T4","L_T5","L_T6","L_T7",
    "F_PU1","F_PU2","F_PU3","F_PU4","F_PU5","F_PU6",
    "F_PU7","F_PU8","F_PU9","F_PU10","F_PU11","F_V2",
    "S_PU1","S_PU2","S_PU3","S_PU4","S_PU5","S_PU6",
    "S_PU7","S_PU8","S_PU9","S_PU10","S_PU11","S_V2",
]

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

# ── ML model: broadcast to all executors ─────────────────────────────────────
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "anomaly_model.pkl")
if os.path.exists(_MODEL_PATH):
    with open(_MODEL_PATH, "rb") as _f:
        _bc_model = spark.sparkContext.broadcast(pickle.load(_f))

    @pandas_udf(IntType())
    def _ml_predict(*cols):
        import pandas as pd
        df_feat = pd.concat(list(cols), axis=1)
        df_feat.columns = _ML_FEATURES
        df_feat = df_feat.fillna(0.0)
        preds = _bc_model.value.predict(df_feat)
        return pd.Series(preds.astype(int))

    _ml_available = True
    print("[ML] anomaly_model.pkl loaded — ml_alert active")
else:
    _ml_available = False
    print("[ML] anomaly_model.pkl not found — ml_alert defaults to 0")

df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("maxOffsetsPerTrigger", 1000) \
    .load()

df_parsed = df_raw \
    .select(from_json(col("value").cast("string"), WATER_SCHEMA).alias("data")) \
    .select("data.*")

df_clean = df_parsed.filter(
    col("L_T1").isNotNull() &
    col("L_T2").isNotNull() &
    col("L_T3").isNotNull() &
    col("L_T4").isNotNull() &
    col("L_T5").isNotNull() &
    col("L_T6").isNotNull() &
    col("L_T7").isNotNull()
)

df_flagged = df_clean.withColumn(
    "alert_type",
    # T1 — PU1 (OPEN <4.0, CLOSED >6.3) [CTOWN.INP CONTROLS]
    when((col("S_PU1") == 1) & (col("L_T1") > 6.3),  lit("PU1_STUCK_ON"))
    .when((col("S_PU1") == 0) & (col("L_T1") < 4.0), lit("PU1_STUCK_OFF"))
    # T1 — PU2 (OPEN <1.0, CLOSED >4.5)
    .when((col("S_PU2") == 1) & (col("L_T1") > 4.5), lit("PU2_STUCK_ON"))
    .when((col("S_PU2") == 0) & (col("L_T1") < 1.0), lit("PU2_STUCK_OFF"))
    # T2 — V2 valve (OPEN <0.5, CLOSED >5.5)
    .when((col("S_V2") == 1) & (col("L_T2") > 5.5),  lit("V2_STUCK_ON"))
    .when((col("S_V2") == 0) & (col("L_T2") < 0.5),  lit("V2_STUCK_OFF"))
    # T3 — PU4 (OPEN <3.0, CLOSED >5.3)
    .when((col("S_PU4") == 1) & (col("L_T3") > 5.3), lit("PU4_STUCK_ON"))
    .when((col("S_PU4") == 0) & (col("L_T3") < 3.0), lit("PU4_STUCK_OFF"))
    # T3 — PU5 (OPEN <1.0, CLOSED >3.5)
    .when((col("S_PU5") == 1) & (col("L_T3") > 3.5), lit("PU5_STUCK_ON"))
    .when((col("S_PU5") == 0) & (col("L_T3") < 1.0), lit("PU5_STUCK_OFF"))
    # T4 — PU6 (OPEN <2.0, CLOSED >3.5)
    .when((col("S_PU6") == 1) & (col("L_T4") > 3.5), lit("PU6_STUCK_ON"))
    .when((col("S_PU6") == 0) & (col("L_T4") < 2.0), lit("PU6_STUCK_OFF"))
    # T4 — PU7 (OPEN <3.0, CLOSED >4.5)
    .when((col("S_PU7") == 1) & (col("L_T4") > 4.5), lit("PU7_STUCK_ON"))
    .when((col("S_PU7") == 0) & (col("L_T4") < 3.0), lit("PU7_STUCK_OFF"))
    # T5 — PU8 (OPEN <1.5, CLOSED >4.0)
    .when((col("S_PU8") == 1) & (col("L_T5") > 4.0), lit("PU8_STUCK_ON"))
    .when((col("S_PU8") == 0) & (col("L_T5") < 1.5), lit("PU8_STUCK_OFF"))
    # T7 — PU10 (OPEN <2.5, CLOSED >4.8)
    .when((col("S_PU10") == 1) & (col("L_T7") > 4.8), lit("PU10_STUCK_ON"))
    .when((col("S_PU10") == 0) & (col("L_T7") < 2.5), lit("PU10_STUCK_OFF"))
    # T7 — PU11 (OPEN <1.0, CLOSED >3.0)
    .when((col("S_PU11") == 1) & (col("L_T7") > 3.0), lit("PU11_STUCK_ON"))
    .when((col("S_PU11") == 0) & (col("L_T7") < 1.0), lit("PU11_STUCK_OFF"))
    .otherwise(lit("NORMAL"))
    # ATT_FLAG được giữ lại như field riêng trong InfluxDB để đánh giá sau,
    # KHÔNG dùng làm điều kiện detection — tránh data leakage.
)

# disp_PUx / disp_V2: 0=OFF(xám), 1=ON(xanh), 2=ALERT(đỏ)
# Dùng cho Canvas color binding vì canvas không bind được string field
df_flagged = df_flagged \
    .withColumn("disp_PU1",
        when((col("S_PU1") == 1) & (col("L_T1") > 6.3), lit(2))
        .when((col("S_PU1") == 0) & (col("L_T1") < 4.0), lit(2))
        .otherwise(col("S_PU1").cast("integer"))
    ) \
    .withColumn("disp_PU2",
        when((col("S_PU2") == 1) & (col("L_T1") > 4.5), lit(2))
        .when((col("S_PU2") == 0) & (col("L_T1") < 1.0), lit(2))
        .otherwise(col("S_PU2").cast("integer"))
    ) \
    .withColumn("disp_V2",
        when((col("S_V2") == 1) & (col("L_T2") > 5.5), lit(2))
        .when((col("S_V2") == 0) & (col("L_T2") < 0.5), lit(2))
        .otherwise(col("S_V2").cast("integer"))
    ) \
    .withColumn("disp_PU4",
        when((col("S_PU4") == 1) & (col("L_T3") > 5.3), lit(2))
        .when((col("S_PU4") == 0) & (col("L_T3") < 3.0), lit(2))
        .otherwise(col("S_PU4").cast("integer"))
    ) \
    .withColumn("disp_PU5",
        when((col("S_PU5") == 1) & (col("L_T3") > 3.5), lit(2))
        .when((col("S_PU5") == 0) & (col("L_T3") < 1.0), lit(2))
        .otherwise(col("S_PU5").cast("integer"))
    ) \
    .withColumn("disp_PU6",
        when((col("S_PU6") == 1) & (col("L_T4") > 3.5), lit(2))
        .when((col("S_PU6") == 0) & (col("L_T4") < 2.0), lit(2))
        .otherwise(col("S_PU6").cast("integer"))
    ) \
    .withColumn("disp_PU7",
        when((col("S_PU7") == 1) & (col("L_T4") > 4.5), lit(2))
        .when((col("S_PU7") == 0) & (col("L_T4") < 3.0), lit(2))
        .otherwise(col("S_PU7").cast("integer"))
    ) \
    .withColumn("disp_PU8",
        when((col("S_PU8") == 1) & (col("L_T5") > 4.0), lit(2))
        .when((col("S_PU8") == 0) & (col("L_T5") < 1.5), lit(2))
        .otherwise(col("S_PU8").cast("integer"))
    ) \
    .withColumn("disp_PU10",
        when((col("S_PU10") == 1) & (col("L_T7") > 4.8), lit(2))
        .when((col("S_PU10") == 0) & (col("L_T7") < 2.5), lit(2))
        .otherwise(col("S_PU10").cast("integer"))
    ) \
    .withColumn("disp_PU11",
        when((col("S_PU11") == 1) & (col("L_T7") > 3.0), lit(2))
        .when((col("S_PU11") == 0) & (col("L_T7") < 1.0), lit(2))
        .otherwise(col("S_PU11").cast("integer"))
    )

# ── ML Early Warning ──────────────────────────────────────────────────────────
if _ml_available:
    df_flagged = df_flagged.withColumn(
        "ml_alert",
        _ml_predict(*[col(f) for f in _ML_FEATURES])
    )
else:
    df_flagged = df_flagged.withColumn("ml_alert", lit(0))

query = df_flagged.writeStream \
    .foreachBatch(write_to_influx) \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .start()

query.awaitTermination()