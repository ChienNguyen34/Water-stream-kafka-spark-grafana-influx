# Security Risk Register — BATADAL Water Network Pipeline
**Scan date:** 2026-05-13  
**Tool:** Trivy 0.61.0  
**Severity filter:** HIGH, CRITICAL  
**Assessed by:** DevSecOps review  
**Policy:** CRITICAL findings must be triaged. Findings in upstream vendor images are accepted risk pending vendor patch.

---

## 1. Scan Summary

| Image | Role | CRITICAL | HIGH | Overall Result | Risk Decision |
|-------|------|----------|------|----------------|---------------|
| `confluentinc/cp-kafka:8.1.2` | Message broker | **0** | 18 | ✅ PASS | Accept — OS packages, vendor-owned |
| `influxdb:2` | Time-series DB | **4** | 16 | ⚠️ MONITOR | Accept — no fix available for most |
| `grafana/grafana:13.0.1` | Visualization | **4** | 12+16 | ⚠️ MONITOR | Accept — Golang stdlib, grafana-owned |
| `apache/spark:3.5.8-java17-python3` | Spark base | **4** | 43 | ⚠️ MONITOR | Accept — Hadoop/Avro/Derby, upstream |
| `bigdata-spark-master` (local build) | Spark master | **4** | 43 | ⚠️ MONITOR | Inherited from spark base image |
| `bigdata-spark-worker` (local build) | Spark worker | **4** | 43 | ⚠️ MONITOR | Inherited from spark base image |
| `bigdata-spark-driver` (local build) | Spark driver | **4** | 43 | ⚠️ MONITOR | Inherited from spark base image |
| `bigdata-generator` (local build) | Data producer | **0** | 2 | ✅ PASS | Accept — low exposure, internal only |

**Total unique CRITICAL CVEs (deduplicated):** 8  
**Total unique HIGH CVEs (deduplicated):** ~50+

---

## 2. CRITICAL Findings — Triage Detail

### 2.1 `influxdb:2` — 4 CRITICAL

| CVE | Package | Status | Description | Triage Decision |
|-----|---------|--------|-------------|-----------------|
| CVE-2026-33845 | libgnutls30 | no fix | GnuTLS: DoS via DTLS zero-length | **ACCEPT** — InfluxDB không dùng DTLS. Port 8086 không expose ra internet trong setup này. |
| CVE-2025-7458 | libsqlite3-0 | no fix | SQLite integer overflow | **ACCEPT** — SQLite dùng internal bởi InfluxDB. Không có user input path trực tiếp. |
| CVE-2023-45853 | zlib1g | will_not_fix | Integer overflow → heap buffer overflow | **ACCEPT** — Vendor đánh dấu `will_not_fix`. Không thể fix nếu không đổi base image. |
| CVE-2025-68121 | stdlib (Go) | fixed: 1.24.13 | crypto/tls: Incorrect cert validation | **MONITOR** — Cần InfluxDB release bản mới build trên Go 1.24.13+. Theo dõi release. |

### 2.2 `grafana/grafana:13.0.1` — CRITICAL

| CVE | Package | Status | Description | Triage Decision |
|-----|---------|--------|-------------|-----------------|
| CVE-2025-68121 | stdlib (Go) | fixed: 1.24.13 | crypto/tls: Incorrect cert validation | **MONITOR** — Cần Grafana release bản mới. Port 3000 chỉ dùng nội bộ. |
| CVE-2024-24790 | stdlib (Go) | fixed: 1.21.11 | net/netip: Unexpected behavior from Is methods | **MONITOR** — Logic bug, không phải RCE. Low exploitability trong context này. |
| CVE-2026-33186 | google.golang.org/grpc | no fix | gRPC-Go vulnerability | **ACCEPT** — Grafana dùng gRPC internal. Không expose gRPC port ra ngoài. |
| CVE-2026-31789 | libcrypto3 / libssl3 | fixed: 3.5.6 | OpenSSL: Heap buffer overflow (32-bit only) | **ACCEPT** — Deployment trên 64-bit. Không ảnh hưởng. |
| CVE-2026-33816 | github.com/jackc/pgx/v5 | fixed: 5.9.0 | PostgreSQL driver memory-safety | **MONITOR** — Grafana dùng pgx để đọc config. Theo dõi Grafana upgrade. |

### 2.3 `apache/spark:3.5.8` + local Spark images — 4 CRITICAL (lặp lại qua các image)

