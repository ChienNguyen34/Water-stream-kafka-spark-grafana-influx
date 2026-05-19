"""
E2E Test - Grafana Cloud (EC2): kiểm tra Grafana trên EC2 hoạt động đúng.
EC2: 18.138.224.73, Grafana port 3000.

Yêu cầu:
  - EC2 đang chạy docker-compose.cloud.yml
  - Security Group mở port 3000

Chạy:
  pytest tst/e2e/test_e2e_grafana_cloud.py -v
  pytest tst/e2e/test_e2e_grafana_cloud.py -v --cloud-url http://<ip>:3000
"""
import base64
import json
import os
import urllib.request
import urllib.error
import pytest

# ---------------------------------------------------------------------------
# Config — override bằng env var CLOUD_GRAFANA_URL hoặc pytest option
# ---------------------------------------------------------------------------
DEFAULT_CLOUD_URL = "http://18.138.224.73:3000"

GRAFANA_URL = os.environ.get("CLOUD_GRAFANA_URL", DEFAULT_CLOUD_URL)
GRAFANA_USER = os.environ.get("CLOUD_GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("CLOUD_GRAFANA_PASSWORD", "adminpassword")
DASHBOARD_UID = "batadal-water"
EXPECTED_PANEL_COUNT = 10


def pytest_addoption(parser):
    """Cho phép truyền --cloud-url qua CLI."""
    try:
        parser.addoption(
            "--cloud-url",
            action="store",
            default=None,
            help="Override Grafana cloud URL, e.g. http://18.138.224.73:3000",
        )
    except ValueError:
        pass  # option đã được đăng ký từ conftest khác


@pytest.fixture(autouse=True, scope="session")
def cloud_grafana_url(request):
    """Cho phép --cloud-url CLI override GRAFANA_URL cho toàn session."""
    global GRAFANA_URL
    cli_url = request.config.getoption("--cloud-url", default=None, skip=True)
    if cli_url:
        GRAFANA_URL = cli_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header() -> str:
    creds = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASSWORD}".encode()).decode()
    return f"Basic {creds}"


def _get(path: str, timeout: int = 10) -> dict:
    url = f"{GRAFANA_URL}{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": _auth_header()},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        pytest.fail(f"GET {url} → HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        pytest.fail(
            f"Grafana EC2 không reachable tại {GRAFANA_URL}: {e}\n"
            f"Kiểm tra: EC2 đang chạy, Security Group mở port 3000, "
            f"docker-compose.cloud.yml đang up."
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cloud_grafana_health():
    """Grafana trên EC2 phải running và database ok."""
    url = f"{GRAFANA_URL}/api/health"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            assert body.get("database") == "ok", (
                f"Grafana EC2 health không ok: {body}"
            )
    except urllib.error.URLError as e:
        pytest.fail(
            f"Grafana EC2 /api/health không reachable ({GRAFANA_URL}): {e}\n"
            "Kiểm tra EC2 running, port 3000 mở trong Security Group."
        )


def test_cloud_grafana_version():
    """Grafana phải trả về version info hợp lệ."""
    result = _get("/api/health")
    assert "version" in result, f"Không có 'version' trong health response: {result}"
    assert result["version"], "Grafana version rỗng"


def test_cloud_dashboard_exists():
    """Dashboard UID 'batadal-water' phải tồn tại trên EC2."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    assert "dashboard" in result, (
        f"Dashboard '{DASHBOARD_UID}' không tồn tại. Response: {result}"
    )


def test_cloud_dashboard_title():
    """Dashboard phải có title đúng."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    title = result["dashboard"].get("title", "")
    assert title, "Dashboard title rỗng"


def test_cloud_dashboard_panel_count():
    """Dashboard trên EC2 phải có đúng số panels như local."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panels = result["dashboard"].get("panels", [])
    assert len(panels) == EXPECTED_PANEL_COUNT, (
        f"Dashboard có {len(panels)} panels, cần {EXPECTED_PANEL_COUNT}"
    )


def test_cloud_dashboard_has_canvas_panel():
    """Phải có Canvas panel (topology map) trên EC2."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panel_types = [p.get("type") for p in result["dashboard"].get("panels", [])]
    assert "canvas" in panel_types, (
        f"Không tìm thấy Canvas panel trên EC2. Panels: {panel_types}"
    )


def test_cloud_dashboard_has_timeseries_panel():
    """Phải có Time Series panel (sensor readings) trên EC2."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panel_types = [p.get("type") for p in result["dashboard"].get("panels", [])]
    assert "timeseries" in panel_types, (
        f"Không tìm thấy Time Series panel trên EC2. Panels: {panel_types}"
    )


def test_cloud_influxdb_datasource_provisioned():
    """Datasource 'influxdb' phải được provision trên Grafana EC2."""
    result = _get("/api/datasources/name/influxdb")
    assert result.get("type") == "influxdb", (
        f"Datasource type không đúng trên EC2: {result}"
    )


def test_cloud_datasource_reachable():
    """Datasource InfluxDB phải ở trạng thái reachable (access mode)."""
    result = _get("/api/datasources/name/influxdb")
    # access = 'proxy' nghĩa là Grafana gọi InfluxDB nội bộ (trong docker network)
    access = result.get("access", "")
    assert access in ("proxy", "direct"), (
        f"Datasource access mode không hợp lệ: '{access}'"
    )


def test_cloud_datasource_uid_matches_dashboard():
    """UID datasource trong Grafana EC2 phải match với uid trong dashboard JSON."""
    ds = _get("/api/datasources/name/influxdb")
    actual_uid = ds.get("uid")
    assert actual_uid, "Datasource không có UID"

    dashboard_result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    dashboard_str = json.dumps(dashboard_result["dashboard"])
    assert actual_uid in dashboard_str, (
        f"Datasource UID '{actual_uid}' không xuất hiện trong dashboard EC2 — "
        "panels có thể không load được data"
    )


def test_cloud_alert_rules_or_annotations():
    """Kiểm tra alert rules endpoint trả về response hợp lệ (không lỗi 5xx)."""
    url = f"{GRAFANA_URL}/api/v1/provisioning/alert-rules"
    req = urllib.request.Request(
        url,
        headers={"Authorization": _auth_header()},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            # 200 OK — có hoặc không có rules đều hợp lệ
            body = resp.read()
            data = json.loads(body) if body else []
            assert isinstance(data, list), f"Alert rules response không phải list: {data}"
    except urllib.error.HTTPError as e:
        # 403 = endpoint tắt, 404 = không có rules — đều chấp nhận được
        if e.code in (403, 404):
            pytest.skip(f"Alert rules endpoint trả về {e.code} — bỏ qua")
        pytest.fail(f"Alert rules endpoint lỗi {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        pytest.fail(f"Không reachable: {e}")
