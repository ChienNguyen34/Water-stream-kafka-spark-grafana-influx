# Test Suite — BATADAL Water Network Pipeline

## Cấu trúc

```
tst/
  conftest.py              ← tự động thêm producer/ và spark_streaming/ vào sys.path
  unit/                    ← test logic thuần Python, không cần Docker
  integration/             ← test containers đang chạy và kết nối được
  e2e/                     ← test dữ liệu chảy xuyên suốt pipeline
trivy_scan.ps1             ← security scan (chạy riêng, không phải pytest)
```

---

## Unit Tests (`tst/unit/`)

**Không cần Docker. Chạy offline hoàn toàn.**

| File | Mô tả | Số test |
|------|--------|---------|
| `test_data_loader.py` | Parse timestamp, load CSV, kiểu dữ liệu, ATT_FLAG | 15 |
| `test_payload_builder.py` | JSON payload structure, types, round, NaN-free | 16 |
| `test_alert_logic.py` | Rule-based alert + disp_PUx logic (pure Python mirror of Spark) | 17 |
| `test_influx_sink.py` | InfluxDB write logic, Point fields/tags/timestamp (mock) | 14 |

```powershell
# Chạy tất cả unit tests
cd d:\Workspace\Bigdata
& venv\Scripts\pytest.exe tst\unit\ -v

# Với coverage report (cần pytest-cov)
& venv\Scripts\pip.exe install pytest-cov
& venv\Scripts\pytest.exe tst\unit\ -v `
    --cov=producer `
    --cov=spark_streaming `
    --cov-report=term-missing `
    --cov-fail-under=80
```

---

## Integration Tests (`tst/integration/`)

**Yêu cầu: `docker-compose up -d` đã chạy thành công.**

| Test | Kiểm tra gì |
|------|-------------|
| `test_all_required_containers_running` | kafka, influxdb, grafana, spark-master, spark-worker-1, spark-driver, generator đều Up |
| `test_no_unhealthy_containers` | Không có container nào ở trạng thái `unhealthy` |
| `test_healthchecked_containers_are_healthy` | kafka và influxdb healthcheck = `healthy` |
| `test_all_containers_on_same_network` | Tất cả service nằm trong `bigdata_default` network |
| `test_port_reachable_from_host` | Port 9092 (Kafka), 8086 (InfluxDB), 3000 (Grafana) connect được từ host |
| `test_influxdb_http_health` | `/health` endpoint trả về `status=pass` |
| `test_grafana_http_health` | `/api/health` endpoint trả về `database=ok` |

```powershell
# Khởi động hệ thống trước
docker-compose up -d

# Chạy integration tests
& venv\Scripts\pytest.exe tst\integration\ -v
```

---

## E2E Tests (`tst/e2e/`)

**Yêu cầu: Toàn bộ pipeline đang chạy — bao gồm Spark đang stream và Generator đang sinh data.**

### test_e2e_dataflow.py — Kiểm tra dữ liệu trong InfluxDB

| Test | Kiểm tra gì |
|------|-------------|
| `test_influxdb_reachable` | InfluxDB HTTP accessible |
| `test_water_telemetry_has_recent_data` | Có ít nhất 1 record trong 60 giây qua |
| `test_l_t1_field_present_in_influx` | Field `L_T1` tồn tại trong 5 phút qua |
| `test_alert_type_tag_exists` | Tag `alert_type` được ghi vào InfluxDB |
| `test_disp_pu_fields_present` | `disp_PU1`, `disp_PU2`, `disp_PU3` tồn tại |
| `test_att_flag_field_present` | Field `ATT_FLAG` (ground truth) tồn tại |
| `test_throughput_minimum_10_records_per_minute` | ≥ 10 records/phút |

### test_e2e_grafana.py — Kiểm tra Grafana dashboard qua API

| Test | Kiểm tra gì |
|------|-------------|
| `test_grafana_health` | Grafana running, database ok |
| `test_dashboard_exists` | Dashboard UID `batadal-water` tồn tại |
| `test_dashboard_has_correct_panel_count` | Đúng 3 panels |
| `test_dashboard_has_canvas_panel` | Có Canvas panel (topology map) |
| `test_dashboard_has_timeseries_panel` | Có Time Series panel (tank levels) |
| `test_influxdb_datasource_provisioned` | Datasource `influxdb` được Grafana nhận diện |
| `test_datasource_uid_matches_dashboard` | UID datasource khớp với dashboard JSON |

```powershell
# Chạy tất cả E2E tests
& venv\Scripts\pytest.exe tst\e2e\ -v

# Chạy từng file riêng
& venv\Scripts\pytest.exe tst\e2e\test_e2e_dataflow.py -v
& venv\Scripts\pytest.exe tst\e2e\test_e2e_grafana.py -v
```

---

## Security Scan (Trivy)

**Không dùng pytest. Chạy script PowerShell riêng.**

Script scan 3 pre-built images (`cp-kafka:8.1.2`, `influxdb:2`, `grafana:13.0.1`) bằng Trivy container — không cần cài Trivy trên host.

- Fail nếu tìm thấy lỗ hổng mức **CRITICAL**
- Report lưu tại `tst/trivy_report.txt`

```powershell
cd d:\Workspace\Bigdata
.\trivy_scan.ps1
```

> **Lưu ý:** Image tự build (`spark-master`, `spark-worker`, `spark-driver`, `generator`) không scan vì dùng `build:` context, không phải pre-built image từ registry.

---

## Chạy toàn bộ (theo thứ tự)

```powershell
# 1. Unit tests (offline)
& venv\Scripts\pytest.exe tst\unit\ -v --cov=producer --cov=spark_streaming --cov-fail-under=80

# 2. Security scan
.\trivy_scan.ps1

# 3. Khởi động hệ thống
docker-compose up -d

# 4. Integration tests
& venv\Scripts\pytest.exe tst\integration\ -v

# 5. E2E tests (sau khi Spark đang stream ~30 giây)
& venv\Scripts\pytest.exe tst\e2e\ -v
```
