"""
Generate BATADAL_synthetic.csv — synthetic water network sensor data
covering 8 attack scenarios not fully represented in dataset03/04.

Normal operation follows realistic CTOWN physics (levels, flows, pressures).
Each attack scenario runs for a sustained period so the ML model can learn
the full anomaly signature, not just boundary violations.

Usage:
    python dataset/generate_synthetic.py
Output:
    dataset/BATADAL_synthetic.csv  (~2800 rows)
"""

import os
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BATADAL_synthetic.csv")

COLUMNS = [
    "DATETIME",
    "L_T1","L_T2","L_T3","L_T4","L_T5","L_T6","L_T7",
    "F_PU1","S_PU1","F_PU2","S_PU2","F_PU3","S_PU3",
    "F_PU4","S_PU4","F_PU5","S_PU5","F_PU6","S_PU6",
    "F_PU7","S_PU7","F_PU8","S_PU8","F_PU9","S_PU9",
    "F_PU10","S_PU10","F_PU11","S_PU11","F_V2","S_V2",
    "P_J280","P_J269","P_J300","P_J256","P_J289","P_J415",
    "P_J302","P_J306","P_J307","P_J317","P_J14","P_J422",
    "ATT_FLAG",
]

# ─────────────────────────────────────────────────────────────── helpers ────

def _n(mu, sigma, lo=None, hi=None, size=1):
    """Clipped normal sample."""
    v = RNG.normal(mu, sigma, size)
    if lo is not None: v = np.clip(v, lo, None)
    if hi is not None: v = np.clip(v, None, hi)
    return float(v[0]) if size == 1 else v


def _p(base, sigma=0.3, lo=0.0):
    """Junction pressure noise."""
    return max(lo, base + RNG.normal(0, sigma))


def normal_row(t_idx: int) -> dict:
    """
    Realistic normal operating row.
    Tank levels oscillate inside control bounds.
    Pumps follow CTOWN.INP CONTROLS logic.
    """
    phase = (t_idx % 24) / 24.0  # hourly cycle
    cyc   = np.sin(2 * np.pi * phase)

    # Tank levels inside safe operating band
    L_T1  = _n(5.2 + 0.5 * cyc,  0.3, 4.0, 6.3)
    L_T2  = _n(3.0 + 0.8 * cyc,  0.4, 0.5, 5.5)
    L_T3  = _n(4.2 + 0.4 * cyc,  0.3, 3.0, 5.3)
    L_T4  = _n(3.8 + 0.3 * cyc,  0.2, 2.0, 4.5)
    L_T5  = _n(2.8 + 0.3 * cyc,  0.2, 1.5, 4.0)
    L_T6  = _n(3.5 + 0.5 * cyc,  0.3, 0.5, 5.2)
    L_T7  = _n(3.7 + 0.4 * cyc,  0.2, 2.5, 4.8)

    # Pump status follows control logic (simplified)
    S_PU1  = 1 if L_T1  < 5.5 else 0
    S_PU2  = 1 if L_T1  < 2.5 else 0
    S_V2   = 1 if L_T2  < 4.0 else 0
    S_PU4  = 1 if L_T3  < 4.5 else 0
    S_PU5  = 1 if L_T3  < 2.5 else 0
    S_PU6  = 1 if L_T4  < 3.0 else 0
    S_PU7  = 1 if L_T4  < 3.5 else 0
    S_PU8  = 1 if L_T5  < 2.5 else 0
    S_PU10 = 1 if L_T7  < 3.5 else 0
    S_PU11 = 1 if L_T7  < 2.0 else 0
    S_PU3  = int(RNG.random() > 0.5)   # PU3 has no automatic control
    S_PU9  = int(RNG.random() > 0.7)
    S_PU11 = 1 if L_T7 < 2.0 else 0

    # Flow rates correlated with pump status
    F_PU1  = _n(98,  3, 0) * S_PU1
    F_PU2  = _n(99,  3, 0) * S_PU2
    F_PU3  = _n(35,  4, 0) * S_PU3
    F_PU4  = _n(35,  4, 0) * S_PU4
    F_PU5  = _n(34,  4, 0) * S_PU5
    F_PU6  = _n(50,  5, 0) * S_PU6
    F_PU7  = _n(50,  5, 0) * S_PU7
    F_PU8  = _n(34,  4, 0) * S_PU8
    F_PU9  = _n(30,  3, 0) * S_PU9
    F_PU10 = _n(30,  3, 0) * S_PU10
    F_PU11 = _n(30,  3, 0) * S_PU11
    F_V2   = _n(81,  3, 0) * S_V2

    # Junction pressures correlated with total flow & levels
    base_p = 0.5 * (F_PU1 + F_PU2) / 100
    return dict(
        L_T1=L_T1, L_T2=L_T2, L_T3=L_T3, L_T4=L_T4,
        L_T5=L_T5, L_T6=L_T6, L_T7=L_T7,
        F_PU1=F_PU1, S_PU1=S_PU1, F_PU2=F_PU2, S_PU2=S_PU2,
        F_PU3=F_PU3, S_PU3=S_PU3, F_PU4=F_PU4, S_PU4=S_PU4,
        F_PU5=F_PU5, S_PU5=S_PU5, F_PU6=F_PU6, S_PU6=S_PU6,
        F_PU7=F_PU7, S_PU7=S_PU7, F_PU8=F_PU8, S_PU8=S_PU8,
        F_PU9=F_PU9, S_PU9=S_PU9, F_PU10=F_PU10, S_PU10=S_PU10,
        F_PU11=F_PU11, S_PU11=S_PU11, F_V2=F_V2, S_V2=S_V2,
        P_J280=_p(3.0 + base_p), P_J269=_p(33.5),
        P_J300=_p(26.4),          P_J256=_p(87.6),
        P_J289=_p(26.5),          P_J415=_p(84.2),
        P_J302=_p(18.9),          P_J306=_p(82.0),
        P_J307=_p(18.8),          P_J317=_p(67.1),
        P_J14=_p(29.4),           P_J422=_p(28.5),
        ATT_FLAG=0,
    )


