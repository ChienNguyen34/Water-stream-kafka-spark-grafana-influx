"""
load_water_data()
    └─> iter_payloads(df)  [từ payload_builder.py]
            └─> for mỗi payload:
                    produce() -> poll() -> sleep(0.02s)
"""
from confluent_kafka import Producer
import time

from config import KAFKA_BROKER, KAFKA_TOPIC, SLEEP_SEC
from data_loader import load_water_data
from payload_builder import iter_payloads

producer = Producer({"bootstrap.servers": KAFKA_BROKER})

def delivery_report(err, msg):
    if err:
        print(f"[ERROR] {err}")
    else:
        print(f"[OK] offset={msg.offset()}")

def message_produce():
    df = load_water_data()
    while True:
        for payload in iter_payloads(df):
            producer.produce(KAFKA_TOPIC, value= payload.encode("utf-8"), callback=delivery_report)
            producer.poll(0)
            time.sleep(SLEEP_SEC)
            
        producer.flush()
        print("[producer] Dataset finished, restarting...")
if __name__ == "__main__":
    message_produce()


