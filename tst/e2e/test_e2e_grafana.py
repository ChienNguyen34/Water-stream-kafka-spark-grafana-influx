"""
E2E Test - Grafana: kiểm tra dashboard tồn tại và data panels trả về data
thông qua Grafana HTTP API.
Yêu cầu: Grafana đang chạy (docker-compose up -d).
Chạy: pytest tst/e2e/test_e2e_grafana.py -v
"""
import base64
import json
import urllib.request
import urllib.error
import pytest

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "adminpassword"
DASHBOARD_UID = "batadal-water"
EXPECTED_PANEL_COUNT = 10


def _auth_header() -> str:
    creds = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASSWORD}".encode()).decode()
    return f"Basic {creds}"


def _get(path: str, timeout: int = 5) -> dict:
    req = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        headers={"Authorization": _auth_header()},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        pytest.fail(f"GET {path} → HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        pytest.fail(f"Grafana không reachable tại {GRAFANA_URL}: {e}")


# ---------------------------------------------------------------------------

def test_grafana_health():
    """Grafana phải running và database ok."""
    try:
        with urllib.request.urlopen(f"{GRAFANA_URL}/api/health", timeout=5) as resp:
            body = json.loads(resp.read())
            assert body.get("database") == "ok", f"Grafana health: {body}"
    except urllib.error.URLError as e:
        pytest.fail(f"Grafana /api/health không reachable: {e}")


def test_dashboard_exists():
    """Dashboard với UID 'batadal-water' phải tồn tại."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    assert "dashboard" in result, f"Response không chứa 'dashboard' key: {result}"


def test_dashboard_has_correct_panel_count():
    """Dashboard phải có đúng {EXPECTED_PANEL_COUNT} panels."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panels = result["dashboard"].get("panels", [])
    assert len(panels) == EXPECTED_PANEL_COUNT, (
        f"Dashboard có {len(panels)} panels, cần {EXPECTED_PANEL_COUNT}"
    )


def test_dashboard_has_canvas_panel():
    """Phải có Canvas panel (topology map)."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panel_types = [p.get("type") for p in result["dashboard"].get("panels", [])]
    assert "canvas" in panel_types, f"Không tìm thấy Canvas panel. Panels: {panel_types}"


def test_dashboard_has_timeseries_panel():
    """Phải có Time Series panel (tank levels)."""
    result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    panel_types = [p.get("type") for p in result["dashboard"].get("panels", [])]
    assert "timeseries" in panel_types, f"Không tìm thấy Time Series panel. Panels: {panel_types}"


def test_influxdb_datasource_provisioned():
    """Datasource 'influxdb' phải được Grafana nhận diện."""
    result = _get("/api/datasources/name/influxdb")
    assert result.get("type") == "influxdb", f"Datasource type không đúng: {result}"


def test_datasource_uid_matches_dashboard():
    """UID datasource trong Grafana phải match với uid trong dashboard JSON."""
    ds = _get("/api/datasources/name/influxdb")
    actual_uid = ds.get("uid")

    dashboard_result = _get(f"/api/dashboards/uid/{DASHBOARD_UID}")
    dashboard_str = json.dumps(dashboard_result["dashboard"])
    assert actual_uid in dashboard_str, (
        f"Datasource UID '{actual_uid}' không xuất hiện trong dashboard — "
        "panels có thể không load được data"
    )
