"""
Tests for producer/data_loader.py
Chạy: pytest tst/unit/test_data_loader.py -v
"""
import pytest
import pandas as pd

from data_loader import load_water_data, SENSOR_FLOAT_COLS, STATUS_INT_COLS, _parse_datetime


@pytest.fixture(scope="module")
def df():
    return load_water_data()


# --- _parse_datetime ---

def test_parse_datetime_format():
    result = _parse_datetime("14/09/16 03")
    assert result == "2016-09-14T03:00:00Z"


def test_parse_datetime_strips_whitespace():
    result = _parse_datetime("  01/01/16 00  ")
    assert result.endswith("Z")


# --- load_water_data ---

def test_load_returns_dataframe(df):
    assert isinstance(df, pd.DataFrame)


def test_load_has_rows(df):
    assert len(df) > 0


def test_load_has_timestamp_column(df):
    assert "timestamp" in df.columns


def test_load_no_datetime_column(df):
    # DATETIME phải được drop và thay bằng timestamp
    assert "DATETIME" not in df.columns


def test_load_all_sensor_cols_present(df):
    for col in SENSOR_FLOAT_COLS:
        assert col in df.columns, f"Missing sensor column: {col}"


def test_load_all_status_cols_present(df):
    for col in STATUS_INT_COLS:
        assert col in df.columns, f"Missing status column: {col}"


def test_load_att_flag_present(df):
    assert "ATT_FLAG" in df.columns


def test_load_no_unknown_att_flag(df):
    # drop_unknown=True (default) phải loại bỏ ATT_FLAG == -999
    assert (df["ATT_FLAG"] == -999).sum() == 0


def test_load_att_flag_values_binary(df):
    unique = set(df["ATT_FLAG"].dropna().unique())
    assert unique.issubset({0, 1}), f"ATT_FLAG có giá trị ngoài {{0,1}}: {unique}"


def test_load_no_null_sensor_cols(df):
    # drop_nulls=True (default)
    for col in SENSOR_FLOAT_COLS:
        nulls = df[col].isnull().sum()
        assert nulls == 0, f"Column {col} vẫn còn {nulls} null"


def test_load_dataset03_all_normal(df):
    # Dataset03 toàn bộ là NORMAL (ATT_FLAG=0)
    first_8761 = df.head(8761)
    assert (first_8761["ATT_FLAG"] == 0).all()


def test_load_dataset04_has_attacks(df):
    # Dataset04 có 219 dòng attack
    assert (df["ATT_FLAG"] == 1).sum() == 219


def test_load_sensor_cols_float_type(df):
    for col in SENSOR_FLOAT_COLS:
        assert pd.api.types.is_float_dtype(df[col]), f"{col} không phải float"


def test_load_att_flag_int_type(df):
    assert pd.api.types.is_integer_dtype(df["ATT_FLAG"])
