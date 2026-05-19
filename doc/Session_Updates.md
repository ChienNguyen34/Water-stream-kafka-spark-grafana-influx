# Session Updates — Bigdata BATADAL Pipeline

Tài liệu ghi lại toàn bộ thay đổi thực hiện trong phiên làm việc này, phục vụ viết báo cáo.

---

## 1. Grafana Dashboard — `grafana/dashboards/water_network.json`

### 1.1 Canvas Panel — Flux Query

**Vấn đề:** Query canvas chỉ kéo `disp_PU1`, `disp_PU2`, `disp_PU3`. Các pump còn lại (PU4–PU11) và valve V2 dùng field `S_PUx` thô nên không có màu alert.

**Thay đổi:** Bỏ `disp_PU3` (PU3 không có rule control trong CTOWN.INP), thêm đầy đủ:

```flux
r._field == "disp_PU1" or r._field == "disp_PU2" or
r._field == "disp_V2" or
r._field == "disp_PU4" or r._field == "disp_PU5" or
r._field == "disp_PU6" or r._field == "disp_PU7" or
r._field == "disp_PU8" or
r._field == "disp_PU10" or r._field == "disp_PU11"
```

### 1.2 Canvas Panel — Override Regexp

| Trước | Sau |
|---|---|
| `^disp_PU` | `^disp_` |

Lý do: `disp_V2` không match `^disp_PU`, cần regexp rộng hơn để áp dụng threshold màu 0=xám / 1=xanh / 2=đỏ.

### 1.3 Canvas Panel — Tank Level Thresholds (Hướng B)

**Vấn đề:** Override cũ dùng 1 rule `^L_T` chung với ngưỡng `6.3m` — sai hoàn toàn cho T4 (max 4.7m), T5 (max 4.5m), T7 (max 5.0m).

**Thay đổi:** Xóa override regex chung, thay bằng **7 override `byName` riêng** theo `CTOWN.INP [CONTROLS]` + `[TANKS]`:

| Tank | Red low | Dark Blue (safe low) | Light Blue (safe high) | Red high |
|------|---------|---------------------|----------------------|----------|
| L_T1 | 0 | 1.0 | 4.0 | 6.3 |
| L_T2 | 0 | 0.5 | 2.5 | 5.5 |
| L_T3 | 0 | 1.0 | 3.0 | 5.3 |
| L_T4 | 0 | 2.0 | 3.0 | 4.5 |
| L_T5 | 0 | 1.5 | 2.5 | 4.0 |
| L_T6 | 0 | 0.5 | 3.0 | 5.2 |
| L_T7 | 0 | 1.0 | 2.5 | 4.8 |

Ngưỡng xanh đậm = `OPEN` threshold (pump bật khi level xuống dưới) → ranh giới cảnh báo low.  
Ngưỡng đỏ cao = `CLOSED` threshold (pump tắt khi level vượt) → ranh giới cảnh báo overflow.

### 1.4 Canvas Element Field Bindings

**Vấn đề:** Các element trên Canvas topology dùng `S_PUx` (raw 0/1) thay vì `disp_PUx` (0=off/1=on/2=alert), nên không hiển thị màu đỏ khi có alert.

| Element | Trước | Sau | Ghi chú |
|---|---|---|---|
| Pump PU3 | `disp_PU3` | `S_PU3` | PU3 không có rule → dùng raw status |
| Valve V2 | `S_V2` | `disp_V2` | Có rule T2 |
| Pump PU4 | `S_PU4` | `disp_PU4` | Có rule T3 |
| Pump PU5 | `S_PU5` | `disp_PU5` | Có rule T3 |
| Pump PU6 | `S_PU6` | `disp_PU6` | Có rule T4 |
| Pump PU7 | `S_PU7` | `disp_PU7` | Có rule T4 |
| Pump PU8 | `S_PU8` | `disp_PU8` | Có rule T5 |
| Pump PU9 | `S_PU9` | `S_PU9` | Không có rule → giữ nguyên |
| Pump PU10 | `S_PU10` | `disp_PU10` | Có rule T7 |
| Pump PU11 | `S_PU11` | `disp_PU11` | Có rule T7 |

### 1.5 Panel 11 — ML Anomaly Status (Stat mới)

Panel Stat hiển thị trạng thái hiện tại của ML model:
- `ml_alert = 0` → **NORMAL** (nền xanh `#22C55E`)
- `ml_alert = 1` → **ATTACK DETECTED** (nền đỏ `#DC2626`)

