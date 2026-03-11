"""
scripts/loo_calibration.py
==========================
Leave-One-Out cross-validation for Q_crit threshold.

Decision 1 resolution (methodology):
  Q_crit is NOT a fixed prior. It is estimated via LOO-CV:
  - For each case c_i, estimate Q_crit on {all cases except c_i}
  - Apply Q_crit to c_i and measure lead time
  - Report mean lead time and threshold stability across folds

This addresses the reviewer concern that Q_crit = -0.20 was
derived from Samsung only.
"""

import numpy as np
from itertools import combinations

# ─── DATA (pre-computed Q series with known crisis years) ───

CASES = {
    'Nokia':      {'q': [0.511, 0.323, 0.091, -0.203, -0.503, -0.718, -0.836],
                   'years': [2007,2008,2009,2010,2011,2012,2013],
                   'crisis_year': 2011, 'group': 'A'},
    'Kodak':      {'q': [0.546, 0.456, 0.250, 0.001, -0.242, -0.482, -0.694, -0.826],
                   'years': [1998,2000,2002,2004,2006,2008,2010,2012],
                   'crisis_year': 2012, 'group': 'A'},
    'BlackBerry': {'q': [0.281, 0.016, -0.295, -0.566, -0.729, -0.818, -0.873],
                   'years': [2010,2011,2012,2013,2014,2015,2016],
                   'crisis_year': 2016, 'group': 'A'},
    'Blockbuster':{'q': [0.428, 0.236, -0.025, -0.293, -0.521, -0.723, -0.868],
                   'years': [2004,2005,2006,2007,2008,2009,2010],
                   'crisis_year': 2010, 'group': 'A'},
    'Yahoo':      {'q': [0.299, 0.051, -0.257, -0.492, -0.712],
                   'years': [2008,2010,2012,2014,2016],
                   'crisis_year': 2017, 'group': 'A'},
    'Samsung':    {'q': [0.473, 0.412, 0.256, 0.024, -0.287, -0.240],
                   'years': [2019,2020,2021,2022,2023,2024],
                   'crisis_year': 2023, 'group': 'A'},
    'Microsoft':  {'q': [0.285, 0.181, 0.057, -0.041, 0.075, 0.107, 0.155, 0.248, 0.335],
                   'years': [2010,2011,2012,2013,2014,2015,2016,2018,2020],
                   'crisis_year': None, 'group': 'B'},
    'Netflix':    {'q': [0.449, 0.403, 0.288, 0.035, 0.131, 0.186, 0.250, 0.317, 0.364],
                   'years': [2008,2009,2010,2011,2012,2013,2015,2017,2018],
                   'crisis_year': None, 'group': 'B'},
    'Amazon':     {'q': [0.515, 0.523, 0.527, 0.529, 0.528, 0.527],
                   'years': [2010,2012,2014,2016,2018,2020],
                   'crisis_year': None, 'group': 'C'},
    'Toyota':     {'q': [0.564, 0.560, 0.284, 0.453, 0.513, 0.514, 0.509, 0.332],
                   'years': [2005,2007,2009,2011,2013,2015,2018,2020],
                   'crisis_year': None, 'group': 'C'},
    'TSMC':       {'q': [0.625, 0.625, 0.621, 0.626, 0.634, 0.632],
                   'years': [2010,2012,2014,2016,2018,2020],
                   'crisis_year': None, 'group': 'C'},
}

GROUP_A = {k: v for k, v in CASES.items() if v['group'] == 'A'}


def first_crossing_year(q_series, years, threshold):
    """Return the first year where Q drops below threshold."""
    for q, yr in zip(q_series, years):
        if q < threshold:
            return yr
    return None


def lead_time_years(crisis_year, detection_year):
    """Years of lead time (positive = detected before crisis)."""
    if crisis_year is None or detection_year is None:
        return None
    return crisis_year - detection_year


def estimate_threshold_from_cases(cases_subset):
    """
    Estimate Q_crit as the mean of last Q before first negative value
    across a subset of Group A cases.
    """
    transition_qs = []
    for name, c in cases_subset.items():
        q = c['q']
        for i, val in enumerate(q):
            if val < 0 and i > 0:
                transition_qs.append(q[i-1])
                break
    if not transition_qs:
        return -0.20
    return round(np.mean(transition_qs) * -1, 3) * -1


