# 📋 PROJECT BACKLOG: REAL-TIME IoT WATER GRID PIPELINE
**Epic:** [DE-101] Xây dựng hạ tầng Containerization & Giả lập luồng dữ liệu Streaming từ bộ dataset BATADAL.
**Architecture:** Kappa Architecture (Streaming-first) với Spark Structured Streaming làm Speed Layer.
**Sprint Goal:** Hoàn thiện luồng dữ liệu "từ file tĩnh ra biểu đồ thời gian thực" chạy hoàn toàn trên Docker.

---

## 📐 PHASE 1: SYSTEM & DATA DESIGN (Thiết kế hệ thống)

- [ ] **[DE-102] Task: Thiết kế kiến trúc hạ tầng (Infrastructure Design)**
  - **Mô tả:** Chốt danh sách các component và luồng giao tiếp mạng nội bộ (Docker bridge network).
  - **Acceptance Criteria (DoD):**
    - [ ] Vẽ sơ đồ luồng dữ liệu chuẩn (Python -> Kafka -> Spark Structured Streaming -> InfluxDB -> Grafana).
    - [ ] Định nghĩa các port cần expose (Kafka: 9092, InfluxDB: 8086, Grafana: 3000).
    - [ ] Thống nhất chiến lược lưu trữ (Persistent Volumes) cho Message Broker và Database.

- [ ] **[DE-103] Task: Định nghĩa Hợp đồng dữ liệu (Data Contract & Data Modeling)**
  - **Mô tả:** Thiết kế cấu trúc payload và logic phân tầng dữ liệu cho đồ án.
  - **Acceptance Criteria (DoD):**
    - [ ] Map các cột từ file CSV (`BATADAL_dataset.csv`) sang định dạng JSON payload.
    - [ ] Chốt Schema (Kiểu dữ liệu của 43 cảm biến, chuẩn thời gian ISO 8601).
    - [ ] Thiết kế logic (trên giấy/tài liệu) cho Tầng Bronze (Raw JSON) và dự kiến cho Tầng Silver (Dữ liệu đã clean) ở Sprint sau.

---

## 💻 PHASE 2: IMPLEMENTATION (Phát triển & Đóng gói Container)

- [ ] **[DE-104] Task: Xây dựng Python Data Generator (IoT Simulator)**
  - **Mô tả:** Viết script đọc file tĩnh và giả lập luồng streaming tốc độ cao.
  - **Acceptance Criteria (DoD):**
    - [ ] Code Python đọc từng dòng file CSV thành công.
    - [ ] Áp dụng thuật toán ép xung thời gian (Time Compression) -> Bắn tối thiểu 50 messages/giây.
    - [ ] Đóng gói script thành công bằng file `Dockerfile` riêng.

- [ ] **[DE-105] Task: Triển khai Message Broker (Kafka Cluster)**
  - **Mô tả:** Dựng hạ tầng thu thập sự kiện.
  - **Acceptance Criteria (DoD):**
    - [ ] Viết file `docker-compose.yml` định nghĩa Kafka + Kraft.
    - [ ] Khởi tạo thành công topic `water_stream`.
    - [ ] Cấu hình thành công persistent volume để không mất data log khi restart.

- [ ] **[DE-106] Task: Triển khai Storage & Visualization (InfluxDB + Grafana)**
  - **Mô tả:** Dựng cơ sở dữ liệu chuỗi thời gian và công cụ trực quan hóa.
  - **Acceptance Criteria (DoD):**
    - [ ] Tích hợp InfluxDB (v2.7) và Grafana vào chung file `docker-compose.yml`.
    - [ ] Thiết lập Healthcheck đảm bảo Grafana chỉ chạy khi InfluxDB đã sẵn sàng.
    - [ ] Cấu hình credentials (user/password/token) qua biến môi trường (Environment Variables).

---

## 🧪 PHASE 3: TESTING & VALIDATION (Kiểm thử & Nghiệm thu)

- [ ] **[DE-107] Task: Level 1 & 2 - Unit Test & Container Inspection**
  - **Mô tả:** Kiểm tra logic nội bộ và cấu trúc đóng gói trước khi chạy hệ thống.
  - **Acceptance Criteria (DoD):**
    - [ ] (Level 1) Script Python chạy không bị crash khi gặp dòng dữ liệu rỗng (Null values).
    - [ ] (Level 2) Review Dockerfile và `docker-compose.yml`: Không dùng tag `:latest` (trừ image tự build), xác nhận các thư viện base không có lỗ hổng bảo mật nghiêm trọng.

- [ ] **[DE-108] Task: Level 3 & 4 - Integration & End-to-End (E2E) Test**
  - **Mô tả:** Kiểm thử tích hợp toàn cụm và nghiệm thu luồng dữ liệu (Data-in-motion).
  - **Acceptance Criteria (DoD):**
    - [ ] (Level 3) Gõ lệnh `docker-compose up -d` -> Toàn bộ containers (Kafka, Spark, Generator, InfluxDB, Grafana) trạng thái "Healthy" và cùng nằm trong 1 Docker Network.
    - [ ] (Level 4 - E2E) Dữ liệu chảy mượt mà: Script Python bắn vào Kafka -> Spark Structured Streaming consume và xử lý -> Lưu vào InfluxDB.
    - [ ] (Level 4 - E2E) Tạo thành công 1 biểu đồ Line Chart trên Grafana UI (hiển thị ví dụ mực nước của bể `L_T1`) nhấp nháy theo thời gian thực (Real-time update).