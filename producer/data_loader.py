"""
Task 2.2 - Data Loader & Normalizer
Đọc và chuẩn hóa dữ liệu BATADAL:
  - Parse DATETIME (dd/mm/yy HH) -> ISO 8601 timestamp
  - Strip tên cột (dataset04 có khoảng trắng thừa)
  - Ép kiểu đúng: float cho sensor, int cho status/flag
  - Xử lý null và ATT_FLAG = -999
  - Ghép dataset03 + dataset04 thành 1 DataFrame
"""

import pandas as pd
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "dataset"

SENSOR_FLOAT_COLS = [
    "L_T1", "L_T2", "L_T3", "L_T4", "L_T5", "L_T6", "L_T7",
    "F_PU1", "F_PU2", "F_PU3", "F_PU4", "F_PU5", "F_PU6",
    "F_PU7", "F_PU8", "F_PU9", "F_PU10", "F_PU11", "F_V2",
    "P_J280", "P_J269", "P_J300", "P_J256", "P_J289", "P_J415",
    "P_J302", "P_J306", "P_J307", "P_J317", "P_J14", "P_J422",
]

STATUS_INT_COLS = [
    "S_PU1", "S_PU2", "S_PU3", "S_PU4", "S_PU5", "S_PU6",
    "S_PU7", "S_PU8", "S_PU9", "S_PU10", "S_PU11", "S_V2",
]


def _parse_datetime(raw: str) -> str:
    """Chuyển 'dd/mm/yy HH' -> 'YYYY-MM-DDTHH:00:00Z'."""
    from datetime import datetime, timezone
    dt = datetime.strptime(raw.strip(), "%d/%m/%y %H")
    return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_single(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Strip tên cột (dataset04 có khoảng trắng sau dấu phẩy)
    df.columns = df.columns.str.strip()
    return df


def load_water_data(
    drop_unknown: bool = True,
    drop_nulls: bool = True,
) -> pd.DataFrame:
    """
    Đọc và chuẩn hóa toàn bộ dữ liệu BATADAL.

    Args:
        drop_unknown: Nếu True, bỏ các dòng ATT_FLAG == -999 (unknown label).
        drop_nulls:   Nếu True, bỏ các dòng có bất kỳ giá trị cảm biến null.

    Returns:
        DataFrame đã chuẩn hóa, sắp xếp theo timestamp tăng dần.
    """
    df03 = _read_single(DATASET_DIR / "BATADAL_dataset03.csv")
    df04 = _read_single(DATASET_DIR / "BATADAL_dataset04.csv")

    df = pd.concat([df03, df04], ignore_index=True)

    # 1. Parse timestamp -> ISO 8601
    df["timestamp"] = df["DATETIME"].apply(_parse_datetime)
    df = df.drop(columns=["DATETIME"])

    # 2. Ép kiểu cột float
    for col in SENSOR_FLOAT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")

    # 3. Ép kiểu cột int (status)
    for col in STATUS_INT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int8")

    # ATT_FLAG có thể là -999 nên parse trước khi cast nhỏ
    df["ATT_FLAG"] = pd.to_numeric(df["ATT_FLAG"], errors="coerce")

    # 4. Xử lý ATT_FLAG = -999 (unknown label trong dataset04)
    if drop_unknown:
        before = len(df)
        df = df[df["ATT_FLAG"] != -999]
        print(f"[data_loader] Dropped {before - len(df)} rows with ATT_FLAG=-999")

    df["ATT_FLAG"] = df["ATT_FLAG"].astype("Int8")

    # 5. Xử lý null ở cột cảm biến
    if drop_nulls:
        before = len(df)
        df = df.dropna(subset=SENSOR_FLOAT_COLS + STATUS_INT_COLS)
        print(f"[data_loader] Dropped {before - len(df)} rows with null sensor values")

    # 6. Sắp xếp theo thời gian
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 7. Đưa timestamp lên đầu
    cols = ["timestamp"] + [c for c in df.columns if c != "timestamp"]
    df = df[cols]

    print(f"[data_loader] Loaded {len(df)} rows | "
          f"ATT_FLAG distribution: {df['ATT_FLAG'].value_counts().to_dict()}")

    return df

