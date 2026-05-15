# Cloud Deployment — BATADAL Big Data Pipeline

## Tổng quan kiến trúc (Option A — Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS EC2 (ap-southeast-1)                  │
│  Instance: batadal-pipeline-new (t3.micro, Ubuntu 24.04)    │
│  IP Public: 18.138.224.73                                    │
│                                                             │
│  ┌──────────┐   ┌───────────┐   ┌──────────┐               │
│  │  Kafka   │   │ InfluxDB  │   │ Grafana  │               │
│  │  :9092   │   │  :8086    │   │  :3000   │               │
│  └──────────┘   └───────────┘   └──────────┘               │
└─────────────────────────────────────────────────────────────┘
          ▲                 ▲
          │ produce         │ write metrics
          │                 │
┌─────────────────────────────────────────────────────────────┐
│                    Local Machine (Windows)                   │
│                                                             │
│  ┌───────────┐   ┌──────────────┐   ┌─────────────────┐    │
│  │ Generator │──▶│ Spark Driver │──▶│ Spark Workers   │    │
│  │(producer/)│   │(spark_stream)│   │  (x2 local)     │    │
│  └───────────┘   └──────────────┘   └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Lý do chọn hybrid:** EC2 t3.micro chỉ có 1 GB RAM, không đủ chạy thêm Spark (cần ~2–4 GB). Kafka + InfluxDB + Grafana chiếm ~750 MB là vừa đủ.

---

## Thông tin EC2 Instance

| Thuộc tính | Giá trị |
|---|---|
| Instance ID | `i-03149c5ac5e7cc9b6` |
| Instance Name | `batadal-pipeline-new` |
| Instance Type | `t3.micro` (1 vCPU, 1 GB RAM) |
| AMI | Ubuntu Server 24.04 LTS |
| Region | `ap-southeast-1` (Singapore) |
| Public IP | `18.138.224.73` |
| Key Pair | `batadal-key_new.pem` |
| Security Group | `sg-0d3c2e2a6a5dd6018` (`launch-wizard-2`) |

---

## Security Group — Inbound Rules

| Port | Protocol | Source | Dịch vụ |
|---|---|---|---|
| 22 | TCP | 0.0.0.0/0 | SSH |
| 9092 | TCP | 0.0.0.0/0 | Kafka |
| 8086 | TCP | 0.0.0.0/0 | InfluxDB |
| 3000 | TCP | 0.0.0.0/0 | Grafana |

> **Lưu ý bảo mật:** Source `0.0.0.0/0` dùng cho môi trường lab. Production nên giới hạn về IP cụ thể.

---

## Services trên EC2

### File cấu hình: `docker-compose.cloud.yml`

| Service | Image | Port | Memory Limit |
|---|---|---|---|
| kafka | `confluentinc/cp-kafka:8.1.2` | 9092 | 350 MB |
| influxdb | `influxdb:2` | 8086 | 256 MB |
| grafana | `grafana/grafana:13.0.1` | 3000 | 128 MB |

### Cấu hình Kafka quan trọng

```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${EC2_PUBLIC_IP}:9092,INTERNAL://kafka:29092
KAFKA_HEAP_OPTS: "-Xmx256m -Xms128m"
```

`EC2_PUBLIC_IP` phải được set khi start để external clients (Spark, Generator) kết nối được.

---

## Cách Deploy lên EC2

### Yêu cầu

- File `batadal-key_new.pem` ở `d:\Workspace\Bigdata\`
- SSH đã được fix permissions:
  ```powershell
  $keyFile = "d:\Workspace\Bigdata\batadal-key_new.pem"
  icacls $keyFile /inheritance:r
  icacls $keyFile /remove "NT AUTHORITY\Authenticated Users"
  icacls $keyFile /remove "BUILTIN\Users"
  icacls $keyFile /remove "BUILTIN\Administrators"
  icacls $keyFile /remove "NT AUTHORITY\SYSTEM"
  ```

### Chạy deploy script

```powershell
cd d:\Workspace\Bigdata
.\deploy_cloud.ps1
```

Script tự động thực hiện:
1. Test SSH connection
2. Cài Docker (nếu chưa có)
3. Upload `docker-compose.cloud.yml` + `grafana/` lên EC2
4. Start Kafka + InfluxDB + Grafana với `EC2_PUBLIC_IP` được set
5. Health check InfluxDB và Grafana

### Start thủ công (nếu cần)

```bash
# SSH vào EC2
ssh -i batadal-key_new.pem ubuntu@18.138.224.73

# Start services
cd ~/batadal
EC2_PUBLIC_IP=18.138.224.73 docker compose up -d

# Kiểm tra
docker compose ps
docker compose logs kafka --tail=20
```

---

## Truy cập Services

### Qua SSH Tunnel (khuyến nghị nếu ISP block port)

```powershell
# Chạy lệnh này và giữ terminal mở
ssh -i "d:\Workspace\Bigdata\batadal-key_new.pem" `
    -o StrictHostKeyChecking=no `
    -N `
    -L 3000:localhost:3000 `
    -L 8086:localhost:8086 `
    -L 9092:localhost:9092 `
    ubuntu@18.138.224.73
