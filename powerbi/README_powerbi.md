# Power BI Dashboard Guide
## HR Workforce Analytics Platform — University of Galway

---

## Data Model Setup

### Files to Import
Import all 8 CSV files from `data/cleaned/` and `data/real/`:

| File | Location | Type |
|------|----------|------|
| `employees.csv` | `data/cleaned/` | Synthetic — core fact table |
| `absences.csv` | `data/cleaned/` | Synthetic — transactional |
| `recruitment.csv` | `data/cleaned/` | Synthetic — transactional |
| `leavers.csv` | `data/cleaned/` | Synthetic — transactional |
| `training.csv` | `data/cleaned/` | Synthetic — transactional |
| `workforce_summary.csv` | `data/cleaned/` | Merged — synthetic vs real |
| `hea_uog_staff_profile.csv` | `data/real/` | Real — HEA benchmark |
| `cso_education_earnings_benchmark.csv` | `data/real/` | Real — CSO benchmark |

**Import method:** Get Data → Text/CSV → Comma delimited. Ensure date columns are detected as Date type.

---

### Relationship Diagram

Set up relationships in Model view (all one-to-many unless noted):

```
employees[employee_id]   → absences[employee_id]        (1:Many, Active)
employees[employee_id]   → leavers[employee_id]          (1:1,    Active)
employees[employee_id]   → training[employee_id]         (1:Many, Active)
employees[employee_id]   → recruitment[hired_employee_id](1:Many, Active, may have nulls)
employees[grade]         → hea_staff_profile[grade]      (Many:Many → resolved via summary)
employees[grade]         → workforce_summary[grade]      (Many:Many → resolved via summary)
```

**Cross-filter direction:** Single (employees → child tables).
Set `employees` as the anchor/hub table. All slicers on `employees` cascade to related tables.

---

### Star Schema Explanation

`employees` acts as the central **fact/dimension table** — it contains both descriptive attributes (grade, gender, department) and metrics (salary). All other tables join to it on `employee_id`.

```
            [absences]
                ↑
[recruitment] → [employees] ← [training]
                ↓
            [leavers]
```

The benchmark tables (`hea_staff_profile`, `cso_earnings_benchmark`) are disconnected reference tables — connect them to `workforce_summary` or reference them in DAX measures directly.

---

## DAX Measures

Create all measures in a dedicated **Measures table** (blank table named `_Measures`).

