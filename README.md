# BATADAL Big Data Pipeline

Real-time anomaly detection pipeline for water distribution network (BATADAL dataset) using Apache Kafka, Apache Spark Structured Streaming, InfluxDB, and Grafana — fully containerized with Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Dataset (BATADAL CSV)                                              │
│        │                                                            │
│        ▼                                                            │
│  ┌──────────────┐    JSON     ┌─────────┐                          │
│  │  Generator   │────────────▶│  Kafka  │  topic: water_stream     │
│  │  (producer/) │             │  :9092  │                          │
│  └──────────────┘             └────┬────┘                          │
│                                    │                                │
│                                    ▼                                │
│                         ┌──────────────────┐                       │
│                         │  Spark Driver    │  Structured Streaming  │
│                         │  + 2 Workers     │  + ML (IsolationForest)│
│                         └────────┬─────────┘                       │
│                                  │ write                            │
│                                  ▼                                  │
│                         ┌────────────────┐   ┌──────────────────┐  │
│                         │   InfluxDB 2   │──▶│    Grafana       │  │
│                         │    :8086       │   │    :3000         │  │
│                         └────────────────┘   └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Data flow:** CSV → Generator → Kafka → Spark (rule-based + ML alert) → InfluxDB → Grafana dashboard

---

## Tech Stack

| Component | Technology | Version |
|---|---|---|
| Message Broker | Apache Kafka (KRaft mode) | `confluentinc/cp-kafka:8.1.2` |
| Stream Processing | Apache Spark Structured Streaming | `3.5.8` |
| Time-series DB | InfluxDB | `influxdb:2` |
| Visualization | Grafana | `13.0.1` |
| Data Generator | Python + confluent-kafka | — |
| ML Model | scikit-learn IsolationForest | `≥1.4.0` |
| Container Runtime | Docker + Docker Compose | — |

---

## Project Structure

```
.
├── docker-compose.yml          # Full local deployment
├── docker-compose.cloud.yml    # Cloud deployment (Kafka+InfluxDB+Grafana on EC2)
├── requirements.txt            # Python dependencies
│
├── producer/                   # Data generator service
│   ├── producer.py             # Main Kafka producer loop
│   ├── data_loader.py          # Load & validate BATADAL CSV
│   ├── payload_builder.py      # Build JSON payloads
│   ├── config.py               # Env-based config
│   └── Dockerfile
│
├── spark_streaming/            # Spark Structured Streaming service
│   ├── stream_processor.py     # Main Spark job (consume → alert → write)
│   ├── influx_sink.py          # InfluxDB writer (foreachBatch)
│   ├── train_model.py          # Train IsolationForest offline
│   ├── anomaly_model.pkl       # Trained model artifact
│   └── Dockerfile
│
├── grafana/
│   ├── provisioning/           # Auto-provisioned datasource & dashboard
│   └── dashboards/             # Dashboard JSON (UID: batadal-water)
│
├── dataset/
│   ├── BATADAL_dataset03.csv   # Training data
│   ├── BATADAL_dataset04.csv   # Test data (with attack labels)
│   └── CTOWN.INP               # EPANET network model
│
├── tst/
│   ├── unit/                   # Unit tests (65 tests)
│   ├── integration/            # Integration tests (Docker required)
│   ├── e2e/                    # End-to-end tests (full pipeline required)
│   ├── conftest.py             # Shared pytest fixtures
│   ├── security_risk_register.md
│   └── README.md
│
├── doc/
│   ├── Cloud_Deployment.md     # AWS EC2 deployment guide
│   ├── Docker_Compose_Explained.md
│   ├── Dataset_Description.md
│   └── Requirement_engineering.md
│
├── deploy_cloud.ps1            # Automated EC2 deploy script (Windows)
├── start_pipeline.ps1          # Local pipeline startup script (Windows)
└── trivy_scan.ps1              # Container security scan script
```

---

