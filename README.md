# seldon-corporate

> *"The fall of Empire is a massive thing, however, and not easily fought. It is dictated by a rising bureaucracy, a receding initiative, a freezing of caste, a damming of curiosity — a hundred other factors."*
> — Isaac Asimov, Foundation

Organizational resilience framework for detecting strategic fragility **before** it appears in financial statements.

**Interactive observatory →** https://rainvare.github.io/seldon-corporate

---

## Core equation

```
Q(t) = R_scalar(t) - Pe(t) × (1 + 0.5 × Pe(t))
```

| Q | Regime |
|---|--------|
| Q > 0.15 | Functional Stability |
| −0.05 ≤ Q ≤ 0.15 | Tension |
| −0.20 ≤ Q < −0.05 | Fragility |
| Q < −0.20 | **Structural Rupture** |

---

## Validation (11 cases, 3 groups)

| Group | Companies | Result |
|-------|-----------|--------|
| A — Collapses | Samsung, Nokia, Kodak, BlackBerry, Blockbuster, Yahoo | 6/6 detected · mean lead 4.3yr |
| B — Adaptive jumps | Microsoft, Netflix | 0/2 false positives |
| C — Sustained resilience | Amazon, Toyota, TSMC | Q > +0.28 throughout |

**LOO cross-validation:** Q_crit = +0.07 (std=0.016) · 0 false positives

---

## Repo structure

```
seldon-corporate/
├── README.md
├── THEORY.md               ← Mathematical specification v3.0
├── DECISIONS.md            ← Methodological design decisions
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── seldon/
│   ├── __init__.py
│   └── model.py
├── data/
│   ├── schema.json
│   ├── samsung_2019_2024.csv
│   ├── nokia_2007_2013.csv
│   ├── kodak_1998_2012.csv
│   ├── blackberry_2010_2016.csv
│   ├── blockbuster_2004_2010.csv
│   ├── yahoo_2008_2016.csv
│   ├── microsoft_2010_2020.csv
│   ├── netflix_2008_2018.csv
│   ├── amazon_2010_2020.csv
│   ├── toyota_2005_2020.csv
│   └── tsmc_2010_2020.csv
├── scripts/
│   └── loo_calibration.py
├── paper/
│   └── seldon_paper_v1.md
└── web/
    └── index.html
```

---

## Five resilience dimensions

| Code | Name | Theoretical basis |
|------|------|-------------------|
| Rs | Strategic | Hamel & Välikangas (2003) |
| Ro | Operational | Weick (1993) |
| Rt | Technological | Christensen (1997) |
| Rf | Financial | Altman (1968) |
| **Rc** | **Cognitive** | **Hambrick & Fukutomi (1991)** |

**Key finding:** Nokia, Kodak, Yahoo, Blockbuster all had Rf ≥ 0.40 at rupture detection. The binding constraint was cognitive, not financial.

---

## Quick start

```python
from seldon.model import ResilienceVector, EnvironmentalPressure, Period

weights = {'Rs': 0.25, 'Ro': 0.20, 'Rt': 0.25, 'Rf': 0.05, 'Rc': 0.25}

period = Period(
    year=2024,
    dims=ResilienceVector(Rs=0.55, Ro=0.60, Rt=0.45, Rf=0.70, Rc=0.40),
    pressure=EnvironmentalPressure(Pt=0.42, Pc=0.50, Preg=0.0),
    weights=weights
)

print(f"Q = {period.Q:.3f} · {period.regime}")
```

## Run LOO calibration

```bash
PYTHONPATH=. python3 scripts/loo_calibration.py
```

---

*Framework design: R. Indira Valentina Réquiz Molina · 2026 · v3.0*
