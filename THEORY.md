# THEORY.md — Seldon Corporate Framework v3.0
## Mathematical Specification

---

## §1. State Variable

```
Q(t) = R_scalar(t) − Pe_eff(t)
```

Q(t) is the **Resilience Margin** — the signed distance between internal adaptive capacity and effective environmental pressure. Q ∈ (−∞, 1] by construction.

---

## §2. Resilience Vector

```
R(t) = [Rs(t), Ro(t), Rt(t), Rf(t), Rc(t)]   each ∈ [0, 1]
R_scalar(t) = Σ wᵢ(t) · Rᵢ(t),    Σwᵢ = 1
```

| Dim | Name | Formula |
|-----|------|---------|
| Rs | Strategic | 0.35·D_rev + 0.30·V_seg + 0.20·R_cap + 0.15·A_est |
| Ro | Operational | 0.40·(1−σ_margin) + 0.35·E_op + 0.25·(1−SC_risk) |
| Rt | Technological | 0.35·I_rd + 0.30·(1−D_leg) + 0.35·Ren_pat |
| Rf | Financial | 0.30·Liq + 0.25·(1−Lev) + 0.30·FCF_cov + 0.15·Cap_acc |
| Rc | Cognitive | 0.30·(1−Ten_ceo) + 0.25·Div_mgmt + 0.25·Rot_exec + 0.20·Innov_culture |

**Variables requiring analyst judgment (flag with κ ≥ 0.70):**
- D_leg: share of revenue from products >8yr old, R&D on maintenance vs. new
- Innov_culture: headcount in new business units / total

---

## §3. Environmental Pressure

```
Pe(t)     = 0.55·Pt + 0.30·Pc + 0.15·Preg         ∈ [0, 1]
Pe_eff(t) = Pe(t) · (1 + γ · Pe(t))                γ = 0.50
```

**Note:** Pe^θ (alternative) is mathematically incorrect for Pe ∈ [0,1] — it reduces Pe rather than amplifying it. The interaction formulation (1 + γ·Pe) guarantees Pe_eff > Pe for all Pe > 0 and monotonic amplification.

| Variable | Meaning | Range |
|----------|---------|-------|
| Pt | Fraction of core market captured by emerging tech | [0,1] |
| Pc | Revenue growth of top-3 competitors, normalized | [0,1] |
| Preg | Regulatory pressure | {0, 0.5, 1} |

---

## §4. Weight Derivation

```
wt_raw = CapEx/Revenue
ws_raw = HHI_revenue
wo_raw = min(DOL/10, 1)
wf_raw = min(ND_EBITDA/6, 1)
wc_raw = min(tenure_csuite_avg_years/12, 1)

wᵢ(t) = wᵢ_raw / Σ wⱼ_raw
```

---

## §5. Dynamic State Equation

```
R(t+1) = R(t)·(1−δ) + α·I(t) − β·G(t) + ΔR_jump(t)
```

| Parameter | Value | Meaning |
|-----------|-------|---------|
| δ | 0.04 | Natural resilience depreciation per period |
| α | 0.15 | Investment → resilience conversion rate |
| β | 0.10 | Growth inertia accumulation rate |
| ΔR_jump | exogenous | Adaptive jump term (non-zero only for Group B events) |

**Equilibrium:** R* = α·I* / (δ + β·G*)

---

## §6. Regime Boundaries

| Q | Regime | Interpretation |
|---|--------|----------------|
| Q > 0.15 | STABLE | Functional stability |
| −0.05 < Q ≤ 0.15 | TENSION | Adaptive pressure, manageable |
| −0.20 < Q ≤ −0.05 | FRAGILITY | Structural fragility growing |
| Q ≤ −0.20 | RUPTURE | Structural rupture — intervention required |

**LOO-calibrated two-threshold system:**
- Q ≈ +0.07 → empirical transition onset (first EWS signal window)
- Q ≈ −0.20 → structural rupture confirmation (0 false positives, n=5)

---

## §7. Early Warning Signals

Based on: Dakos et al. (2012, PLOS ONE); Scheffer et al. (2009, Nature)

```
EWS_var : σ(Q, window=4) / σ(Q, historical) > 1.50
EWS_ac  : AC₁(Q, window=4) > 0.70
EWS_csd : Δrecovery_time > 50% above historical average
```

**Sensitivity tested at windows {3, 4, 5} — results stable.**

---

## §8. Validation Protocol

### §8.1 Test Cases

| Group | Purpose | N |
|-------|---------|---|
| A — Collapses | Q should cross −0.20 before crisis event | 6 |
| B — Adaptive jumps | Q should approach but not cross −0.20 | 2 |
| C — Sustained | Q should remain > +0.28 throughout | 3 |

### §8.2 Pass Criteria

The model passes if:
- Q crosses −0.20 before the crisis event in ≥ 4/6 Group A cases
- Lead time ≥ 1 year in all passing cases
- False positives < 2 in Groups B+C

**Achieved:** 6/6 Group A pass · mean lead 4.3yr · 0 false positives

### §8.3 LOO Cross-Validation

For each Group A case `cᵢ`:
1. Estimate Q_crit from remaining 5 cases
2. Apply to `cᵢ`, record lead time
3. Check Groups B+C for false positives

Result: Q_crit mean = +0.07, std = 0.016 (stable across folds)

---

## §9. Known Limitations

1. Normalizations are internal (no sector peer group) — future: z-score sectorial
2. D_leg and Innov_culture require analyst judgment
3. Preg is a categorical variable in a continuous model
4. δ = 0.04 is a prior, not MLE-calibrated
5. ΔR_jump is exogenous — the model detects but does not predict adaptive jumps
6. Rot_exec is ambiguous during advanced crisis (exits may be involuntary)

---

## §10. Version History

| Version | Change |
|---------|--------|
| Ψ (v1) | Ψ = P/I·e^λt — diverged, no regime boundaries |
| v2.0 | Q = R − Pe, 4 dimensions, EWS added |
| v3.0 | + Rc dimension, + δ depreciation, Pe amplification corrected |