# ───────────────────────────────────────────────── attack scenario builders ─

def attack_a1_pu1_stuck_on(n=60) -> list:
    """A1: PU1 and PU2 forced ON while T1 overflows — actuator attack."""
    rows = []
    L_T1 = 6.4
    for _ in range(n):
        L_T1 = min(6.5, L_T1 + _n(0.03, 0.01, 0))
        r = normal_row(0)
        r.update(L_T1=L_T1, S_PU1=1, S_PU2=1,
                 F_PU1=_n(98, 3, 80), F_PU2=_n(99, 3, 80),
                 ATT_FLAG=1)
        rows.append(r)
    return rows


def attack_a2_pu4_pu5_stuck_off(n=60) -> list:
    """A2: PU4 and PU5 forced OFF while T3 drains critically low."""
    rows = []
    L_T3 = 2.8
    for _ in range(n):
        L_T3 = max(0.2, L_T3 - _n(0.04, 0.01, 0))
        r = normal_row(0)
        r.update(L_T3=L_T3, S_PU4=0, S_PU5=0,
                 F_PU4=0.0, F_PU5=0.0,
                 ATT_FLAG=1)
        rows.append(r)
    return rows


def attack_a3_sensor_spoof_t4(n=70) -> list:
    """A3: Sensor spoofing — L_T4 reads normal (2.5) but
    PU6+PU7 both ON with high flow causes pressure anomaly.
    Rule-based MISSES this because L_T4 looks fine."""
    rows = []
    for _ in range(n):
        r = normal_row(0)
        r.update(
            L_T4=_n(2.5, 0.1, 2.0, 3.0),  # spoofed: looks normal
            S_PU6=1, S_PU7=1,               # both pumps forced on
            F_PU6=_n(52, 3, 45),
            F_PU7=_n(51, 3, 44),
            # pressure drops due to over-pumping
            P_J280=_p(0.5, 0.2, 0), P_J269=_p(8.0, 1.0),
            P_J256=_p(20.0, 2.0),   P_J289=_p(6.0, 1.0),
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


def attack_a4_v2_valve_attack(n=60) -> list:
    """A4: V2 forced CLOSED but T2 level drops while neighbour pressure rises.
    Attacker blocks T2 supply — L_T2 drains faster than expected."""
    rows = []
    L_T2 = 4.5
    for _ in range(n):
        L_T2 = max(0.1, L_T2 - _n(0.06, 0.01, 0))
        r = normal_row(0)
        r.update(
            L_T2=L_T2, S_V2=0, F_V2=0.0,
            # pressure backs up upstream
            P_J280=_p(5.5, 0.5), P_J269=_p(40.0, 2.0),
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


def attack_a5_t5_cascade(n=70) -> list:
    """A5: T5 drains (PU8 stuck-off) AND T7 also affected (PU10/11 off).
    Multi-tank simultaneous drain — complex cascade scenario."""
    rows = []
    L_T5, L_T7 = 1.4, 2.4
    for _ in range(n):
        L_T5 = max(0.1, L_T5 - _n(0.03, 0.01, 0))
        L_T7 = max(0.1, L_T7 - _n(0.02, 0.01, 0))
        r = normal_row(0)
        r.update(
            L_T5=L_T5, S_PU8=0, F_PU8=0.0,
            L_T7=L_T7, S_PU10=0, S_PU11=0,
            F_PU10=0.0, F_PU11=0.0,
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


def attack_a6_flow_injection(n=60) -> list:
    """A6: Ghost flow — F_PU3 shows high flow but S_PU3=0.
    Indicates sensor manipulation / illegal injection.
    Rule-based CANNOT detect (no PU3 rule exists)."""
    rows = []
    for _ in range(n):
        r = normal_row(0)
        r.update(
            S_PU3=0,
            F_PU3=_n(65, 5, 50),   # flow WITHOUT pump signal
            P_J280=_p(4.0, 0.4),    # slight pressure rise
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


def attack_a7_pressure_collapse(n=60) -> list:
    """A7: Network-wide pressure collapse while pumps seem normal.
    Could indicate pipe burst or hidden valve manipulation.
    Undetectable by level/status rules."""
    rows = []
    for _ in range(n):
        r = normal_row(0)
        r.update(
            P_J280=_p(0.2, 0.1, 0),  P_J269=_p(1.5, 0.3, 0),
            P_J300=_p(0.8, 0.2, 0),  P_J256=_p(2.0, 0.5, 0),
            P_J289=_p(0.9, 0.2, 0),  P_J415=_p(1.8, 0.4, 0),
            P_J302=_p(0.5, 0.1, 0),  P_J306=_p(1.5, 0.3, 0),
            P_J307=_p(0.4, 0.1, 0),  P_J317=_p(1.2, 0.3, 0),
            P_J14=_p(0.6, 0.2, 0),   P_J422=_p(0.7, 0.2, 0),
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


def attack_a8_correlated_multi_tank(n=70) -> list:
    """A8: Coordinated attack on T1, T3, T7 simultaneously.
    All three tanks pushed toward unsafe levels at same time.
    Complex scenario testing multi-feature correlation."""
    rows = []
    L_T1, L_T3, L_T7 = 6.3, 1.2, 1.1
    for _ in range(n):
        L_T1 = min(6.5, L_T1 + _n(0.02, 0.01, 0))
        L_T3 = max(0.1, L_T3 - _n(0.02, 0.01, 0))
        L_T7 = max(0.1, L_T7 - _n(0.02, 0.01, 0))
        r = normal_row(0)
        r.update(
            L_T1=L_T1, S_PU1=1, S_PU2=1,
            F_PU1=_n(98, 3, 80), F_PU2=_n(99, 3, 80),
            L_T3=L_T3, S_PU4=0, S_PU5=0,
            F_PU4=0.0, F_PU5=0.0,
            L_T7=L_T7, S_PU10=0, S_PU11=0,
            F_PU10=0.0, F_PU11=0.0,
            ATT_FLAG=1,
        )
        rows.append(r)
    return rows


# ──────────────────────────────────────────────────────────────────── main ─

def main():
    rows = []
    n_normal = 2200

    # Normal operation (80% of data)
    for i in range(n_normal):
        r = normal_row(i)
        r["DATETIME"] = f"SYN/{i:04d}"
        rows.append(r)

    # Attack scenarios interspersed
    attacks = [
        ("A1_PU1_STUCK_ON",       attack_a1_pu1_stuck_on()),
        ("A2_PU4_PU5_STUCK_OFF",  attack_a2_pu4_pu5_stuck_off()),
        ("A3_SENSOR_SPOOF_T4",    attack_a3_sensor_spoof_t4()),
        ("A4_V2_VALVE_ATTACK",    attack_a4_v2_valve_attack()),
        ("A5_T5_CASCADE",         attack_a5_t5_cascade()),
        ("A6_FLOW_INJECTION",     attack_a6_flow_injection()),
        ("A7_PRESSURE_COLLAPSE",  attack_a7_pressure_collapse()),
        ("A8_MULTI_TANK",         attack_a8_correlated_multi_tank()),
    ]

    att_idx = n_normal
    for name, att_rows in attacks:
        for r in att_rows:
            r["DATETIME"] = f"SYN/{att_idx:04d}"
            att_idx += 1
        rows.extend(att_rows)
        print(f"  {name}: {len(att_rows)} rows")

    df = pd.DataFrame(rows, columns=COLUMNS)

    total     = len(df)
    n_att     = int(df["ATT_FLAG"].sum())
    n_norm    = total - n_att
    print(f"\nTotal rows : {total}")
    print(f"  Normal   : {n_norm} ({100*n_norm/total:.1f}%)")
    print(f"  Attack   : {n_att} ({100*n_att/total:.1f}%)")

    df.to_csv(OUT, index=False, float_format="%.6f")
    print(f"\n[saved] {OUT}")


if __name__ == "__main__":
    main()
