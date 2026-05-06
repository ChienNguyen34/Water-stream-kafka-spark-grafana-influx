# Giải thích chi tiết `docker-compose.yml`

File `docker-compose.yml` định nghĩa toàn bộ hạ tầng pipeline Big Data gồm 5 services: **Kafka** (message broker), **InfluxDB** (time-series database), **Grafana** (dashboard), **Spark Master** và **Spark Worker** (stream processing).

---

## Tổng quan kiến trúc

```
Producer (Python)
      │
      ▼
   Kafka :9092  (KRaft mode, confluentinc/cp-kafka:8.1.2)
      │
      ▼
   Spark Master :7077 / Worker
      │
      ▼
   InfluxDB :8086  (influxdb:2)
      │
      ▼
   Grafana :3000  (grafana/grafana:13.0.1)
```

---

## Service 1: Kafka

> 📖 **Doc config:** https://docs.confluent.io/platform/current/installation/docker/config-reference.html

```yaml
kafka:
  image: confluentinc/cp-kafka:8.1.2
  container_name: kafka
  volumes:
    - kafka_data:/var/lib/kafka/data
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
  ports:
    - "9092:9092"
```

#### Biến môi trường

| Biến | Giá trị | Giải thích |
|---|---|---|
| `KAFKA_NODE_ID` | `1` | ID định danh node trong cluster. Single-node để `1` |
| `KAFKA_PROCESS_ROLES` | `broker,controller` | **KRaft mode** — node đảm nhiệm cả 2 vai trò: `broker` (nhận/gửi message) và `controller` (quản lý metadata). Không cần Zookeeper |
| `KAFKA_LISTENERS` | `PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093` | 2 listener: `PLAINTEXT` cho client ở port 9092, `CONTROLLER` cho giao tiếp KRaft nội bộ ở port 9093 |
| `KAFKA_ADVERTISED_LISTENERS` | `PLAINTEXT://localhost:9092` | Địa chỉ Kafka quảng bá cho client bên ngoài. Dùng `localhost` khi producer chạy trên máy host. Nếu producer chạy trong container thì đổi thành `kafka:9092` |
| `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP` | `PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT` | Map tên listener → giao thức bảo mật. Dùng `PLAINTEXT` (không mã hóa) cho môi trường dev |
| `KAFKA_CONTROLLER_LISTENER_NAMES` | `CONTROLLER` | Listener dùng cho KRaft controller, phải khớp tên ở `KAFKA_LISTENERS` |
| `KAFKA_CONTROLLER_QUORUM_VOTERS` | `1@kafka:9093` | Danh sách voter trong KRaft quorum. Format: `nodeId@hostname:port` |
| `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR` | `1` | Số replica của topic `__consumer_offsets`. Để `1` cho single-node, production nên để `3` |
| `KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR` | `1` | Số replica của topic quản lý transaction. Lý do tương tự trên |
| `KAFKA_TRANSACTION_STATE_LOG_MIN_ISR` | `1` | Số replica tối thiểu in-sync trước khi ghi transaction thành công |
| `KAFKA_AUTO_CREATE_TOPICS_ENABLE` | `"true"` | Tự động tạo topic `water_stream` khi producer gửi message đầu tiên. Đây là env var chính thống của `confluentinc/cp-kafka` |
| `CLUSTER_ID` | `MkU3OEVBNTcwNTJENDM2Qk` | UUID cluster dạng base64, bắt buộc trong KRaft mode. Tạo bằng `kafka-storage.sh random-uuid`, giữ nguyên sau khi tạo |

#### Volume

```yaml
volumes:
  - kafka_data:/var/lib/kafka/data
```

Persist Kafka log segment (message data) và metadata. Không mất data khi restart container.

#### Ports

Port 9092 expose ra ngoài cho producer/consumer. Port 9093 (CONTROLLER) chỉ dùng nội bộ Docker network, không expose.

---

## Service 2: InfluxDB

