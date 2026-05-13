"""
Tạo payload dưới dang JSON để gửi lên producer
"""
from data_loader import SENSOR_FLOAT_COLS, STATUS_INT_COLS, load_water_data
import json
import math

# Giới hạn vật lý hợp lệ của từng nhóm sensor trong mạng BATADAL
_SENSOR_RANGES = {
    # Tank levels (m)
    "L_T1": (0.0, 10.0), "L_T2": (0.0, 10.0), "L_T3": (0.0, 10.0),
    "L_T4": (0.0, 10.0), "L_T5": (0.0, 10.0), "L_T6": (0.0, 10.0),
    "L_T7": (0.0, 10.0),
    # Pump flows (L/s) — giá trị âm là không hợp lệ vật lý
    "F_PU1": (0.0, 500.0), "F_PU2": (0.0, 500.0), "F_PU3": (0.0, 500.0),
    "F_PU4": (0.0, 500.0), "F_PU5": (0.0, 500.0), "F_PU6": (0.0, 500.0),
    "F_PU7": (0.0, 500.0), "F_PU8": (0.0, 500.0), "F_PU9": (0.0, 500.0),
    "F_PU10": (0.0, 500.0), "F_PU11": (0.0, 500.0),
    # Valve flow (L/s)
    "F_V2": (0.0, 500.0),
    # Junction pressures (m)
    "P_J280": (-5.0, 100.0), "P_J269": (-5.0, 100.0), "P_J300": (-5.0, 100.0),
    "P_J256": (-5.0, 100.0), "P_J289": (-5.0, 100.0), "P_J415": (-5.0, 100.0),
    "P_J302": (-5.0, 100.0), "P_J306": (-5.0, 100.0), "P_J307": (-5.0, 100.0),
    "P_J317": (-5.0, 100.0), "P_J14":  (-5.0, 100.0), "P_J422": (-5.0, 100.0),
}


def validate_payload(payload: dict) -> list[str]:
    """
    Kiểm tra sanity của payload trước khi gửi lên Kafka.
    Trả về danh sách lỗi (rỗng = hợp lệ).
    """
    errors = []

    # 1. Kiểm tra timestamp tồn tại và không rỗng
    ts = payload.get("timestamp")
    if not ts or not isinstance(ts, str):
        errors.append("timestamp missing or invalid")

    # 2. Kiểm tra null / NaN trên tất cả sensor float
    for col in SENSOR_FLOAT_COLS:
        val = payload.get(col)
        if val is None or math.isnan(val):
            errors.append(f"{col} is null/NaN")
            continue
        # 3. Kiểm tra range vật lý
        lo, hi = _SENSOR_RANGES[col]
        if not (lo <= val <= hi):
            errors.append(f"{col}={val} out of range [{lo}, {hi}]")

    # 4. Kiểm tra status chỉ là 0 hoặc 1
    for col in STATUS_INT_COLS:
        val = payload.get(col)
        if val is None:
            errors.append(f"{col} is null")
        elif val not in (0, 1):
            errors.append(f"{col}={val} invalid (expected 0 or 1)")

    return errors


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
    skipped = 0
    for row in df.itertuples():
        payload = row_to_payload(row)
        errors = validate_payload(payload)
        if errors:
            skipped += 1
            print(f"[validation] SKIP row {row.Index}: {errors}")
            continue
        yield json.dumps(payload)
    if skipped:
        print(f"[validation] Total skipped: {skipped} rows")

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