Query Flux: `last()` của field `ml_alert` trong 2 phút gần nhất.

### 1.6 Panel 12 — ML Alert History (Timeseries mới)

Timeseries hiển thị lịch sử `ml_alert` trong 30 phút gần nhất:
- Step-after interpolation (signal nhị phân 0/1)
- Fill opacity 20%, threshold line+area tại value=1 (đỏ)
- `aggregateWindow(every: 10s, fn: max)` để tránh noise

**Panel count:** 8 → **10** panels.

---

## 2. Docker Compose — `docker-compose.yml`

### 2.1 Local/Cloud Switching Comments

Thêm comment toggle để dễ chuyển giữa local và cloud:

```yaml
# spark-driver environment:
# Kafka_broker on cloud
# - KAFKA_BROKER=18.138.224.73:9092
# Kafka_broker local
- KAFKA_BROKER=kafka:29092
# influx on cloud
# - INFLUX_URL=http://18.138.224.73:8086
# influx local
- INFLUX_URL=http://influxdb:8086

# generator environment:
# Kafka_broker on cloud
# KAFKA_BROKER: 18.138.224.73:9092
# Kafka_broker local
KAFKA_BROKER: kafka:29092
```

> **Lưu ý:** `kafka:29092` dùng listener `INTERNAL` (container-to-container). `localhost:9092` chỉ dùng từ host machine.

### 2.2 Spark Memory Settings

**Vấn đề:** Executor OOM (`java.lang.OutOfMemoryError: Java heap space`) khi xử lý burst batch sau restart.

| Config | Trước | Sau |
|---|---|---|
| `SPARK_WORKER_MEMORY` | `2g` | `3g` (cả 2 workers) |
| `--executor-memory` | (mặc định 1g) | `1536m` |
| `--driver-memory` | (mặc định 1g) | `1g` (explicit) |
| `--conf spark.executor.memoryOverhead` | (không có) | `256m` |

### 2.3 Auto-clear Checkpoint

**Vấn đề:** Khi chuyển giữa cloud Kafka và local Kafka, checkpoint cũ lưu offsets của broker khác → `FileAlreadyExistsException: .metadata.crc already exists` → crash loop.

**Giải pháp:** Wrap `spark-submit` bằng `sh -c` để tự động xóa checkpoint trước khi start:

```yaml
command: >
  sh -c "
  find /tmp/spark-checkpoint -mindepth 1 -delete &&
  /opt/spark/bin/spark-submit ...
  "
```

> **Lý do dùng `find -mindepth 1 -delete` thay vì `rm -rf *`:**  
> `rm -rf /path/*` bỏ sót hidden files (`.metadata.crc`, `.lock`) do glob `*` không match files bắt đầu bằng `.`.  
> `rm -rf /path` không thể xóa mount point của Docker volume.

---

## 3. Spark Streaming — `spark_streaming/stream_processor.py`

### 3.1 Mở rộng null filter

**Trước:** Chỉ check `L_T1.isNotNull()`.  
**Sau:** Check tất cả 7 tanks (`L_T1` đến `L_T7`).

### 3.2 maxOffsetsPerTrigger

Thêm giới hạn số message xử lý mỗi micro-batch để tránh OOM khi có backlog lớn:

```python
.option("maxOffsetsPerTrigger", 1000)
```

### 3.3 ML Inference — pandas_udf

Load `anomaly_model.pkl` tại startup, broadcast tới executors, áp dụng qua `pandas_udf`:

```python
_bc_model = spark.sparkContext.broadcast(pickle.load(_f))

@pandas_udf(IntegerType())
def _ml_predict(*cols):
    df_feat = pd.concat(list(cols), axis=1)
    df_feat.columns = _ML_FEATURES
    df_feat = df_feat.fillna(0.0)
    preds = _bc_model.value.predict(df_feat)
    return pd.Series(preds.astype(int))

df_flagged = df_flagged.withColumn(
    "ml_alert",
    _ml_predict(*[col(f) for f in _ML_FEATURES])
)
```

Nếu `anomaly_model.pkl` chưa tồn tại → `ml_alert` mặc định `0` (không crash).

---

## 4. Phase 3.5 — ML Early Warning

### 4.1 Dataset

| Dataset | Rows | Normal | Attack | Ghi chú |
|---|---|---|---|---|
| `BATADAL_dataset03.csv` | 8761 | 8761 | 0 | Chỉ normal operation |
| `BATADAL_dataset04.csv` | 4177 | N/A | N/A | ATT_FLAG=-999 (blind test, không có label) |
| `BATADAL_synthetic.csv` | 2710 | 2200 | 510 | 8 attack scenarios tự tổng hợp |