> 📖 **Doc config:** https://docs.influxdata.com/influxdb/v2/install/use-docker/?t=Docker+Compose

```yaml
influxdb:
  image: influxdb:2
  container_name: influxdb
  environment:
    DOCKER_INFLUXDB_INIT_MODE: setup
    DOCKER_INFLUXDB_INIT_USERNAME: admin
    DOCKER_INFLUXDB_INIT_PASSWORD: adminpassword
    DOCKER_INFLUXDB_INIT_ORG: bigdata
    DOCKER_INFLUXDB_INIT_BUCKET: water_bucket
    DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: my-super-secret-token
  ports:
    - "8086:8086"
  volumes:
    - influxdb_data:/var/lib/influxdb2
  healthcheck:
    test: ["CMD", "influx", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

#### Biến môi trường

Các biến `DOCKER_INFLUXDB_INIT_*` chỉ có tác dụng **lần đầu tiên** khởi động (khi volume còn trống), sau đó bị bỏ qua.

| Biến | Giá trị | Giải thích |
|---|---|---|
| `DOCKER_INFLUXDB_INIT_MODE` | `setup` | Kích hoạt auto-setup thay cho việc phải vào UI setup thủ công |
| `DOCKER_INFLUXDB_INIT_USERNAME` | `admin` | Tên tài khoản admin đầu tiên |
| `DOCKER_INFLUXDB_INIT_PASSWORD` | `adminpassword` | Mật khẩu admin. **Đổi trước khi deploy production** |
| `DOCKER_INFLUXDB_INIT_ORG` | `bigdata` | Tên organization — đơn vị quản lý cao nhất trong InfluxDB 2.x |
| `DOCKER_INFLUXDB_INIT_BUCKET` | `water_bucket` | Bucket (tương đương database) được tạo sẵn để lưu dữ liệu cảm biến |
| `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN` | `my-super-secret-token` | API token dùng để xác thực khi Spark và Grafana ghi/đọc data. **Đổi trước khi deploy production** |

#### Healthcheck

> 📖 **Doc:** https://docs.docker.com/reference/compose-file/services/#healthcheck

```yaml
healthcheck:
  test: ["CMD", "influx", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

| Field | Giá trị | Giải thích |
|---|---|---|
| `test` | `influx ping` | Lệnh kiểm tra — gọi CLI `influx ping` để xác nhận InfluxDB đang nhận request |
| `interval` | `10s` | Kiểm tra mỗi 10 giây |
| `timeout` | `5s` | Nếu lệnh chạy quá 5s → coi là failed |
| `retries` | `5` | Fail 5 lần liên tiếp → container chuyển sang `unhealthy` |
| `start_period` | `30s` | Chờ 30s sau khi container start trước khi bắt đầu kiểm tra (InfluxDB cần thời gian init) |

---

## Service 3: Grafana

> 📖 **Doc config:** https://grafana.com/docs/grafana/latest/setup-grafana/configure-docker/

```yaml
grafana:
  image: grafana/grafana:13.0.1
  container_name: grafana
  depends_on:
    influxdb:
      condition: service_healthy
  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: adminpassword
  ports:
    - "3000:3000"
  volumes:
    - grafana_data:/var/lib/grafana
```

#### depends_on với condition

```yaml
depends_on:
  influxdb:
    condition: service_healthy
```

Grafana chỉ start **sau khi InfluxDB đạt trạng thái `healthy`** (healthcheck pass). Khác với `depends_on: - influxdb` (chỉ đợi container start, không đợi service sẵn sàng).

#### Biến môi trường

| Biến | Giá trị | Giải thích |
|---|---|---|
| `GF_SECURITY_ADMIN_USER` | `admin` | Tên tài khoản admin đăng nhập Grafana UI |
| `GF_SECURITY_ADMIN_PASSWORD` | `adminpassword` | Mật khẩu admin. **Đổi trước khi deploy production** |

Grafana hỗ trợ hàng trăm biến `GF_*` — xem đầy đủ tại [Grafana env vars doc](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#override-configuration-with-environment-variables).

---

## Service 4 & 5: Spark Master + Worker

> 📖 **Doc config:** https://spark.apache.org/docs/latest/spark-standalone.html

```yaml
spark-master:
  image: apache/spark:3.5.8-java17-python3
  container_name: spark-master
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
  environment:
    - SPARK_MASTER_HOST=spark-master
    - SPARK_MASTER_PORT=7077
    - SPARK_MASTER_WEBUI_PORT=8080
  ports:
    - "7077:7077"
    - "8080:8080"
  volumes:
    - ./spark_streaming:/opt/spark-apps

spark-worker:
  image: apache/spark:3.5.8-java17-python3
  container_name: spark-worker
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
  depends_on:
    - spark-master
  environment:
    - SPARK_WORKER_MEMORY=2g
    - SPARK_WORKER_CORES=2
  volumes:
    - ./spark_streaming:/opt/spark-apps
```

#### Image

`apache/spark:3.5.8-java17-python3` — image chính thống của Apache Software Foundation, bao gồm Java 17 và Python 3 (cần cho PySpark). Dùng Spark 3.5.x vì `spark-sql-kafka` connector (`_2.12`) đã stable và có nhiều tài liệu hơn Spark 4.x.

#### command

Image `apache/spark` không dùng env var `SPARK_MODE` như Bitnami. Phải chỉ định trực tiếp class Java:

| Service | Command |
|---|---|
| Master | `spark-class org.apache.spark.deploy.master.Master` |
| Worker | `spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077` |

#### Biến môi trường

| Biến | Giá trị | Giải thích |
|---|---|---|
| `SPARK_MASTER_HOST` | `spark-master` | Hostname master dùng để bind, phải khớp với tên service trong Docker network |
| `SPARK_MASTER_PORT` | `7077` | Port giao tiếp master–worker |
| `SPARK_MASTER_WEBUI_PORT` | `8080` | Port web UI của Spark master |
| `SPARK_WORKER_MEMORY` | `2g` | RAM tối đa cấp cho worker |
| `SPARK_WORKER_CORES` | `2` | Số CPU core tối đa cấp cho worker |

#### Volume

```yaml
volumes:
  - ./spark_streaming:/opt/spark-apps
```

Mount thư mục `spark_streaming/` (chứa PySpark job) vào container. Khi submit job:
```bash
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-apps/your_job.py
```

---

## Named Volumes

> 📖 **Doc:** https://docs.docker.com/reference/compose-file/volumes/

```yaml
volumes:
  kafka_data:
  influxdb_data:
  grafana_data:
```

| Volume | Service | Lưu gì |
|---|---|---|
| `kafka_data` | Kafka | Log segment (message data), partition metadata |
| `influxdb_data` | InfluxDB | Time-series data, WAL, metadata |
| `grafana_data` | Grafana | Dashboard JSON, datasource config, user settings |

Data **không mất** khi `docker-compose down`. Chỉ mất khi chạy `docker-compose down -v`.

---

## Các lệnh thường dùng

```bash
# Khởi động toàn bộ stack (detached)
docker-compose up -d

# Xem trạng thái và healthcheck
docker-compose ps

# Xem log realtime của 1 service
docker-compose logs -f kafka

# Dừng (giữ data)
docker-compose down

# Dừng và xóa toàn bộ data
docker-compose down -v
```

---

## Cổng truy cập

| Service | URL | Ghi chú |
|---|---|---|
| Kafka | `localhost:9092` | Kết nối từ producer/consumer |
| InfluxDB UI | `http://localhost:8086` | Quản lý bucket, query Flux |
| Grafana UI | `http://localhost:3000` | Xem dashboard |
| Spark Master UI | `http://localhost:8080` | Xem trạng thái jobs, workers |
