# Checklist Đồ án Big Data: Hệ thống Phân tích Dữ liệu IoT Mạng Nước (BATADAL)

## Giai đoạn 0: Thiết kế Hệ thống [DE-102, DE-103]
- [x] **0.1 Vẽ sơ đồ kiến trúc [DE-102]:** Vẽ sơ đồ luồng dữ liệu chuẩn (Python -> Kafka -> Spark Structured Streaming -> InfluxDB -> Grafana).
- [x] **0.2 Định nghĩa port [DE-102]:** Chốt các port cần expose — Kafka: 9092, InfluxDB: 8086, Grafana: 3000.
- [x] **0.3 Chiến lược Persistent Volume [DE-102]:** Thống nhất chiến lược lưu trữ (Persistent Volumes) cho Kafka và InfluxDB.
- [x] **0.4 Data Contract - CSV → JSON [DE-103]:** Map các cột từ file CSV BATADAL sang cấu trúc JSON payload chuẩn.
- [x] **0.5 Data Contract - Schema [DE-103]:** Chốt kiểu dữ liệu của 43 cảm biến, chuẩn thời gian ISO 8601.
- [x] **0.6 Data Modeling - Bronze/Silver [DE-103]:** Thiết kế logic phân tầng dữ liệu (Bronze: Raw JSON, Silver: Cleaned) trên tài liệu.

## Giai đoạn 1: Chuẩn bị Hạ tầng & Môi trường (Local) [DE-105, DE-106]
- [x] **1.1 Cài đặt môi trường cơ bản:** Cài đặt Docker, Docker Compose và Python (>= 3.9).
- [x] **1.2 Cấu hình Kafka [DE-105]:** Viết file `docker-compose.yml` định nghĩa Kafka (KRaft mode — không cần Zookeeper).
- [x] **1.3 Persistent Volume cho Kafka [DE-105]:** Cấu hình volume để không mất data log khi restart.
- [x] **1.4 Khởi tạo topic `water_stream` [DE-105]:** Tạo thành công topic Kafka cho luồng dữ liệu cảm biến.
- [x] **1.5 Tích hợp InfluxDB & Grafana [DE-106]:** Thêm InfluxDB (v2.7) và Grafana vào chung file `docker-compose.yml`.
- [x] **1.6 Healthcheck cho Grafana [DE-106]:** Thiết lập `depends_on` + healthcheck đảm bảo Grafana chỉ start khi InfluxDB đã sẵn sàng.
- [x] **1.7 Credentials qua Environment Variables [DE-106]:** Cấu hình user/password/token qua biến môi trường, không hardcode trong code.
- [x] **1.8 Thiết lập môi trường lập trình:** Tạo Virtual Environment (venv). Cài đặt: `pyspark`, `pandas`, `confluent-kafka`, `scikit-learn`, `influxdb-client`.

## Giai đoạn 2: Xây dựng Data Generator Tool (Python) [DE-104]
- [x] **2.1 Chuẩn bị dữ liệu:** Tải file CSV BATADAL (`dataset03`, `dataset04`) và file mô tả mạng `CTOWN.INP`.
- [x] **2.2 Xử lý dữ liệu Nước:** Đọc và chuẩn hóa dữ liệu BATADAL — parse timestamp (ISO 8601), rename cột, xử lý giá trị null.
- [x] **2.3 Đóng gói JSON Payload:** Định dạng từng dòng thành cấu trúc JSON theo Data Contract đã thiết kế ở 0.4.
- [x] **2.4 Time Compression [DE-104]:** Áp dụng thuật toán ép xung thời gian — đảm bảo tốc độ tối thiểu **50 messages/giây**.
- [x] **2.5 Tích hợp Kafka Producer:** Khởi tạo Producer bằng `confluent-kafka`, stream tuần tự vào topic `water_stream`.
- [x] **2.6 Đóng gói Dockerfile [DE-104]:** Viết `Dockerfile` riêng cho generator, đóng gói thành công vào container.

## Giai đoạn 3: Xử lý luồng (Speed Layer) - Spark Structured Streaming
- [x] **3.1 Khởi tạo Spark Structured Streaming:** Cấu hình PySpark để consume dữ liệu real-time từ topic `water_stream`.
- [x] **3.2 Tiền xử lý (Streaming):** Lọc bỏ các bản ghi null/rác, ép kiểu dữ liệu (casting) về đúng định dạng Float/Int.
- [x] **3.3 Tích hợp Anomaly Detection:** Chạy Rule-based engine (dựa trên `CTOWN.INP`) hoặc mô hình ML để phát hiện sự cố rò rỉ/áp suất bất thường.
- [x] **3.4 Ghi kết quả (Sink):** Ghi cờ cảnh báo (Alerts) và trạng thái bơm vào InfluxDB (Measurement: `water_telemetry`) thông qua `influxdb-client`.

