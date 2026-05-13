"""
Tests for producer/payload_builder.py
Chạy: pytest tst/unit/test_payload_builder.py -v
"""
import json
import pytest

from data_loader import load_water_data, SENSOR_FLOAT_COLS, STATUS_INT_COLS
from payload_builder import row_to_payload, iter_payloads


@pytest.fixture(scope="module")
def df():
    return load_water_data()


@pytest.fixture(scope="module")
def normal_row(df):
    return next(df.itertuples())


@pytest.fixture(scope="module")
def attack_row(df):
    return next(df[df["ATT_FLAG"] == 1].itertuples())


# --- row_to_payload: cấu trúc ---

def test_payload_has_timestamp(normal_row):
    p = row_to_payload(normal_row)
    assert "timestamp" in p


def test_payload_timestamp_iso8601(normal_row):
    p = row_to_payload(normal_row)
    ts = p["timestamp"]
    assert ts.endswith("Z")
    assert "T" in ts


def test_payload_has_all_sensor_cols(normal_row):
    p = row_to_payload(normal_row)
    for col in SENSOR_FLOAT_COLS:
        assert col in p, f"Thiếu sensor field: {col}"


def test_payload_has_all_status_cols(normal_row):
    p = row_to_payload(normal_row)
    for col in STATUS_INT_COLS:
        assert col in p, f"Thiếu status field: {col}"


def test_payload_has_att_flag(normal_row):
    p = row_to_payload(normal_row)
    assert "ATT_FLAG" in p


# --- row_to_payload: kiểu dữ liệu ---

def test_payload_sensor_values_are_float(normal_row):
    p = row_to_payload(normal_row)
    for col in SENSOR_FLOAT_COLS:
        assert isinstance(p[col], float), f"{col} không phải float"


def test_payload_status_values_are_int(normal_row):
    p = row_to_payload(normal_row)
    for col in STATUS_INT_COLS:
        assert isinstance(p[col], int), f"{col} không phải int"


def test_payload_att_flag_is_int(normal_row):
    p = row_to_payload(normal_row)
    assert isinstance(p["ATT_FLAG"], int)


def test_payload_sensor_rounded_4_decimals(normal_row):
    p = row_to_payload(normal_row)
    for col in SENSOR_FLOAT_COLS:
        val = p[col]
        assert round(val, 4) == val, f"{col} chưa được round 4 chữ số thập phân"


# --- row_to_payload: giá trị ---

def test_payload_normal_att_flag_is_0(normal_row):
    p = row_to_payload(normal_row)
    assert p["ATT_FLAG"] == 0


def test_payload_attack_att_flag_is_1(attack_row):
    p = row_to_payload(attack_row)
    assert p["ATT_FLAG"] == 1


def test_payload_status_values_binary(normal_row):
    p = row_to_payload(normal_row)
    for col in STATUS_INT_COLS:
        assert p[col] in (0, 1), f"{col} có giá trị không hợp lệ: {p[col]}"


def test_payload_tank_levels_positive(normal_row):
    p = row_to_payload(normal_row)
    for col in ["L_T1", "L_T2", "L_T3", "L_T4", "L_T5", "L_T6", "L_T7"]:
        assert p[col] >= 0, f"{col} âm: {p[col]}"


# --- iter_payloads ---

def test_iter_payloads_yields_valid_json(df):
    gen = iter_payloads(df)
    first = next(gen)
    parsed = json.loads(first)
    assert isinstance(parsed, dict)
    assert "timestamp" in parsed


def test_iter_payloads_count(df):
    # iter_payloads có thể skip rows không hợp lệ (validation) nên count <= len(df)
    count = sum(1 for _ in iter_payloads(df))
    assert 0 < count <= len(df)


def test_iter_payloads_no_nan_in_json(df):
    # JSON không hỗ trợ NaN — kiểm tra không có chuỗi 'NaN' trong output
    gen = iter_payloads(df)
    for i, payload_str in enumerate(gen):
        assert "NaN" not in payload_str, f"Row {i} chứa NaN trong JSON"
        if i >= 100:
            break  # kiểm tra 100 row đầu là đủ