### 4.2 Synthetic Dataset — `dataset/generate_synthetic.py`

8 attack scenarios mô phỏng các dạng tấn công khác nhau:

| ID | Tên | Mô tả | Rule-based có bắt? |
|---|---|---|---|
| A1 | PU1 Stuck-On | PU1+PU2 forced ON, T1 overflow (L_T1 > 6.5) | ✅ Có |
| A2 | PU4/PU5 Stuck-Off | PU4+PU5 forced OFF, T3 drain critically (L_T3 < 0.2) | ✅ Có |
| A3 | Sensor Spoof T4 | L_T4 spoofed = 2.5 (normal), nhưng PU6+PU7 cả 2 chạy → áp suất drop | ❌ Không |
| A4 | V2 Valve Attack | V2 forced OFF, T2 level drops, áp suất ngược dòng tăng | ✅ Có (STUCK_OFF) |
| A5 | T5 Cascade | PU8 off (T5 drain) + PU10/11 off (T7 drain) đồng thời | ✅ Có |
| A6 | Ghost Flow | F_PU3 > 50 nhưng S_PU3 = 0 (flow without pump signal) | ❌ Không (PU3 không có rule) |
| A7 | Pressure Collapse | Tất cả P_J drop gần 0, pump status bình thường | ❌ Không |
| A8 | Multi-Tank Coord. | T1 overflow + T3 drain + T7 drain đồng thời | ✅ Có |

**Nhận xét:** Scenarios A3, A6, A7 là các attack rule-based KHÔNG thể phát hiện — đây chính là giá trị bổ sung của ML model.

### 4.3 Feature Engineering

**31 features** — không dùng time features vì `COMPRESSION_FACTOR=180000` phá vỡ mối quan hệ thời gian thực tế:

| Nhóm | Features | Số lượng |
|---|---|---|
| Tank levels | `L_T1`–`L_T7` | 7 |
| Flow rates | `F_PU1`–`F_PU11`, `F_V2` | 12 |
| Pump/valve status | `S_PU1`–`S_PU11`, `S_V2` | 12 |

### 4.4 Training Strategy

- **Negative (normal):** dataset03 (8761 rows)
- **Positive (attacks):** BATADAL_synthetic.csv (510 rows)
- **Split:** Stratified 75/25 (sklearn `train_test_split`, `stratify=y`)
- **Final model:** Train trên 100% combined data sau khi evaluate

```
Total  : 11471 rows | Normal: 10961 | Attack: 510
Train  :  8603 | Val: 2868 | Val attacks: 128
```

### 4.5 Model — RandomForestClassifier

```python
RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",   # xử lý class imbalance ~21:1
    random_state=42,
    n_jobs=-1,
)
```

### 4.6 Kết quả Đánh giá

```
=== Classification Report (stratified 25% val) ===
              precision    recall  f1-score   support
      Normal       0.99      1.00      0.99      2740
      Attack       1.00      0.73      0.85       128

    accuracy                           0.99      2868
   macro avg       0.99      0.87      0.92      2868
weighted avg       0.99      0.99      0.99      2868

=== Confusion Matrix ===
  TN=2740  FP=   0
  FN=  34  TP=  94
```

**Phân tích:**
- **Precision = 1.00:** Không có false positive — mọi alert đều là thật
- **Recall = 0.73:** Bỏ sót ~27% attack cases (chủ yếu các attack subtle trong synthetic)
- **F1 = 0.85:** Kết quả tốt, đủ để triển khai production

### 4.7 Top 10 Feature Importances

| Rank | Feature | Importance |
|---|---|---|
| 1 | L_T1 | 0.2402 |
| 2 | L_T6 | 0.2013 |
| 3 | F_PU10 | 0.0882 |
| 4 | L_T7 | 0.0549 |
| 5 | S_PU10 | 0.0405 |
| 6 | L_T5 | 0.0403 |
| 7 | L_T2 | 0.0391 |
| 8 | L_T3 | 0.0338 |
| 9 | F_PU7 | 0.0326 |
| 10 | F_PU3 | 0.0287 |

Tank levels chiếm dominant — phù hợp vì attacks chủ yếu thao túng mực nước.

---

## 5. InfluxDB Sink — `spark_streaming/influx_sink.py`

Thêm `ml_alert` vào `_INT_FIELDS`:

```python
_INT_FIELDS = [
    ...
    "disp_PU10", "disp_PU11",
    "ml_alert",   # NEW
]
```