## Giai đoạn 3.5: ML Early Warning (Supervised Anomaly Detection)
- [ ] **3.5.1 Train model offline:** Viết `spark_streaming/train_model.py` — load dataset03 + dataset04, feature engineering (diff, rolling mean, flow balance), train Random Forest, lưu model ra `anomaly_model.pkl`.
- [ ] **3.5.2 Đánh giá model offline:** Tính Precision / Recall / F1-score trên tập test (dataset04), in classification report và confusion matrix.
- [ ] **3.5.3 Tích hợp model vào Spark Streaming:** Cập nhật `stream_processor.py` — load `anomaly_model.pkl` qua Spark broadcast variable, gọi predict qua `pandas_udf` trên mỗi micro-batch.
- [ ] **3.5.4 Cập nhật Docker image:** Thêm `scikit-learn` vào `spark_streaming/Dockerfile`, rebuild image `spark-master` và `spark-worker`.
- [ ] **3.5.5 Kiểm tra kết quả inference:** Xác nhận InfluxDB nhận được trường `ml_alert` (0/1) cùng với `alert_type` rule-based — so sánh 2 nguồn cảnh báo.

## Giai đoạn 4: Trực quan hóa dữ liệu (Grafana Dashboard)
- [ ] **4.1 Kết nối Data Source:** Thêm InfluxDB làm data source trong Grafana, cấu hình bucket `water_bucket` và token xác thực.
- [ ] **4.2 Dashboard Trạng thái Mạng:** Tạo Line Chart panel theo dõi mực nước bể `L_T1`, áp suất và lưu lượng theo thời gian thực bằng Flux query.
- [ ] **4.3 Dashboard Cảnh báo Sự cố:** Vẽ biểu đồ cảnh báo (đỏ/xanh) và timeline sự kiện bất thường, cấu hình Alert Rule trong Grafana khi phát hiện anomaly.

## Giai đoạn 5: Kiểm thử & Nghiệm thu [DE-107, DE-108]
- [ ] **5.1 Unit Test - Null handling [DE-107]:** Script Python chạy không bị crash khi gặp dòng dữ liệu rỗng (Null values).
- [ ] **5.2 Container Inspection [DE-107]:** Review Dockerfile và `docker-compose.yml` — không dùng tag `:latest` (trừ image tự build), không có lỗ hổng bảo mật nghiêm trọng.
- [ ] **5.3 Integration Test [DE-108]:** Chạy `docker-compose up -d` → toàn bộ containers (Kafka, Spark, Generator, InfluxDB, Grafana) trạng thái "Healthy", cùng 1 Docker Network.
- [ ] **5.4 E2E Test - Data Flow [DE-108]:** Dữ liệu chảy xuyên suốt: Python → Kafka → Spark Structured Streaming → InfluxDB.
- [ ] **5.5 E2E Test - Grafana [DE-108]:** Biểu đồ Line Chart `L_T1` trên Grafana UI cập nhật nhấp nháy theo thời gian thực.

## Giai đoạn 6: Triển khai Đám mây (Cloud Deployment)
- [ ] **6.1 Khởi tạo Cloud:** Tạo tài khoản và cấp phát máy ảo (VM) trên AWS (EC2) hoặc GCP (Compute Engine).
- [ ] **6.2 Cài đặt môi trường Cloud:** Cài đặt Docker trên VM.
- [ ] **6.3 Triển khai dịch vụ:** Đẩy file `docker-compose.yml` lên Cloud và khởi chạy hệ thống (Kafka, Spark, InfluxDB, Grafana).
- [ ] **6.4 Cấu hình Mạng & Tường lửa:** Mở các port cần thiết (9092 cho Kafka, 8086 cho InfluxDB, 3000 cho Grafana) và cho phép Data Generator từ máy local bắn dữ liệu lên Cloud.

## Giai đoạn 7: Đánh giá Hiệu năng & Hoàn thiện (Evaluation)
- [ ] **7.1 Đánh giá Thuật toán:** Tính Accuracy/F1-score/Precision/Recall cho khả năng phát hiện đúng nhãn bất thường (`ATT_FLAG`) trên dữ liệu BATADAL.
- [ ] **7.2 Đánh giá Thông lượng & Độ trễ (System Metrics):** Đo Throughput (messages/giây) và Latency (từ Kafka đến Grafana).
- [ ] **7.3 Đánh giá Khả năng Mở rộng (Scalability):** Ghi nhận mức tiêu thụ CPU/RAM và so sánh hiệu năng Spark trên single-node vs. multi-node.
- [ ] **7.4 Tổng kết & Viết báo cáo:** Vẽ sơ đồ kiến trúc, giải thích luồng dữ liệu, chụp ảnh Dashboard và lập bảng so sánh các metric đánh giá.