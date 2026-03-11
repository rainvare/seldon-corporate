"""
seldon.model
============
Core Organizational Resilience Model v3.0

Q(t) = R_scalar(t) - Pe(t)*(1 + gamma*Pe(t))

R_scalar(t) = sum(w_i * R_i(t))    where R_i in [Rs, Ro, Rt, Rf, Rc]
Pe(t)       = 0.55*Pt + 0.30*Pc + 0.15*Preg

Regimes:
  Q > 0.15            Functional Stability
  -0.05 <= Q <= 0.15  Tension
  -0.20 <= Q < -0.05  Fragility
  Q < -0.20           Structural Rupture
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


GAMMA = 0.50   # Pe amplification coefficient
ALPHA = 0.15   # Investment -> resilience conversion
BETA  = 0.10   # Growth inertia accumulation
DELTA = 0.04   # Natural resilience depreciation

# Regime thresholds
THRESHOLD_STABLE   =  0.15
THRESHOLD_TENSION  = -0.05
THRESHOLD_FRAGILE  = -0.20


@dataclass
class ResilienceVector:
    Rs: float  # Strategic
    Ro: float  # Operational
    Rt: float  # Technological
    Rf: float  # Financial
    Rc: float  # Cognitive

    def to_dict(self):
        return {'Rs': self.Rs, 'Ro': self.Ro, 'Rt': self.Rt,
                'Rf': self.Rf, 'Rc': self.Rc}

    def scalar(self, weights: dict) -> float:
        return (weights['Rs']*self.Rs + weights['Ro']*self.Ro +
                weights['Rt']*self.Rt + weights['Rf']*self.Rf +
                weights['Rc']*self.Rc)


@dataclass
class EnvironmentalPressure:
    Pt:   float  # Technology disruption [0,1]
    Pc:   float  # Competitive pressure  [0,1]
    Preg: float  # Regulatory pressure   {0, 0.5, 1}

    def raw(self) -> float:
        return 0.55*self.Pt + 0.30*self.Pc + 0.15*self.Preg

    def effective(self) -> float:
        p = self.raw()
        return p * (1 + GAMMA * p)


@dataclass
class Period:
    year:     int
    dims:     ResilienceVector
    pressure: EnvironmentalPressure
    weights:  dict

    @property
    def R_scalar(self) -> float:
        return self.dims.scalar(self.weights)

    @property
    def Pe_raw(self) -> float:
        return self.pressure.raw()

    @property
    def Pe_eff(self) -> float:
        return self.pressure.effective()

    @property
    def Q(self) -> float:
        return self.R_scalar - self.Pe_eff

    @property
    def regime(self) -> str:
        q = self.Q
        if q > THRESHOLD_STABLE:    return "STABLE"
        if q > THRESHOLD_TENSION:   return "TENSION"
        if q > THRESHOLD_FRAGILE:   return "FRAGILITY"
        return "RUPTURE"

    def to_dict(self) -> dict:
        return {
            'year':     self.year,
            'Rs':       self.dims.Rs,
            'Ro':       self.dims.Ro,
            'Rt':       self.dims.Rt,
            'Rf':       self.dims.Rf,
            'Rc':       self.dims.Rc,
            'R_scalar': round(self.R_scalar, 4),
            'Pe_raw':   round(self.Pe_raw, 4),
            'Pe_eff':   round(self.Pe_eff, 4),
            'Q':        round(self.Q, 4),
            'regime':   self.regime,
        }


class EWSCalculator:
    """Early Warning Signal calculator for a Q(t) series."""

    VARIANCE_THRESHOLD = 1.50
    AC_THRESHOLD       = 0.70
    CSD_THRESHOLD      = 0.50   # 50% increase in recovery time

    def __init__(self, q_series: list[float], window: int = 4):
        self.q = np.array(q_series)
        self.window = window

    def variance_ratio(self) -> list[Optional[float]]:
        """Rolling variance / historical variance."""
        hist_var = np.var(self.q)
        out = []
        for i in range(len(self.q)):
            if i < self.window - 1:
                out.append(None)
            else:
                seg = self.q[max(0, i-self.window+1):i+1]
                out.append(round(float(np.var(seg) / hist_var), 3) if hist_var > 0 else None)
        return out

    def autocorrelation_lag1(self) -> list[Optional[float]]:
        """Rolling lag-1 autocorrelation."""
        out = []
        for i in range(len(self.q)):
            if i < self.window:
                out.append(None)
            else:
                seg = self.q[max(0, i-self.window+1):i+1]
                if len(seg) < 2:
                    out.append(None)
                else:
                    corr = np.corrcoef(seg[:-1], seg[1:])[0,1]
                    out.append(round(float(corr), 3))
        return out

    def ews_active(self) -> dict:
        """Returns dict of active EWS signals at final period."""
        vr  = self.variance_ratio()
        ac  = self.autocorrelation_lag1()
        last_vr = next((x for x in reversed(vr) if x is not None), None)
        last_ac = next((x for x in reversed(ac) if x is not None), None)
        return {
            'EWS_var': last_vr is not None and last_vr > self.VARIANCE_THRESHOLD,
            'EWS_ac':  last_ac is not None and last_ac > self.AC_THRESHOLD,
            'EWS_var_value': last_vr,
            'EWS_ac_value':  last_ac,
        }


def derive_weights(capex_rev: float, hhi_rev: float,
                   dol: float, nd_ebitda: float,
                   avg_tenure_years: float) -> dict:
    """
    Derive dimension weights from observable financials.

    Parameters
    ----------
    capex_rev       : CapEx / Revenue
    hhi_rev         : Revenue HHI (0-1, 1=fully concentrated)
    dol             : Degree of Operating Leverage
    nd_ebitda       : Net Debt / EBITDA (capped at 6)
    avg_tenure_years: Average C-suite tenure in years
    """
    wt_raw = capex_rev
    ws_raw = hhi_rev
    wo_raw = min(dol / 10, 1.0)
    wf_raw = min(nd_ebitda / 6, 1.0)
    wc_raw = min(avg_tenure_years / 12, 1.0)

    total = wt_raw + ws_raw + wo_raw + wf_raw + wc_raw
    if total == 0:
        raise ValueError("All raw weights are zero")

    return {
        'Rs': round(ws_raw / total, 4),
        'Ro': round(wo_raw / total, 4),
        'Rt': round(wt_raw / total, 4),
        'Rf': round(wf_raw / total, 4),
        'Rc': round(wc_raw / total, 4),
    }