```dax
-- ── HEADCOUNT ──────────────────────────────────────────────────────────────

Total Headcount =
COUNTROWS(employees)

Active Headcount =
CALCULATE(
    COUNTROWS(employees),
    employees[status] = "Active"
)

Female Headcount =
CALCULATE([Active Headcount], employees[gender] = "Female")

Male Headcount =
CALCULATE([Active Headcount], employees[gender] = "Male")

Pct Female =
DIVIDE([Female Headcount], [Active Headcount])


-- ── TURNOVER ───────────────────────────────────────────────────────────────

Leavers Count =
COUNTROWS(leavers)

Turnover Rate % =
DIVIDE(
    [Leavers Count],
    DIVIDE([Active Headcount] + [Leavers Count], 2)
) * 100


-- ── ABSENCE ────────────────────────────────────────────────────────────────

Total Sick Days =
CALCULATE(
    SUM(absences[days_absent]),
    absences[absence_type] IN {"Certified Sick Leave", "Uncertified Sick Leave"}
)

Absence Rate % =
DIVIDE([Total Sick Days], [Active Headcount] * 230) * 100

Bradford Factor Avg =
AVERAGEX(
    SUMMARIZE(
        absences,
        absences[employee_id],
        "Spells", COUNTROWS(absences),
        "Days", SUM(absences[days_absent])
    ),
    [Spells]^2 * [Days]
)

RTW Compliance % =
VAR EligibleAbs =
    CALCULATE(
        COUNTROWS(absences),
        absences[absence_type] IN {"Certified Sick Leave", "Uncertified Sick Leave"},
        absences[days_absent] >= 3
    )
VAR RTWCompleted =
    CALCULATE(
        COUNTROWS(absences),
        absences[absence_type] IN {"Certified Sick Leave", "Uncertified Sick Leave"},
        absences[days_absent] >= 3,
        absences[return_to_work_interview] = TRUE()
    )
RETURN DIVIDE(RTWCompleted, EligibleAbs) * 100


-- ── GENDER PAY GAP ────────────────────────────────────────────────────────

Mean Salary Female =
CALCULATE(AVERAGE(employees[salary]), employees[gender] = "Female", employees[status] = "Active")

Mean Salary Male =
CALCULATE(AVERAGE(employees[salary]), employees[gender] = "Male", employees[status] = "Active")

Mean Gender Pay Gap % =
DIVIDE([Mean Salary Male] - [Mean Salary Female], [Mean Salary Male]) * 100

Median Salary Female =
CALCULATE(
    PERCENTILE.INC(employees[salary], 0.5),
    employees[gender] = "Female",
    employees[status] = "Active"
)

Median Salary Male =
CALCULATE(
    PERCENTILE.INC(employees[salary], 0.5),
    employees[gender] = "Male",
    employees[status] = "Active"
)

Median Gender Pay Gap % =
DIVIDE([Median Salary Male] - [Median Salary Female], [Median Salary Male]) * 100


-- ── RECRUITMENT ───────────────────────────────────────────────────────────

Avg Time to Fill =
CALCULATE(
    AVERAGE(recruitment[time_to_fill_days]),
    recruitment[outcome] = "Filled"
)

Avg Time to Fill Academic =
CALCULATE([Avg Time to Fill], recruitment[is_academic] = TRUE)

Avg Time to Fill Support =
CALCULATE([Avg Time to Fill], recruitment[is_academic] = FALSE)

Open Vacancies =
CALCULATE(COUNTROWS(recruitment), recruitment[outcome] = "Ongoing")

Fill Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(recruitment), recruitment[outcome] = "Filled"),
    COUNTROWS(recruitment)
) * 100


-- ── TRAINING ──────────────────────────────────────────────────────────────

Training Completion % =
DIVIDE(
    CALCULATE(COUNTROWS(training), training[passed] = TRUE()),
    COUNTROWS(training)
) * 100

Mandatory Training Compliance % =
VAR MandatoryEmployees =
    SUMMARIZE(
        FILTER(training, training[mandatory] = TRUE() && training[passed] = TRUE()),
        training[employee_id]
    )
RETURN
    DIVIDE(COUNTROWS(MandatoryEmployees), [Active Headcount]) * 100

Training Spend Total =
SUMX(training, training[cost_eur])

Training Spend Per Head =
DIVIDE([Training Spend Total], [Active Headcount])


-- ── RAG STATUS ────────────────────────────────────────────────────────────

Training RAG =
SWITCH(
    TRUE(),
    [Mandatory Training Compliance %] >= 95, "Green",
    [Mandatory Training Compliance %] >= 80, "Amber",
    "Red"
)

Absence RAG =
SWITCH(
    TRUE(),
    [Absence Rate %] < 3, "Green",
    [Absence Rate %] < 4.5, "Amber",
    "Red"
)
```

---

## Dashboard Pages

### Page 1: Executive Summary
**Purpose:** Board-level KPI snapshot. One-page executive view.

**Visuals:**
- 6× KPI Cards: Active Headcount | Turnover Rate % | Absence Rate % | Mean GPG % | Open Vacancies | Training Compliance %
- Clustered Column: Headcount by department (current year)
- Line Chart: Monthly starters vs leavers trend (2020–2024)
- Card: "Data based on HEA 2023 and CSO Q4 2024 published benchmarks"
- Gauge: Absence Rate % vs 4.5% public sector benchmark

**Slicers:** Year | Department | Employment Type

---

### Page 2: Workforce & Demographics
**Purpose:** Deep-dive on workforce composition and HEA benchmark comparison.

**Visuals:**
- Stacked Bar: Headcount by department split by employment type
- Clustered Bar (SHOWCASE): Synthetic headcount vs HEA real headcount by grade/gender
  - Use `workforce_summary[synthetic_headcount]` and `workforce_summary[real_hea_headcount]`
  - Add data label showing `variance_pct`
- 100% Stacked Bar: Gender distribution by grade (highlight professor level)
- Donut Chart: Employment type split (Permanent/Fixed-Term/Part-Time)
- Table: Grade-level salary ranges vs `benchmark_salary_band`

**Slicers:** Department | Gender | Academic vs Support | Campus

---

### Page 3: Absence & Wellbeing
**Purpose:** HR operations view of attendance patterns and intervention triggers.

**Visuals:**
- Matrix Heatmap: Department × Month (absence rate % values, conditional formatting)
  - Set heat scale: White=0%, Yellow=2%, Red=4.5%+
- Bar Chart: Top 10 employees by Bradford Factor score
- Line Chart: Certified vs Uncertified sick leave trend (monthly, 2021–2024)
- Card: RTW Interview Compliance % with target line at 95%
- Stacked Bar: Absence type breakdown by department

