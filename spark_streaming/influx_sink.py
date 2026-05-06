from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / "config.env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass  # trong Docker inject qua env vars, không cần dotenv

INFLUX_URL    = os.getenv("INFLUX_URL",    "http://influxdb:8086")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN",  "my-super-secret-token")
INFLUX_ORG    = os.getenv("INFLUX_ORG",    "bigdata")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "water_bucket")

_FLOAT_FIELDS = [
    "L_T1","L_T2","L_T3","L_T4","L_T5","L_T6","L_T7",
    "F_PU1","F_PU2","F_PU3","F_PU4","F_PU5","F_PU6",
    "F_PU7","F_PU8","F_PU9","F_PU10","F_PU11","F_V2",
    "P_J280","P_J269","P_J300","P_J256","P_J289","P_J415",
    "P_J302","P_J306","P_J307","P_J317","P_J14","P_J422",
]
_INT_FIELDS = [
    "S_PU1","S_PU2","S_PU3","S_PU4","S_PU5","S_PU6",
    "S_PU7","S_PU8","S_PU9","S_PU10","S_PU11","S_V2",
    "ATT_FLAG",
]

def write_to_influx(df_batch, batch_id):
    if df_batch.isEmpty():
        return

    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    points = []
    for row in df_batch.collect():
        point = Point("water_telemetry") \
            .tag("alert_type", row.alert_type)

        for f in _FLOAT_FIELDS:
            val = getattr(row, f, None)
            if val is not None:
                point = point.field(f, float(val))

        for f in _INT_FIELDS:
            val = getattr(row, f, None)
            if val is not None:
                point = point.field(f, int(val))

        point = point.time(row.timestamp)
        points.append(point)

    write_api.write(bucket=INFLUX_BUCKET, record=points)
    client.close()
    print(f"[sink] batch {batch_id}: wrote {len(points)} points")