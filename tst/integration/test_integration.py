"""
Integration Test: kiểm tra tất cả containers đang chạy, healthy, cùng network, port reachable.
Yêu cầu: docker-compose up -d đã chạy trước.
Chạy: pytest tst/integration/test_integration.py -v
"""
import json
import socket
import subprocess
import pytest


COMPOSE_PROJECT = "bigdata"
EXPECTED_NETWORK = f"{COMPOSE_PROJECT}_default"

REQUIRED_CONTAINERS = ["kafka", "influxdb", "grafana", "spark-master", "spark-worker-1", "spark-driver", "generator"]
HEALTHCHECKED_CONTAINERS = ["kafka", "influxdb"]

HOST_PORTS = [
    ("localhost", 9092, "Kafka"),
    ("localhost", 8086, "InfluxDB"),
    ("localhost", 3000, "Grafana"),
]


def _docker_ps() -> list[dict]:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{json .}}"],
        capture_output=True, text=True, check=True,
    )
    return [json.loads(line) for line in result.stdout.strip().splitlines() if line]


# ---------------------------------------------------------------------------

def test_all_required_containers_running():
    """Tất cả containers trong docker-compose phải đang Up."""
    containers = _docker_ps()
    running_names = [c["Names"] for c in containers]
    missing = [s for s in REQUIRED_CONTAINERS if not any(s in n for n in running_names)]
    assert not missing, f"Containers chưa chạy: {missing}"


def test_no_unhealthy_containers():
    """Không được có container nào ở trạng thái unhealthy."""
    result = subprocess.run(
        ["docker", "ps", "--filter", "health=unhealthy", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=True,
    )
    unhealthy = result.stdout.strip()
    assert unhealthy == "", f"Containers unhealthy: {unhealthy}"


def test_healthchecked_containers_are_healthy():
    """Kafka và InfluxDB phải có healthcheck status = healthy."""
    for container in HEALTHCHECKED_CONTAINERS:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
            capture_output=True, text=True,
        )
        status = result.stdout.strip()
        assert status == "healthy", (
            f"Container '{container}' health status: '{status}' (expected 'healthy')"
        )


def test_all_containers_on_same_network():
    """Tất cả service containers phải cùng 1 Docker network."""
    result = subprocess.run(
        ["docker", "network", "inspect", EXPECTED_NETWORK, "--format", "{{json .Containers}}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"Network '{EXPECTED_NETWORK}' không tồn tại. "
        f"Chắc chắn docker-compose up đã chạy chưa?"
    )
    containers_in_network = json.loads(result.stdout.strip())
    names_in_network = [v["Name"] for v in containers_in_network.values()]
    for service in ["kafka", "influxdb", "grafana"]:
        assert any(service in n for n in names_in_network), (
            f"Container '{service}' không nằm trong network '{EXPECTED_NETWORK}'"
        )


@pytest.mark.parametrize("host,port,label", HOST_PORTS)
def test_port_reachable_from_host(host, port, label):
    """Các port expose ra host phải connect được trong 5 giây."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    sock.close()
    assert result == 0, f"{label} port {port} không reachable từ host (error code: {result})"


def test_influxdb_http_health():
    """InfluxDB HTTP /health endpoint phải trả về status=pass."""
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen("http://localhost:8086/health", timeout=5) as resp:
            body = json.loads(resp.read())
            assert body["status"] == "pass", f"InfluxDB health: {body}"
    except urllib.error.URLError as e:
        pytest.fail(f"InfluxDB /health không reachable: {e}")


def test_grafana_http_health():
    """Grafana HTTP /api/health endpoint phải trả về database=ok."""
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen("http://localhost:3000/api/health", timeout=5) as resp:
            body = json.loads(resp.read())
            assert body.get("database") == "ok", f"Grafana health: {body}"
    except urllib.error.URLError as e:
        pytest.fail(f"Grafana /api/health không reachable: {e}")
