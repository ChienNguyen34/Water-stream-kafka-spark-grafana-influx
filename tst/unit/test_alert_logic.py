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
    Nguồn ngưỡng: CTOWN.INP [CONTROLS] section.
    Cập nhật hàm này khi thay đổi rule trong Spark.
    """
    # T1 — PU1 (OPEN <4.0, CLOSED >6.3)
    if row.S_PU1 == 1 and row.L_T1 > 6.3:  return "PU1_STUCK_ON"
    if row.S_PU1 == 0 and row.L_T1 < 4.0:  return "PU1_STUCK_OFF"
    # T1 — PU2 (OPEN <1.0, CLOSED >4.5)
    if row.S_PU2 == 1 and row.L_T1 > 4.5:  return "PU2_STUCK_ON"
    if row.S_PU2 == 0 and row.L_T1 < 1.0:  return "PU2_STUCK_OFF"
    # T2 — V2 valve (OPEN <0.5, CLOSED >5.5)
    if row.S_V2 == 1  and row.L_T2 > 5.5:  return "V2_STUCK_ON"
    if row.S_V2 == 0  and row.L_T2 < 0.5:  return "V2_STUCK_OFF"
    # T3 — PU4 (OPEN <3.0, CLOSED >5.3)
    if row.S_PU4 == 1 and row.L_T3 > 5.3:  return "PU4_STUCK_ON"
    if row.S_PU4 == 0 and row.L_T3 < 3.0:  return "PU4_STUCK_OFF"
    # T3 — PU5 (OPEN <1.0, CLOSED >3.5)
    if row.S_PU5 == 1 and row.L_T3 > 3.5:  return "PU5_STUCK_ON"
    if row.S_PU5 == 0 and row.L_T3 < 1.0:  return "PU5_STUCK_OFF"
    # T4 — PU6 (OPEN <2.0, CLOSED >3.5)
    if row.S_PU6 == 1 and row.L_T4 > 3.5:  return "PU6_STUCK_ON"
    if row.S_PU6 == 0 and row.L_T4 < 2.0:  return "PU6_STUCK_OFF"
    # T4 — PU7 (OPEN <3.0, CLOSED >4.5)
    if row.S_PU7 == 1 and row.L_T4 > 4.5:  return "PU7_STUCK_ON"
    if row.S_PU7 == 0 and row.L_T4 < 3.0:  return "PU7_STUCK_OFF"
    # T5 — PU8 (OPEN <1.5, CLOSED >4.0)
    if row.S_PU8 == 1 and row.L_T5 > 4.0:  return "PU8_STUCK_ON"
    if row.S_PU8 == 0 and row.L_T5 < 1.5:  return "PU8_STUCK_OFF"
    # T7 — PU10 (OPEN <2.5, CLOSED >4.8)
    if row.S_PU10 == 1 and row.L_T7 > 4.8: return "PU10_STUCK_ON"
    if row.S_PU10 == 0 and row.L_T7 < 2.5: return "PU10_STUCK_OFF"
    # T7 — PU11 (OPEN <1.0, CLOSED >3.0)
    if row.S_PU11 == 1 and row.L_T7 > 3.0: return "PU11_STUCK_ON"
    if row.S_PU11 == 0 and row.L_T7 < 1.0: return "PU11_STUCK_OFF"
    return "NORMAL"


def compute_disp(row) -> dict:
    """
    Mirror logic disp_PUx / disp_V2 trong stream_processor.py.
    0=OFF(xám), 1=ON(xanh), 2=ALERT(đỏ)
    """
    disp_PU1  = 2 if ((row.S_PU1 == 1 and row.L_T1 > 6.3) or
                      (row.S_PU1 == 0 and row.L_T1 < 4.0)) else row.S_PU1
    disp_PU2  = 2 if ((row.S_PU2 == 1 and row.L_T1 > 4.5) or
                      (row.S_PU2 == 0 and row.L_T1 < 1.0)) else row.S_PU2
    disp_V2   = 2 if ((row.S_V2  == 1 and row.L_T2 > 5.5) or
                      (row.S_V2  == 0 and row.L_T2 < 0.5)) else row.S_V2
    disp_PU4  = 2 if ((row.S_PU4 == 1 and row.L_T3 > 5.3) or
                      (row.S_PU4 == 0 and row.L_T3 < 3.0)) else row.S_PU4
    disp_PU5  = 2 if ((row.S_PU5 == 1 and row.L_T3 > 3.5) or
                      (row.S_PU5 == 0 and row.L_T3 < 1.0)) else row.S_PU5
    disp_PU6  = 2 if ((row.S_PU6 == 1 and row.L_T4 > 3.5) or
                      (row.S_PU6 == 0 and row.L_T4 < 2.0)) else row.S_PU6
    disp_PU7  = 2 if ((row.S_PU7 == 1 and row.L_T4 > 4.5) or
                      (row.S_PU7 == 0 and row.L_T4 < 3.0)) else row.S_PU7
    disp_PU8  = 2 if ((row.S_PU8 == 1 and row.L_T5 > 4.0) or
                      (row.S_PU8 == 0 and row.L_T5 < 1.5)) else row.S_PU8
    disp_PU10 = 2 if ((row.S_PU10 == 1 and row.L_T7 > 4.8) or
                      (row.S_PU10 == 0 and row.L_T7 < 2.5)) else row.S_PU10
    disp_PU11 = 2 if ((row.S_PU11 == 1 and row.L_T7 > 3.0) or
                      (row.S_PU11 == 0 and row.L_T7 < 1.0)) else row.S_PU11
    return {
        "disp_PU1": disp_PU1, "disp_PU2": disp_PU2, "disp_V2": disp_V2,
        "disp_PU4": disp_PU4, "disp_PU5": disp_PU5,
        "disp_PU6": disp_PU6, "disp_PU7": disp_PU7,
        "disp_PU8": disp_PU8,
        "disp_PU10": disp_PU10, "disp_PU11": disp_PU11,
    }


def make_row(**kwargs):
    defaults = dict(
        S_PU1=0, S_PU2=0, S_PU4=0, S_PU5=0,
        S_PU6=0, S_PU7=0, S_PU8=0, S_PU10=0, S_PU11=0, S_V2=0,
        L_T1=5.0, L_T2=3.0, L_T3=2.5, L_T4=3.0, L_T5=2.5, L_T7=3.5,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# T1 — PU1
# ---------------------------------------------------------------------------

def test_normal_no_anomaly():
    assert compute_alert(make_row(S_PU1=1, L_T1=5.0)) == "NORMAL"

def test_pu1_stuck_on():
    assert compute_alert(make_row(S_PU1=1, L_T1=6.5)) == "PU1_STUCK_ON"

def test_pu1_stuck_on_boundary():
    # Đúng tại ngưỡng 6.3 → không trigger (phải > 6.3)
    assert compute_alert(make_row(S_PU1=1, L_T1=6.3)) == "NORMAL"

def test_pu1_stuck_off():
    assert compute_alert(make_row(S_PU1=0, L_T1=3.5)) == "PU1_STUCK_OFF"

def test_pu1_stuck_off_boundary():
    assert compute_alert(make_row(S_PU1=0, L_T1=4.0)) == "NORMAL"

# ---------------------------------------------------------------------------
# T1 — PU2
# ---------------------------------------------------------------------------

def test_pu2_stuck_on():
    assert compute_alert(make_row(S_PU1=0, S_PU2=1, L_T1=5.0)) == "PU2_STUCK_ON"

def test_pu2_stuck_on_boundary():
    assert compute_alert(make_row(S_PU2=1, L_T1=4.5)) == "NORMAL"

def test_pu2_stuck_off():
    assert compute_alert(make_row(S_PU2=0, L_T1=0.5)) == "PU2_STUCK_OFF"

def test_pu1_takes_priority_over_pu2():
    assert compute_alert(make_row(S_PU1=1, S_PU2=1, L_T1=6.5)) == "PU1_STUCK_ON"

# ---------------------------------------------------------------------------
# T2 — V2
# ---------------------------------------------------------------------------

def test_v2_stuck_on():
    assert compute_alert(make_row(S_V2=1, L_T2=5.8)) == "V2_STUCK_ON"

def test_v2_stuck_off():
    assert compute_alert(make_row(S_V2=0, L_T2=0.3)) == "V2_STUCK_OFF"

def test_v2_normal():
    assert compute_alert(make_row(S_V2=1, L_T2=3.0)) == "NORMAL"

# ---------------------------------------------------------------------------
# T3 — PU4
# ---------------------------------------------------------------------------

def test_pu4_stuck_on():
    assert compute_alert(make_row(S_PU4=1, L_T3=5.5)) == "PU4_STUCK_ON"

def test_pu4_stuck_off():
    assert compute_alert(make_row(S_PU4=0, L_T3=2.0)) == "PU4_STUCK_OFF"

def test_pu4_normal():
    assert compute_alert(make_row(S_PU4=1, L_T3=4.0)) == "NORMAL"

# ---------------------------------------------------------------------------
# T3 — PU5
# ---------------------------------------------------------------------------

def test_pu5_stuck_on():
    assert compute_alert(make_row(S_PU5=1, L_T3=4.0)) == "PU5_STUCK_ON"

def test_pu5_stuck_off():
    assert compute_alert(make_row(S_PU5=0, L_T3=0.5)) == "PU5_STUCK_OFF"

def test_pu4_takes_priority_over_pu5():
    # PU4 check comes before PU5 in the chain
    assert compute_alert(make_row(S_PU4=1, S_PU5=1, L_T3=5.5)) == "PU4_STUCK_ON"

# ---------------------------------------------------------------------------
# T4 — PU6
# ---------------------------------------------------------------------------

def test_pu6_stuck_on():
    assert compute_alert(make_row(S_PU6=1, L_T4=4.0)) == "PU6_STUCK_ON"

def test_pu6_stuck_off():
    assert compute_alert(make_row(S_PU6=0, L_T4=1.5)) == "PU6_STUCK_OFF"

# ---------------------------------------------------------------------------
# T4 — PU7
# ---------------------------------------------------------------------------

def test_pu7_stuck_on():
    assert compute_alert(make_row(S_PU7=1, L_T4=5.0)) == "PU7_STUCK_ON"

def test_pu7_stuck_off():
    assert compute_alert(make_row(S_PU7=0, L_T4=2.5)) == "PU7_STUCK_OFF"

# ---------------------------------------------------------------------------
# T5 — PU8
# ---------------------------------------------------------------------------

def test_pu8_stuck_on():
    assert compute_alert(make_row(S_PU8=1, L_T5=4.5)) == "PU8_STUCK_ON"

def test_pu8_stuck_off():
    assert compute_alert(make_row(S_PU8=0, L_T5=1.0)) == "PU8_STUCK_OFF"

def test_pu8_normal():
    assert compute_alert(make_row(S_PU8=1, L_T5=2.5)) == "NORMAL"

# ---------------------------------------------------------------------------
# T7 — PU10
# ---------------------------------------------------------------------------

def test_pu10_stuck_on():
    assert compute_alert(make_row(S_PU10=1, L_T7=5.0)) == "PU10_STUCK_ON"

def test_pu10_stuck_off():
    assert compute_alert(make_row(S_PU10=0, L_T7=2.0)) == "PU10_STUCK_OFF"

# ---------------------------------------------------------------------------
# T7 — PU11
# ---------------------------------------------------------------------------

def test_pu11_stuck_on():
    assert compute_alert(make_row(S_PU11=1, L_T7=3.5)) == "PU11_STUCK_ON"

def test_pu11_stuck_off():
    assert compute_alert(make_row(S_PU11=0, L_T7=0.5)) == "PU11_STUCK_OFF"

def test_pu10_takes_priority_over_pu11():
    assert compute_alert(make_row(S_PU10=1, S_PU11=1, L_T7=5.0)) == "PU10_STUCK_ON"

# ---------------------------------------------------------------------------
# disp columns
# ---------------------------------------------------------------------------

def test_disp_pu1_alert():
    row = make_row(S_PU1=1, L_T1=6.5)
    assert compute_disp(row)["disp_PU1"] == 2

def test_disp_pu2_alert():
    row = make_row(S_PU2=1, L_T1=5.0)
    assert compute_disp(row)["disp_PU2"] == 2

def test_disp_v2_alert():
    row = make_row(S_V2=1, L_T2=6.0)
    assert compute_disp(row)["disp_V2"] == 2

def test_disp_pu4_alert():
    row = make_row(S_PU4=1, L_T3=5.5)
    assert compute_disp(row)["disp_PU4"] == 2

def test_disp_pu8_normal_on():
    row = make_row(S_PU8=1, L_T5=2.5)
    assert compute_disp(row)["disp_PU8"] == 1

def test_disp_pu10_off():
    row = make_row(S_PU10=0, L_T7=3.5)
    assert compute_disp(row)["disp_PU10"] == 0


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