```

Sau đó truy cập:
- Grafana: **http://localhost:3000** (admin / adminpassword)
- InfluxDB: **http://localhost:8086**
- Kafka: `localhost:9092`

### Truy cập trực tiếp (nếu ISP không block)

- Grafana: **http://18.138.224.73:3000**
- InfluxDB: **http://18.138.224.73:8086**
- Kafka: `18.138.224.73:9092`

---

## Chạy Local Spark + Generator trỏ vào EC2

### Trường hợp không dùng tunnel (trực tiếp)

```powershell
# docker-compose.yml đã được cấu hình env vars:
# KAFKA_BROKER: 18.138.224.73:9092
# INFLUX_URL: http://18.138.224.73:8086

docker-compose up -d spark-master spark-worker spark-worker-2 spark-driver generator
```

### Trường hợp dùng SSH tunnel

Đổi env vars trong `docker-compose.yml`:
```yaml
KAFKA_BROKER: localhost:9092
INFLUX_URL: http://localhost:8086
```

> **Lưu ý:** `depends_on: kafka` và `depends_on: influxdb` đã được xóa khỏi `spark-driver` và `generator` vì các services này chạy trên EC2, không phải local.

---

## Kiểm tra sau deploy

```powershell
# Kiểm tra containers trên EC2
ssh -i "d:\Workspace\Bigdata\batadal-key_new.pem" -o StrictHostKeyChecking=no ubuntu@18.138.224.73 "docker ps"

# Kiểm tra InfluxDB
Invoke-RestMethod "http://18.138.224.73:8086/health"

# Kiểm tra Grafana
Invoke-RestMethod "http://18.138.224.73:3000/api/health"

# Kiểm tra Kafka listener có IP đúng không
ssh -i "d:\Workspace\Bigdata\batadal-key_new.pem" -o StrictHostKeyChecking=no ubuntu@18.138.224.73 "docker logs kafka 2>&1 | grep -i 'advertised'"
#compose up
ssh -i "d:\Workspace\Bigdata\batadal-key_new.pem" -o StrictHostKeyChecking=no ubuntu@18.138.224.73 "cd ~/batadal && EC2_PUBLIC_IP=18.138.224.73 docker compose up -d kafka grafana 2>&1"
```

---

## Vấn đề đã gặp & cách xử lý

| Vấn đề | Nguyên nhân | Giải pháp |
|---|---|---|
| SSH: `bad permissions` | File `.pem` có quyền quá rộng (Windows) | `icacls` xóa ACL thừa, chỉ giữ user hiện tại |
| `EC2_PUBLIC_IP` not set | Kafka start thiếu env var | Thêm `EC2_PUBLIC_IP=18.138.224.73` trước lệnh `docker compose up` |
| Port 3000/8086 không reach được | ISP block outbound port lạ | Dùng SSH tunnel `-L 3000:localhost:3000` |
| Docker install fail: `&&` error | PowerShell parse `&&` như PS syntax | Dùng `& ssh @SSH_ARGS` array thay vì `Invoke-Expression` |
| `docker: command not found` | Docker chưa cài trên EC2 | Script `deploy_cloud.ps1` tự cài qua apt |
| Kafka `Exited (137)` + Grafana `Exited (1)` sau vài giờ | t3.micro chỉ 1 GB RAM, không có swap → Linux OOM killer kill Kafka; Grafana SQLite bị corrupt do bị kill đột ngột | Thêm 1 GB swap (xem bên dưới) + xóa volume Grafana để recreate |

### Thêm Swap trên EC2 (fix OOM kill)

**Swap là gì:** Vùng không gian trên EBS disk được dùng làm RAM ảo. Khi RAM đầy, Linux chuyển bớt dữ liệu ít dùng ra swap thay vì kill process. Chậm hơn RAM nhưng giữ container không bị OOM kill.

**Chi phí:** t3.micro có 8 GB EBS mặc định (~$0.08/GB/tháng). 1 GB swap tốn thêm ~$0.08/tháng — không đáng kể.

```bash
# SSH vào EC2 rồi chạy:
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab  # persist sau reboot

# Kiểm tra
free -m
```

**Fix Grafana SQLite bị locked (sau khi bị OOM kill):**

```bash
cd ~/batadal
docker rm grafana
docker volume rm batadal_grafana_data
EC2_PUBLIC_IP=18.138.224.73 docker compose up -d grafana
```

---

## Checklist Phase 6

- [x] **6.1** Tạo AWS account + EC2 instance (t3.micro, Ubuntu 24.04)
- [x] **6.2** Cài Docker trên EC2 qua `deploy_cloud.ps1`
- [x] **6.3** Deploy Kafka + InfluxDB + Grafana lên EC2
- [x] **6.4** Cấu hình Security Group (ports 22/9092/8086/3000)
- [x] **6.5** Grafana accessible qua SSH tunnel
- [x] **6.6** Kafka advertise đúng EC2 public IP
