"""
Đọc config từ biến môi trường.
- Chạy local: load từ file config.env (dotenv)
- Chạy trong Docker: docker-compose inject qua environment:
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Chỉ load file .env khi chạy local (file tồn tại)
_env_path = Path(__file__).parent / "config.env"
if _env_path.exists():
    load_dotenv(_env_path)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_TOPIC", "water_stream")

_interval = float(os.getenv("ORIGINAL_INTERVAL_SEC", "3600"))
_factor   = float(os.getenv("COMPRESSION_FACTOR", "180000"))
SLEEP_SEC = _interval / _factor   # 3600 / 180000 = 0.02s -> 50 msg/s
