"""
E2E Test - Data Flow: kiểm tra dữ liệu đang chảy qua pipeline
Python Generator → Kafka → Spark → InfluxDB.
Yêu cầu: toàn bộ pipeline đang chạy (docker-compose up -d + spark-submit).
Chạy: pytest tst/e2e/test_e2e_dataflow.py -v
"""
import json
import urllib.request
import urllib.error
import pytest

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-super-secret-token"
INFLUX_ORG = "bigdata"
INFLUX_BUCKET = "water_bucket"
MEASUREMENT = "water_telemetry"


def _flux_query(query: str) -> str:
    """Gửi Flux query đến InfluxDB, trả về response body (CSV)."""
    url = f"{INFLUX_URL}/api/v2/query?org={INFLUX_ORG}"
    data = query.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Token {INFLUX_TOKEN}",
            "Content-Type": "application/vnd.flux",
            "Accept": "application/csv",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        pytest.fail(f"InfluxDB query thất bại: {e}")


def _parse_csv_rows(csv_text: str) -> list[str]:
    """Lọc bỏ comment lines (#) và header, trả về data rows."""
    return [
        line for line in csv_text.strip().splitlines()
        if line and not line.startswith("#") and not line.startswith(",result")
    ]


def _parse_count_from_csv(csv_text: str) -> int:
    """
    Parse giá trị count từ kết quả Flux |> count().
    Tìm đúng cột _value thay vì lấy cột cuối cùng (có thể là tag string).
    """
    lines = [l for l in csv_text.strip().splitlines() if l and not l.startswith("#")]
    if len(lines) < 2:
        return 0

    # Tìm header row (dòng bắt đầu bằng ",result" hoặc chứa "_value")
    header_line = None
    data_lines = []
    for line in lines:
        if "_value" in line and header_line is None:
            header_line = line
        elif header_line is not None:
            data_lines.append(line)

    if not header_line or not data_lines:
        return 0

    headers = header_line.split(",")
    try:
        value_idx = headers.index("_value")
    except ValueError:
        return 0

    last_row = data_lines[-1].split(",")
    if value_idx >= len(last_row):
        return 0

    try:
        return int(last_row[value_idx].strip())
    except ValueError:
        return 0


# ---------------------------------------------------------------------------

def test_influxdb_reachable():
    """InfluxDB phải accessible trước khi chạy các E2E test."""
    try:
        with urllib.request.urlopen(f"{INFLUX_URL}/health", timeout=5) as resp:
            body = json.loads(resp.read())
            assert body["status"] == "pass"
    except urllib.error.URLError as e:
        pytest.fail(f"InfluxDB không reachable: {e}")


def test_water_telemetry_has_recent_data():
    """Pipeline phải có ít nhất 1 record trong 60 giây qua."""
    csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -60s)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> limit(n: 1)
''')
    rows = _parse_csv_rows(csv)
    assert len(rows) > 0, (
        "Không có data trong water_telemetry 60s gần nhất. "
        "Kiểm tra Spark và Generator có đang chạy không?"
    )


def test_l_t1_field_present_in_influx():
    """Field L_T1 phải tồn tại trong measurement (last 5 phút)."""
    csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}" and r._field == "L_T1")
  |> limit(n: 1)
''')
    rows = _parse_csv_rows(csv)
    assert len(rows) > 0, "Field L_T1 không có trong InfluxDB"


def test_alert_type_tag_exists():
    """Tag alert_type phải được ghi vào InfluxDB."""
    csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> keep(columns: ["alert_type", "_time", "_value", "_field"])
  |> limit(n: 1)
''')
    assert "alert_type" in csv, "Tag 'alert_type' không có trong InfluxDB response"


def test_disp_pu_fields_present():
    """disp_PU1, disp_PU2, disp_PU3 phải được ghi vào InfluxDB."""
    for field in ["disp_PU1", "disp_PU2", "disp_PU3"]:
        csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}" and r._field == "{field}")
  |> limit(n: 1)
''')
        rows = _parse_csv_rows(csv)
        assert len(rows) > 0, f"Field '{field}' không có trong InfluxDB"


def test_att_flag_field_present():
    """ATT_FLAG (ground truth) phải được lưu trong InfluxDB."""
    csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}" and r._field == "ATT_FLAG")
  |> limit(n: 1)
''')
    rows = _parse_csv_rows(csv)
    assert len(rows) > 0, "Field 'ATT_FLAG' không có trong InfluxDB"


def test_throughput_minimum_10_records_per_minute():
    """Pipeline phải xử lý ít nhất 10 records/phút (smoke check)."""
    csv = _flux_query(f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -1m)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}" and r._field == "L_T1")
  |> count()
''')
    count_value = _parse_count_from_csv(csv)
    assert count_value > 0, "Không đếm được records trong 1 phút qua"
    assert count_value >= 10, (
        f"Throughput quá thấp: chỉ có {count_value} records/phút (cần >= 10)"
    )