**Conditional formatting:** Bradford Factor — Red ≥450, Amber 100–449, Green <100

**Slicers:** Year | Department | Absence Type

---

### Page 4: Recruitment
**Purpose:** Talent acquisition performance and pipeline health.

**Visuals:**
- Funnel: Openings → Applications → Filled (by source)
- Clustered Box (approximated via scatter): Time to fill distribution — Academic vs Support
- Bar: Average time to fill by department
- Table: Source effectiveness (fill rate %, avg TTF, total opened)
- KPI Cards: Open Vacancies | Fill Rate % | Avg TTF Academic | Avg TTF Support
- Gauge: Avg TTF Academic vs 90-day target

**Slicers:** Year | Department | Academic vs Support | Outcome | Source

---

### Page 5: Gender Pay Gap Report
**Purpose:** Statutory disclosure view per Irish Gender Pay Gap Information Act 2021.

**Visuals:**
- Card Stack: Mean GPG % | Median GPG % | Mean Bonus Gap % | Median Bonus Gap %
- Clustered Bar: Mean salary Female vs Male by grade (sorted by gap size)
- Stacked Bar: Quartile pay band composition — Q1 to Q4 by gender %
  - Q4 typically shows highest male concentration (professor grade)
- Line: Year-on-year GPG trend (use hire_date year as proxy)
- Reference line: Irish HEI benchmark 16.2% (mean) / 12.8% (median)
- Text card: "Reported in accordance with the Gender Pay Gap Information Act 2021. Data represents synthetic records calibrated to HEA 2023 published figures."

**Slicers:** Grade | Department | Academic vs Support | Employment Type

---

### Page 6: Training & Compliance
**Purpose:** L&D investment and regulatory compliance monitoring.

**Visuals:**
- RAG Table: Department | Completion % | Mandatory Compliance % | RAG Status
  - Conditional formatting: Green ≥95%, Amber 80–94%, Red <80%
- Bar: Training completions by category
- Bar: Spend per employee by department (with €1,200 sector benchmark line)
- Pie: Provider split (Internal / External / Online / Skillnet)
- KPI Cards: Overall Completion % | Mandatory Compliance % | Total Spend | Spend per Head
- Table: Top 10 employees with zero mandatory training (compliance risk)

**Slicers:** Year | Department | Category | Provider | Mandatory (Yes/No)

---

## Slicer Panel (applies across all pages)

Create a consistent slicer panel on every page:

| Slicer | Field | Type |
|--------|-------|------|
| Year | `employees[hire_date].[Year]` | Dropdown |
| Department | `employees[department]` | List |
| Employment Type | `employees[employment_type]` | List |
| Academic vs Support | `employees[is_academic]` | Toggle/List |
| Campus | `employees[campus]` | Dropdown |
| Gender | `employees[gender]` | Dropdown |

---

## Conditional Formatting Rules

### Compliance RAG (Training, RTW):
- **Green:** Value ≥ 95%
- **Amber:** Value ≥ 80% and < 95%
- **Red:** Value < 80%

### Bradford Factor:
- **Green:** < 100
- **Amber:** 100–449
- **Red:** ≥ 450

### Absence Rate:
- **Green:** < 3%
- **Amber:** 3–4.5%
- **Red:** > 4.5%

### Gender Pay Gap:
- **Green:** < 10%
- **Amber:** 10–16%
- **Red:** > 16%

---

## Colour Theme

Apply University of Galway brand colours:
- Primary: `#8B1A2E` (maroon)
- Secondary: `#1F4E79` (navy blue)
- Neutral: `#F5F5F5` (light grey)
- Text: `#4A4A4A` (dark grey)

Import theme JSON in View → Themes → Browse for themes (create a custom theme file with these hex codes).

---

## Data Refresh

The dataset is static CSV files — no scheduled refresh needed. If you update the Python scripts and regenerate CSVs, use **Refresh** in Power BI Desktop to reload from the same file paths.

---

## Notes on Data Sources

All individual-level data (employees, absences, recruitment, leavers, training) is **synthetic** — generated for portfolio/demonstration purposes using statistically calibrated random generation.

Benchmark comparisons use **real published data**:
- HEA Staff Profiles by Gender 2023: https://hea.ie/policy/gender/statistics/
- CSO Earnings and Labour Costs Q4 2024: https://www.cso.ie/en/statistics/earningsandlabourcosts/
- Irish Gender Pay Gap Information Act 2021: https://www.gov.ie/en/publication/173e5-gender-pay-gap-information/
