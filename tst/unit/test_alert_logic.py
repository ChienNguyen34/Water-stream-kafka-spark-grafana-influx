"""
Tests for rule-based alert logic trong spark_streaming/stream_processor.py
Không dùng Spark — extract logic thành pure Python để test nhanh.
Chạy: pytest tst/unit/test_alert_logic.py -v
"""
import pytest
from types import SimpleNamespace


def compute_alert(row) -> str:
    """
    Mirror chính xác logic trong stream_processor.py df_flagged.
    Cập nhật hàm này khi thay đổi rule trong Spark.
    """
    if row.S_PU1 == 1 and row.L_T1 > 6.3:
        return "PU1_STUCK_ON"
    if row.S_PU1 == 0 and row.L_T1 < 4.0:
        return "PU1_STUCK_OFF"
    if row.S_PU2 == 1 and row.L_T1 > 6.3:
        return "PU2_STUCK_ON"
    if row.S_PU3 == 1 and row.L_T3 > 4.5:
        return "PU3_STUCK_ON"
    if row.S_PU3 == 0 and row.L_T3 < 1.0:
        return "PU3_STUCK_OFF"
    return "NORMAL"


def compute_disp(row) -> dict:
    """
    Mirror logic disp_PUx trong stream_processor.py.
    0=OFF(xám), 1=ON(xanh), 2=ALERT(đỏ)
    """
    disp_PU1 = 2 if ((row.S_PU1 == 1 and row.L_T1 > 6.3) or
                     (row.S_PU1 == 0 and row.L_T1 < 4.0)) else row.S_PU1
    disp_PU2 = 2 if (row.S_PU2 == 1 and row.L_T1 > 6.3) else row.S_PU2
    disp_PU3 = 2 if ((row.S_PU3 == 1 and row.L_T3 > 4.5) or
                     (row.S_PU3 == 0 and row.L_T3 < 1.0)) else row.S_PU3
    return {"disp_PU1": disp_PU1, "disp_PU2": disp_PU2, "disp_PU3": disp_PU3}


def make_row(**kwargs):
    defaults = dict(S_PU1=0, S_PU2=0, S_PU3=0, L_T1=5.0, L_T3=2.5)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- compute_alert ---

def test_normal_no_anomaly():
    row = make_row(S_PU1=1, L_T1=5.0)
    assert compute_alert(row) == "NORMAL"


def test_pu1_stuck_on():
    row = make_row(S_PU1=1, L_T1=6.5)
    assert compute_alert(row) == "PU1_STUCK_ON"


def test_pu1_stuck_on_boundary():
    # Đúng tại ngưỡng 6.3 → không trigger (phải > 6.3)
    row = make_row(S_PU1=1, L_T1=6.3)
    assert compute_alert(row) == "NORMAL"


def test_pu1_stuck_off():
    row = make_row(S_PU1=0, L_T1=3.5)
    assert compute_alert(row) == "PU1_STUCK_OFF"


def test_pu1_stuck_off_boundary():
    # Đúng tại ngưỡng 4.0 → không trigger (phải < 4.0)
    row = make_row(S_PU1=0, L_T1=4.0)
    assert compute_alert(row) == "NORMAL"


def test_pu2_stuck_on():
    row = make_row(S_PU1=0, S_PU2=1, L_T1=6.5)
    assert compute_alert(row) == "PU2_STUCK_ON"


def test_pu1_takes_priority_over_pu2():
    row = make_row(S_PU1=1, S_PU2=1, L_T1=6.5)
    assert compute_alert(row) == "PU1_STUCK_ON"


def test_pu3_stuck_on():
    row = make_row(S_PU3=1, L_T3=5.0)
    assert compute_alert(row) == "PU3_STUCK_ON"


def test_pu3_stuck_off():
    row = make_row(S_PU3=0, L_T3=0.5)
    assert compute_alert(row) == "PU3_STUCK_OFF"


def test_pu3_normal_range():
    row = make_row(S_PU3=1, L_T3=3.0)
    assert compute_alert(row) == "NORMAL"


# --- compute_disp ---

def test_disp_all_off_normal():
    row = make_row(S_PU1=0, S_PU2=0, S_PU3=0, L_T1=5.0, L_T3=2.5)
    d = compute_disp(row)
    assert d == {"disp_PU1": 0, "disp_PU2": 0, "disp_PU3": 0}


def test_disp_all_on_normal():
    row = make_row(S_PU1=1, S_PU2=1, S_PU3=1, L_T1=5.0, L_T3=2.5)
    d = compute_disp(row)
    assert d == {"disp_PU1": 1, "disp_PU2": 1, "disp_PU3": 1}


def test_disp_pu1_alert_on():
    row = make_row(S_PU1=1, L_T1=7.0)
    assert compute_disp(row)["disp_PU1"] == 2


def test_disp_pu1_alert_off():
    row = make_row(S_PU1=0, L_T1=3.0)
    assert compute_disp(row)["disp_PU1"] == 2


def test_disp_pu2_alert():
    row = make_row(S_PU2=1, L_T1=7.0)
    assert compute_disp(row)["disp_PU2"] == 2


def test_disp_pu3_alert_on():
    row = make_row(S_PU3=1, L_T3=5.0)
    assert compute_disp(row)["disp_PU3"] == 2


def test_disp_pu3_alert_off():
    row = make_row(S_PU3=0, L_T3=0.5)
    assert compute_disp(row)["disp_PU3"] == 2


def test_disp_values_always_in_0_1_2():
    test_cases = [
        make_row(S_PU1=0, S_PU2=0, S_PU3=0, L_T1=5.0, L_T3=2.5),
        make_row(S_PU1=1, S_PU2=1, S_PU3=1, L_T1=5.0, L_T3=2.5),
        make_row(S_PU1=1, L_T1=7.0),
        make_row(S_PU1=0, L_T1=3.0),
        make_row(S_PU3=1, L_T3=5.0),
    ]
    for row in test_cases:
        d = compute_disp(row)
        for key, val in d.items():
            assert val in (0, 1, 2), f"{key}={val} nằm ngoài {{0,1,2}}"