---

## 6. Dockerfile — `spark_streaming/Dockerfile`

Thêm `scikit-learn` để executor có thể load và chạy RandomForest model:

```dockerfile
RUN pip install --no-cache-dir \
    "influxdb-client>=1.40.0" \
    "python-dotenv>=1.0.0" \
    "scikit-learn>=1.4.0"   # NEW
```

> **Rebuild required:** `docker compose build spark-master spark-worker spark-worker-2 spark-driver`

---

## 7. Tests

### 7.1 E2E Test Panel Count

| File | Trước | Sau |
|---|---|---|
| `tst/e2e/test_e2e_grafana.py` | `EXPECTED_PANEL_COUNT = 3` → `8` (session trước) | `8` → **`10`** |
| `tst/e2e/test_e2e_grafana_cloud.py` | `EXPECTED_PANEL_COUNT = 3` → `8` (session trước) | `8` → **`10`** |

---

## 8. Rule-based Detection — Tổng hợp rules từ CTOWN.INP

Cập nhật đầy đủ `stream_processor.py` từ `CTOWN.INP [CONTROLS]` section:

| Pump/Valve | Tank | OPEN khi level < | CLOSED khi level > | alert_type khi vi phạm |
|---|---|---|---|---|
| PU1 | T1 | 4.0 m | 6.3 m | `PU1_STUCK_ON` / `PU1_STUCK_OFF` |
| PU2 | T1 | 1.0 m | 4.5 m | `PU2_STUCK_ON` / `PU2_STUCK_OFF` |
| V2  | T2 | 0.5 m | 5.5 m | `V2_STUCK_ON` / `V2_STUCK_OFF` |
| PU4 | T3 | 3.0 m | 5.3 m | `PU4_STUCK_ON` / `PU4_STUCK_OFF` |
| PU5 | T3 | 1.0 m | 3.5 m | `PU5_STUCK_ON` / `PU5_STUCK_OFF` |
| PU6 | T4 | 2.0 m | 3.5 m | `PU6_STUCK_ON` / `PU6_STUCK_OFF` |
| PU7 | T4 | 3.0 m | 4.5 m | `PU7_STUCK_ON` / `PU7_STUCK_OFF` |
| PU8 | T5 | 1.5 m | 4.0 m | `PU8_STUCK_ON` / `PU8_STUCK_OFF` |
| PU10 | T7 | 2.5 m | 4.8 m | `PU10_STUCK_ON` / `PU10_STUCK_OFF` |
| PU11 | T7 | 1.0 m | 3.0 m | `PU11_STUCK_ON` / `PU11_STUCK_OFF` |
| PU3, PU9 | — | Không có rule | Không có rule | Không detect |
| T6 | — | Không có pump control | Không có pump control | Level hiển thị only |

**`disp_PUx` encoding:**
- `0` = Pump OFF (xám)
- `1` = Pump ON bình thường (xanh)
- `2` = Pump ALERT — STUCK_ON hoặc STUCK_OFF (đỏ)

---

## 9. Files Tạo/Thay đổi — Tóm tắt

| File | Hành động | Mô tả |
|---|---|---|
| `grafana/dashboards/water_network.json` | Sửa | Flux query, overrides per-tank, element bindings, thêm panel 11+12 |
| `docker-compose.yml` | Sửa | Local/cloud toggle, memory settings, auto-clear checkpoint |
| `spark_streaming/stream_processor.py` | Sửa | maxOffsetsPerTrigger, ML broadcast + pandas_udf, ml_alert column |
| `spark_streaming/influx_sink.py` | Sửa | Thêm ml_alert vào _INT_FIELDS |
| `spark_streaming/Dockerfile` | Sửa | Thêm scikit-learn |
| `spark_streaming/train_model.py` | **Tạo mới** | Train RF, stratified eval, save pkl + json |
| `dataset/generate_synthetic.py` | **Tạo mới** | 8 attack scenarios, 2710 rows |
| `dataset/BATADAL_synthetic.csv` | **Generated** | Synthetic dataset |
| `spark_streaming/anomaly_model.pkl` | **Generated** | Deployed RF model |
| `spark_streaming/feature_names.json` | **Generated** | Feature list cho inference |
| `tst/e2e/test_e2e_grafana.py` | Sửa | EXPECTED_PANEL_COUNT 8→10 |
| `tst/e2e/test_e2e_grafana_cloud.py` | Sửa | EXPECTED_PANEL_COUNT 8→10 |