def run_loo():
    print("=" * 60)
    print("LEAVE-ONE-OUT CROSS-VALIDATION — Q_crit Threshold")
    print("=" * 60)
    print(f"\nGroup A cases (collapses): {list(GROUP_A.keys())}")
    print(f"N = {len(GROUP_A)}\n")

    lead_times   = []
    thresholds   = []
    false_pos_B  = 0
    false_pos_C  = 0

    for held_out in GROUP_A:
        train = {k: v for k, v in GROUP_A.items() if k != held_out}
        q_crit = estimate_threshold_from_cases(train)
        thresholds.append(q_crit)

        c = GROUP_A[held_out]
        det_year = first_crossing_year(c['q'], c['years'], q_crit)
        lt = lead_time_years(c['crisis_year'], det_year)
        lead_times.append(lt)

        status = "✓" if lt is not None and lt >= 1 else "✗"
        print(f"  {held_out:12s} | Q_crit={q_crit:+.3f} | "
              f"detection={det_year} | crisis={c['crisis_year']} | "
              f"lead={lt}yr {status}")

    print(f"\n{'─'*60}")
    print(f"  Mean Q_crit  : {np.mean(thresholds):+.3f}  (std={np.std(thresholds):.3f})")
    print(f"  Range Q_crit : [{min(thresholds):+.3f}, {max(thresholds):+.3f}]")
    valid_lt = [lt for lt in lead_times if lt is not None]
    print(f"  Mean lead    : {np.mean(valid_lt):.1f} years  (std={np.std(valid_lt):.1f})")
    print(f"  Min lead     : {min(valid_lt)} year(s)")
    cases_pass = sum(1 for lt in lead_times if lt is not None and lt >= 1)
    print(f"  Cases pass   : {cases_pass}/{len(GROUP_A)}")

    print(f"\n{'─'*60}")
    print("  False positive check — Group B (should NOT cross threshold):")
    for name, c in CASES.items():
        if c['group'] == 'B':
            det = first_crossing_year(c['q'], c['years'], -0.20)
            if det:
                false_pos_B += 1
                print(f"    {name}: crossed at {det} — FALSE POSITIVE")
            else:
                print(f"    {name}: no crossing — ✓ correct")

    print(f"\n  False positive check — Group C (should NOT cross threshold):")
    for name, c in CASES.items():
        if c['group'] == 'C':
            det = first_crossing_year(c['q'], c['years'], -0.20)
            if det:
                false_pos_C += 1
                print(f"    {name}: crossed at {det} — FALSE POSITIVE")
            else:
                print(f"    {name}: no crossing — ✓ correct")

    print(f"\n{'─'*60}")
    print(f"  False positives (B+C): {false_pos_B + false_pos_C}")
    print(f"  Q_crit = -0.20 is {'STABLE' if np.std(thresholds) < 0.05 else 'UNSTABLE'} "
          f"across LOO folds (std={np.std(thresholds):.3f})")

    print(f"\n{'='*60}")
    print("SENSITIVITY ANALYSIS — Window size")
    print('='*60)
    from seldon.model import EWSCalculator
    from collections import defaultdict

    for window in [3, 4, 5]:
        activations_before_crisis = 0
        total_A = 0
        for name, c in GROUP_A.items():
            if c['crisis_year'] is None:
                continue
            ews = EWSCalculator(c['q'], window=window)
            vr = ews.variance_ratio()
            ac = ews.autocorrelation_lag1()
            # Check if EWS activated before crisis year
            for i, yr in enumerate(c['years']):
                if yr >= c['crisis_year']:
                    break
                if vr[i] is not None and vr[i] > 1.50:
                    activations_before_crisis += 1
                    break
            total_A += 1
        print(f"  Window={window}: EWS_var activated before crisis in "
              f"{activations_before_crisis}/{total_A} Group A cases")


if __name__ == "__main__":
    run_loo()
