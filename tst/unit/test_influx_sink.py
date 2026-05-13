"""
Tests for spark_streaming/influx_sink.py
Dùng unittest.mock để thay thế InfluxDBClient — không cần InfluxDB thật.
Chạy: pytest tst/unit/test_influx_sink.py -v
"""
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import influx_sink
from influx_sink import write_to_influx, _FLOAT_FIELDS, _INT_FIELDS


# ---------------------------------------------------------------------------
# Helper: tạo một Spark-like row giả (SimpleNamespace)
# ---------------------------------------------------------------------------

def make_row(**overrides):
    """Tạo row với đầy đủ field mặc định, override theo ý muốn."""
    defaults = dict(
        alert_type="NORMAL",
        timestamp="2016-01-01T00:00:00Z",
        L_T1=5.0,  L_T2=3.0,  L_T3=2.5,  L_T4=1.5,
        L_T5=2.0,  L_T6=1.8,  L_T7=2.2,
        F_PU1=0.5, F_PU2=0.0, F_PU3=0.3, F_PU4=0.2,
        F_PU5=0.0, F_PU6=0.1, F_PU7=0.0, F_PU8=0.0,
        F_PU9=0.0, F_PU10=0.0, F_PU11=0.0, F_V2=0.4,
        P_J280=10.0, P_J269=9.5, P_J300=11.0, P_J256=8.0,
        P_J289=9.0,  P_J415=7.5, P_J302=10.5, P_J306=9.8,
        P_J307=10.2, P_J317=8.5, P_J14=11.5,  P_J422=7.0,
        S_PU1=1, S_PU2=0, S_PU3=1, S_PU4=0,
        S_PU5=0, S_PU6=1, S_PU7=0, S_PU8=0,
        S_PU9=0, S_PU10=0, S_PU11=0, S_V2=1,
        ATT_FLAG=0,
        disp_PU1=1, disp_PU2=0, disp_PU3=1,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_batch(*rows):
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = False
    mock_df.collect.return_value = list(rows)
    return mock_df


def make_empty_batch():
    mock_df = MagicMock()
    mock_df.isEmpty.return_value = True
    return mock_df


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_batch_does_not_call_influx():
    with patch("influx_sink.InfluxDBClient") as mock_client_cls:
        write_to_influx(make_empty_batch(), batch_id=0)
        mock_client_cls.assert_not_called()


@patch("influx_sink.InfluxDBClient")
def test_write_calls_write_api(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row()), batch_id=1)
    mock_write_api.write.assert_called_once()


@patch("influx_sink.InfluxDBClient")
def test_write_passes_correct_bucket(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row()), batch_id=1)
    _, kwargs = mock_write_api.write.call_args
    assert kwargs["bucket"] == influx_sink.INFLUX_BUCKET


@patch("influx_sink.InfluxDBClient")
def test_write_sends_correct_point_count(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    rows = [make_row(), make_row(alert_type="PU1_STUCK_ON"), make_row(ATT_FLAG=1)]
    write_to_influx(make_batch(*rows), batch_id=2)
    _, kwargs = mock_write_api.write.call_args
    assert len(kwargs["record"]) == 3


@patch("influx_sink.InfluxDBClient")
def test_point_has_measurement_water_telemetry(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row()), batch_id=3)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert line.startswith("water_telemetry")


@patch("influx_sink.InfluxDBClient")
def test_point_has_alert_type_tag(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(alert_type="PU1_STUCK_ON")), batch_id=4)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "alert_type=PU1_STUCK_ON" in line


@patch("influx_sink.InfluxDBClient")
def test_point_has_l_t1_field(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(L_T1=4.567)), batch_id=5)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "L_T1=" in line


@patch("influx_sink.InfluxDBClient")
def test_point_has_att_flag_field(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(ATT_FLAG=1)), batch_id=6)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "ATT_FLAG=" in line


@patch("influx_sink.InfluxDBClient")
def test_point_has_disp_fields(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(disp_PU1=2, disp_PU2=1, disp_PU3=0)), batch_id=7)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "disp_PU1=" in line
    assert "disp_PU2=" in line
    assert "disp_PU3=" in line


@patch("influx_sink.InfluxDBClient")
def test_point_has_event_time_field(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(timestamp="2016-09-14T03:00:00Z")), batch_id=8)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "event_time=" in line


@patch("influx_sink.InfluxDBClient")
def test_point_has_timestamp_ns(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row()), batch_id=9)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    parts = line.rsplit(" ", 1)
    assert len(parts) == 2
    assert parts[1].isdigit(), f"Timestamp không phải số nguyên ns: '{parts[1]}'"


@patch("influx_sink.InfluxDBClient")
def test_none_float_field_is_skipped(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(L_T2=None)), batch_id=10)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "L_T2=" not in line


@patch("influx_sink.InfluxDBClient")
def test_none_int_field_is_skipped(mock_client_cls):
    mock_write_api = MagicMock()
    mock_client_cls.return_value.write_api.return_value = mock_write_api
    write_to_influx(make_batch(make_row(S_PU2=None)), batch_id=11)
    _, kwargs = mock_write_api.write.call_args
    line = kwargs["record"][0].to_line_protocol()
    assert "S_PU2=" not in line


@patch("influx_sink.InfluxDBClient")
def test_client_is_closed_after_write(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.write_api.return_value = MagicMock()
    write_to_influx(make_batch(make_row()), batch_id=12)
    mock_client.close.assert_called_once()


@patch("influx_sink.InfluxDBClient")
def test_influx_url_passed_to_client(mock_client_cls):
    mock_client_cls.return_value.write_api.return_value = MagicMock()
    write_to_influx(make_batch(make_row()), batch_id=13)
    _, kwargs = mock_client_cls.call_args
    assert (
        kwargs.get("url") == influx_sink.INFLUX_URL
        or mock_client_cls.call_args[0][0] == influx_sink.INFLUX_URL
        or "url" in str(mock_client_cls.call_args)
    )