## Quick Start (Local)

### Prerequisites

- Docker Desktop
- Python 3.10+
- Windows (scripts use PowerShell) or adapt commands for Linux/macOS

### 1. Clone & setup

```bash
git clone <repo-url>
cd Bigdata
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Start full pipeline

```powershell
.\start_pipeline.ps1
```

Or manually:

```powershell
# Start infrastructure
docker-compose up -d kafka influxdb grafana

# Wait for Kafka to be healthy, then start Spark + Generator
docker-compose up -d spark-master spark-worker spark-worker-2 spark-driver generator
```

### 3. Access services

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3000 | admin / adminpassword |
| InfluxDB | http://localhost:8086 | admin / adminpassword |
| Spark Master UI | http://localhost:8090 | — |

---

## Dataset

**BATADAL** (BATtle of the water treatment ALgorithms) — a water distribution network dataset from the C-TOWN benchmark network.

| File | Description |
|---|---|
| `BATADAL_dataset03.csv` | Normal operation data (training) |
| `BATADAL_dataset04.csv` | Data with cyber-attack labels (`ATT_FLAG`) |

**Sensors:** 7 tank levels (L_T1–L_T7), 11 pump flows (F_PU1–F_PU11), 11 pump statuses (S_PU1–S_PU11), 1 valve (F_V2, S_V2)

**Attack label:** `ATT_FLAG = 1` → attack, `ATT_FLAG = -1` → normal

---

## Alert Logic

The pipeline uses **two complementary detection methods**:

### Rule-based
```
pump pressure P_J415 > 60  →  PRESSURE_HIGH alert
```

### ML-based (IsolationForest)
```
IsolationForest trained on normal data (dataset03)
Anomaly score threshold: -0.1
Prediction -1 → ML_ANOMALY alert
```

Alerts are tagged `alert_type` in InfluxDB:
- `NORMAL`
- `PRESSURE_HIGH`
- `ML_ANOMALY`

---

## Running Tests

```powershell
# Activate venv first
venv\Scripts\activate

# Unit tests only (no Docker required)
pytest tst/unit/ -v --cov=producer --cov=spark_streaming --cov-report=term-missing

# Integration tests (requires docker-compose up)
pytest tst/integration/ -v

# E2E tests (requires full pipeline running + data flowing)
pytest tst/e2e/ -v

# All tests
pytest tst/ -v
```

See [tst/README.md](tst/README.md) for detailed test documentation.

---

## Cloud Deployment (AWS EC2 — Hybrid Mode)

Kafka + InfluxDB + Grafana run on EC2; Spark + Generator run locally.

```powershell
# Deploy to EC2 (requires batadal-key_new.pem)
.\deploy_cloud.ps1
```

See [doc/Cloud_Deployment.md](doc/Cloud_Deployment.md) for full guide including SSH tunnel setup, Security Group config, and troubleshooting.

---

## Security

Container vulnerability scans are run with [Trivy](https://trivy.dev/):

```powershell
.\trivy_scan.ps1
# Report saved to tst/trivy_report.txt
```

Known CVEs are documented and risk-assessed in [tst/security_risk_register.md](tst/security_risk_register.md).

---

## Configuration

Key environment variables (set in `docker-compose.yml` or `.env`):

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BROKER` | `kafka:29092` | Kafka bootstrap server |
| `KAFKA_TOPIC` | `water_stream` | Kafka topic name |
| `INFLUX_URL` | `http://influxdb:8086` | InfluxDB endpoint |
| `INFLUX_TOKEN` | `my-super-secret-token` | InfluxDB auth token |
| `INFLUX_ORG` | `bigdata` | InfluxDB organization |
| `INFLUX_BUCKET` | `water_bucket` | InfluxDB bucket |
| `COMPRESSION_FACTOR` | `180000` | Generator speed (lower = faster) |

---

## License

This project is for academic/educational purposes using the public BATADAL dataset.
