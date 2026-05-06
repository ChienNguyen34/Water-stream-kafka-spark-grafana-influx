"""
Tạo payload dưới dang JSON để gửi lên producer
"""
from data_loader import SENSOR_FLOAT_COLS, STATUS_INT_COLS, load_water_data
import json

def row_to_payload(row) -> dict:
    """
    Hàm lặp qua từng hàng của dataframe và trả về payload
    """
    payload = {"timestamp": row.timestamp}

    for col in SENSOR_FLOAT_COLS:
        payload[col] = round(float(getattr(row, col)), 4)

    for col in STATUS_INT_COLS:
        payload[col] = int(getattr(row, col))

    payload["ATT_FLAG"] = int(row.ATT_FLAG)

    return payload

def iter_payloads(df):
    for row in df.itertuples():
        yield json.dumps(row_to_payload(row))

def payload_builder():
    """
    Hàm test full payload
    """
    payloads = []
    df = load_water_data()
    for row in df.itertuples():
        payload = json.dumps(row_to_payload(row))
        payloads.append(payload)
    print(payloads[0])