| CVE | Package | Status | Description | Triage Decision |
|-----|---------|--------|-------------|-----------------|
| CVE-2024-47561 | apache-avro 1.7.7 | fixed: 1.11.4 | **Schema parsing → RCE** | **MONITOR** — Spark dùng Avro qua Hadoop client. Không deserialize schema từ nguồn untrusted trong pipeline này. Risk giảm. |
| CVE-2022-46337 | apache-derby 10.14.2 | fixed: 10.16+ | LDAP Authentication Bypass | **ACCEPT** — Derby chỉ dùng làm embedded metadata store trong Spark. Không có LDAP configured. Không expose Derby port. |
| CVE-2023-44981 | zookeeper 3.6.3 | fixed: 3.7.2 | Authorization Bypass | **ACCEPT** — Project dùng Kafka KRaft mode (không dùng ZooKeeper). ZooKeeper JAR có trong Hadoop client nhưng **không được khởi chạy**. |
| CVE-2026-33845 | (Spark OS layer) | no fix | GnuTLS DoS | **ACCEPT** — Không expose DTLS. |

---

## 3. Risk Register

| ID | CVE | Severity | Image | Risk Decision | Owner | Review Date | Notes |
|----|-----|----------|-------|---------------|-------|-------------|-------|
| R-001 | CVE-2025-68121 | CRITICAL | influxdb:2, grafana:13.0.1 | MONITOR | DevOps | 2026-08-01 | Upgrade khi vendor release build mới với Go 1.24.13+ |
| R-002 | CVE-2024-47561 | CRITICAL | spark (all) | MONITOR | DevOps | 2026-08-01 | Avro schema chỉ từ trusted source. Upgrade Spark khi có bản mới tích hợp Avro 1.11.4+ |
| R-003 | CVE-2026-33816 | CRITICAL | grafana:13.0.1 | MONITOR | DevOps | 2026-08-01 | Theo dõi Grafana release với pgx v5.9.0+ |
| R-004 | CVE-2023-45853 | CRITICAL | influxdb:2 | ACCEPT | Tech Lead | 2026-11-01 | `will_not_fix` từ vendor. Không có fix upstream. Re-evaluate nếu expose public. |
| R-005 | CVE-2022-46337 | CRITICAL | spark (all) | ACCEPT | Tech Lead | 2026-11-01 | Derby không dùng LDAP trong deployment này. No exposure. |
| R-006 | CVE-2023-44981 | CRITICAL | spark (all) | ACCEPT | Tech Lead | 2026-11-01 | ZooKeeper JAR có nhưng không chạy (KRaft mode). No exposure. |
| R-007 | CVE-2026-31789 | CRITICAL | grafana:13.0.1 | ACCEPT | Tech Lead | 2026-11-01 | 32-bit only. Deployment trên 64-bit. Not applicable. |
| R-008 | HIGH (×50+) | HIGH | All images | ACCEPT | DevOps | 2026-11-01 | Bulk accept — OS/runtime packages, upstream vendor responsibility |

---

## 4. Mitigation Controls (hiện tại)

Dù có CVE, các control sau giảm thiểu risk thực tế:

| Control | Mô tả |
|---------|-------|
| **Network isolation** | Tất cả service trong Docker internal network. Chỉ expose port cần thiết (9092, 8086, 3000). |
| **No public internet exposure** | Không có service nào có public IP trong deployment local/lab này. |
| **No DTLS / no LDAP / no ZooKeeper** | Các CVE liên quan đến tính năng không dùng → risk = 0 trong context này. |
| **Token-based auth** | InfluxDB dùng token, Grafana dùng basic auth — không anonymous access. |
| **Kafka KRaft mode** | Không dùng ZooKeeper → CVE-2023-44981 không áp dụng. |

---

## 5. Kết luận

- **CRITICAL CVE thực sự có rủi ro trong context này:** R-001 (Go TLS), R-002 (Avro RCE path) → **MONITOR**
- **CRITICAL CVE không áp dụng hoặc không có fix:** R-004 đến R-007 → **ACCEPT**
- **Không có CRITICAL nào yêu cầu action ngay** vì deployment là lab/internal, không public-facing
- **Generator image** (`bigdata-generator`) sạch nhất: 0 CRITICAL, 2 HIGH → trạng thái tốt

> **Khuyến nghị dài hạn:** Pin image versions và thiết lập scheduled Trivy scan hàng tuần để phát hiện CVE mới kịp thời khi đưa lên production.
