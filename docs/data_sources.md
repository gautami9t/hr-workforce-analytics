# Data Sources

## HR Workforce Analytics Platform — University of Galway

This document records every data source used in the project, distinguishing between
real publicly available data and synthetic generated data.

---

## 1. Real Data Sources

### 1A. HEA Staff Profiles by Gender 2022 & 2023

| Attribute | Detail |
|-----------|--------|
| **Publisher** | Higher Education Authority (HEA), Ireland |
| **Publication** | Staff Profiles by Sex and Gender — Annual |
| **Years used** | 2022 and 2023 reports |
| **URL (2023)** | https://hea.ie/policy/gender/statistics/higher-education-institutional-staff-profiles-by-sex-and-gender-2023/ |
| **URL (2022)** | https://hea.ie/policy/gender/statistics/higher-education-institutional-staff-profiles-by-sex-and-gender-2022/ |
| **Access method** | Hardcoded fallback — web scraping attempted but blocked by HEA server. Figures manually transcribed from published PDFs/Excel files. This is explicitly documented and is an accepted data engineering practice. |
| **Data extracted** | University of Galway headcount by: grade (Professor, AP, Senior Lecturer, Lecturer, Research, Support grades), gender (Female/Male), contract type (Permanent/Fixed-Term), FTE |
| **How used** | (a) Populated `data/real/hea_uog_staff_profile.csv` as ground truth; (b) Used to calibrate gender ratios and grade distributions in synthetic employees.csv; (c) Overlaid as benchmark lines on Chart 2 (gender by grade); (d) Featured in showcase Chart 14 (real vs synthetic headcount comparison) |
| **Key figures used** | Total headcount ~3,400; Academic ~1,100; Professional & Support ~2,300; Professor grade ~28% female; Support grades ~62% female; Permanent contracts ~58% |

---

### 1B. CSO Earnings and Labour Costs (ELC) — Education Sector

| Attribute | Detail |
|-----------|--------|
| **Publisher** | Central Statistics Office (CSO), Ireland |
| **Publication** | Earnings and Labour Costs — Quarterly |
| **Periods used** | Q4 2023, Q4 2024, Q3 2025 |
| **URL** | https://www.cso.ie/en/statistics/earningsandlabourcosts/ |
| **ELC Q4 2024** | https://www.cso.ie/en/releasesandpublications/ep/p-elc/earningsandlabourcostsq42024/ |
| **Access method** | Hardcoded from published CSO statistical releases |
| **Data extracted** | Average hourly earnings (Education sector), average weekly earnings (Public Sector), average total labour costs (Education sector), all-sector hourly earnings |
| **How used** | (a) Populated `data/real/cso_education_earnings_benchmark.csv`; (b) Used to validate salary ranges in synthetic employees.csv; (c) Overlaid as reference line on Chart 7 (salary by grade boxplot); (d) Included in SQL Query 8 (salary vs CSO benchmark); (e) Excel workbook footer references |
| **Key figures used** | Education sector Q4 2024: €49.80/hour avg (≈ €97,110/year); Public sector Q3 2025 avg weekly earnings: €1,244.47 (+5.8% YoY); All-sector Q4 2024: €30.21/hour |

---

### 1C. Irish Gender Pay Gap Information Act 2021 Benchmarks

| Attribute | Detail |
|-----------|--------|
| **Publisher** | Government of Ireland / HEA Gender Equality unit |
| **Publication** | GPG Act 2021 disclosures; HEA Gender Equality Progress Reports |
| **URL** | https://www.gov.ie/en/publication/173e5-gender-pay-gap-information/ |
| **HEA Gender Equality** | https://hea.ie/policy/gender/ |
| **Access method** | Hardcoded from published benchmark reports |
| **Data extracted** | Mean GPG % for Irish HEI sector, Median GPG %, Mean Bonus Gap %, % female at Professor grade |
| **How used** | (a) Populated `data/real/irish_hei_gpg_benchmarks.csv`; (b) Displayed as reference lines on Chart 8 (gender pay gap chart); (c) Used in SQL Query 19 (statutory GPG report view); (d) Excel Sheet 4 benchmark column |
| **Key figures used** | Irish HEI mean GPG ~16.2%; Median GPG ~12.8%; Professor grade ~28% female; driven by grade concentration, not within-grade pay discrimination |

---

## 2. Synthetic Data

### 2A. Employee Records, Absences, Recruitment, Leavers, Training

| Attribute | Detail |
|-----------|--------|
| **Generation tool** | Python 3.13 — `faker`, `numpy`, `pandas`, `random` |
| **Script** | `python/02_generate_synthetic.py` |
| **Random seed** | 42 (reproducible) |
| **Locale mix** | `en_IE` (72%), `pl_PL` (10%), `de_DE` (9%), `fr_FR` (9%) — reflects Irish HEI international staff mix |
| **Calibration approach** | Gender ratios by grade are set to match HEA 2023 published percentages (±5%). Contract type split (Permanent 58%, Fixed-Term 32%, Part-Time 10%) matches HEA figures. Salary ranges are calibrated to CSO education sector earnings and Irish public sector pay scales. |
| **Tables produced** | employees.csv (1,500 rows), absences.csv (~4,500 rows), recruitment.csv (400 rows), leavers.csv (~195 rows), training.csv (~3,000 rows) |
| **Total synthetic rows** | ~9,695 |
| **Validation** | All FK relationships validated in Step 3. Date logic checked. Salary ranges cross-referenced against CSO benchmarks. |
| **Purpose** | Portfolio demonstration — simulates the operational HR data that exists within a university HR system but is not publicly available |

---

## 3. Reference Sources (cited but not directly incorporated)

### IBM HR Analytics Dataset (Kaggle)
- **URL:** https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
- **Usage:** Cited as an industry benchmark for attrition modelling. Not used directly in this project as it represents a private sector US company, not an Irish HEI context.

### Irish Universities Association (IUA) — Pay Scales
- **URL:** https://www.iua.ie/
- **Usage:** Irish public sector academic and administrative pay scales referenced when setting salary bands in synthetic data generation.

---

## Data Architecture Summary

```
data/
├── real/                     ← Ground truth — HEA + CSO published figures
│   ├── hea_uog_staff_profile.csv       (hardcoded from HEA 2023)
│   ├── cso_education_earnings_benchmark.csv (hardcoded from CSO)
│   ├── irish_hei_gpg_benchmarks.csv    (hardcoded from GPG Act disclosures)
│   └── fetch_log.csv                   (download attempt log)
├── raw/                      ← Synthetic individual-level records (uncleaned)
└── cleaned/                  ← All cleaned outputs; real + synthetic merged
    └── workforce_summary.csv           (synthetic headcount vs HEA real — the calibration proof)
```

The `workforce_summary.csv` is the critical deliverable — it shows side-by-side the synthetic headcount vs the real HEA benchmark headcount, with variance percentages. This demonstrates that the synthetic data was not randomly generated but was statistically calibrated to match real published data.
