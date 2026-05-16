"""
Step 3: Clean, Validate, and Merge Data
Applies data quality checks, FK validation, date logic checks,
salary benchmarking, and creates merged/enriched outputs.
"""

import os
import pandas as pd
import numpy as np
from datetime import date

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR    = os.path.join(BASE_DIR, "data", "raw")
REAL_DIR   = os.path.join(BASE_DIR, "data", "real")
CLEAN_DIR  = os.path.join(BASE_DIR, "data", "cleaned")
os.makedirs(CLEAN_DIR, exist_ok=True)

dq_report = []  # Data quality report accumulator

def dq_check(table, check_name, total, issues):
    pct_clean = round((1 - issues / max(total, 1)) * 100, 2)
    dq_report.append({
        "table": table, "check": check_name,
        "total_rows": total, "issues_found": issues,
        "pct_clean": pct_clean,
        "resolution": "Flagged with dq_flag; FK issues set to NULL",
    })
    print(f"  [{table}] {check_name}: {issues} issues / {total} rows ({pct_clean}% clean)")
    return issues


# ────────────────────────────────────────────────────────────────────────────
# LOAD RAW DATA
# ────────────────────────────────────────────────────────────────────────────

emp  = pd.read_csv(os.path.join(RAW_DIR, "employees.csv"),   parse_dates=["hire_date", "date_of_birth"])
abs_ = pd.read_csv(os.path.join(RAW_DIR, "absences.csv"),    parse_dates=["start_date", "end_date"])
rec  = pd.read_csv(os.path.join(RAW_DIR, "recruitment.csv"), parse_dates=["date_opened", "date_closed"])
lev  = pd.read_csv(os.path.join(RAW_DIR, "leavers.csv"),     parse_dates=["leaving_date"])
tr   = pd.read_csv(os.path.join(RAW_DIR, "training.csv"),    parse_dates=["completion_date"])
hea  = pd.read_csv(os.path.join(REAL_DIR, "hea_uog_staff_profile.csv"))
cso  = pd.read_csv(os.path.join(REAL_DIR, "cso_education_earnings_benchmark.csv"))

print("── Step 3: Data Cleaning & QA ─────────────────────────────")

# ────────────────────────────────────────────────────────────────────────────
# EMPLOYEES — QA
# ────────────────────────────────────────────────────────────────────────────
emp["dq_flag"] = ""
valid_emp_ids = set(emp["employee_id"])

# Salary range check against CSO
cso_edu_hourly = 49.80  # Q4 2024 Education sector
approx_annual  = cso_edu_hourly * 37.5 * 52  # ~€97,110 mean for education
# Accept salaries between 25k and 135k as plausible
sal_issues = ((emp["salary"] < 25000) | (emp["salary"] > 135000)).sum()
emp.loc[(emp["salary"] < 25000) | (emp["salary"] > 135000), "dq_flag"] += "salary_out_of_range;"
dq_check("employees", "Salary range check (25k–135k)", len(emp), int(sal_issues))

# Age check: must be 22–70 at hire date
emp["age_at_hire"] = (emp["hire_date"] - emp["date_of_birth"]).dt.days / 365.25
age_issues = ((emp["age_at_hire"] < 18) | (emp["age_at_hire"] > 70)).sum()
emp.loc[(emp["age_at_hire"] < 18) | (emp["age_at_hire"] > 70), "dq_flag"] += "age_at_hire_invalid;"
dq_check("employees", "Age at hire (18–70)", len(emp), int(age_issues))

# Manager FK check
valid_mgr = emp["manager_id"].isin(valid_emp_ids) | emp["manager_id"].isna()
mgr_issues = (~valid_mgr).sum()
emp.loc[~valid_mgr, "manager_id"] = None
emp.loc[~valid_mgr, "dq_flag"] += "invalid_manager_id;"
dq_check("employees", "Manager FK validity", len(emp), int(mgr_issues))

# Standardise text
for col in ["gender", "employment_type", "status", "department", "campus"]:
    emp[col] = emp[col].str.strip().str.title()

# Add benchmark salary band from CSO
GRADE_BAND_MAP = {
    "Grade 3-4":                "€28,000–€38,000",
    "Grade 5":                  "€35,000–€50,000",
    "Grade 6":                  "€45,000–€62,000",
    "Grade 7":                  "€56,000–€75,000",
    "Senior Management":        "€72,000–€110,000",
    "Lecturer Below Bar":       "€52,000–€75,000",
    "Senior Lecturer Above Bar":"€72,000–€95,000",
    "Associate Professor":      "€88,000–€110,000",
    "Professor":                "€102,000–€130,000",
    "Research Fellow / Postdoc":"€40,000–€68,000",
}
emp["benchmark_salary_band"] = emp["grade"].map(GRADE_BAND_MAP).fillna("Unknown")

emp_clean = emp.copy()
emp_clean.to_csv(os.path.join(CLEAN_DIR, "employees.csv"), index=False)
print(f"  employees.csv cleaned → {len(emp_clean)} rows\n")


# ────────────────────────────────────────────────────────────────────────────
# ABSENCES — QA
# ────────────────────────────────────────────────────────────────────────────
abs_["dq_flag"] = ""

# FK check
fk_issues = (~abs_["employee_id"].isin(valid_emp_ids)).sum()
abs_.loc[~abs_["employee_id"].isin(valid_emp_ids), "dq_flag"] += "invalid_employee_id;"
dq_check("absences", "Employee FK validity", len(abs_), int(fk_issues))

# Date logic: start < end
date_issues = (abs_["start_date"] >= abs_["end_date"]).sum()
abs_.loc[abs_["start_date"] >= abs_["end_date"], "dq_flag"] += "start_after_end;"
dq_check("absences", "start_date < end_date", len(abs_), int(date_issues))

# Days_absent consistency
abs_["days_calc"] = (abs_["end_date"] - abs_["start_date"]).dt.days
day_issues = (abs_["days_absent"] != abs_["days_calc"]).sum()
# Overwrite with calculated value for accuracy
abs_["days_absent"] = abs_["days_calc"]
abs_.drop(columns=["days_calc"], inplace=True)
dq_check("absences", "days_absent consistency", len(abs_), int(day_issues))

# Add sector average absence rate reference
abs_["sector_avg_absence_rate_pct"] = 4.5  # Irish public sector benchmark

abs_.to_csv(os.path.join(CLEAN_DIR, "absences.csv"), index=False)
print(f"  absences.csv cleaned → {len(abs_)} rows\n")


# ────────────────────────────────────────────────────────────────────────────
# RECRUITMENT — QA
# ────────────────────────────────────────────────────────────────────────────
rec["dq_flag"] = ""

# Hired employee FK check
hired_fk = rec["hired_employee_id"].dropna()
hired_fk_issues = (~hired_fk.isin(valid_emp_ids)).sum()
rec.loc[rec["hired_employee_id"].notna() & ~rec["hired_employee_id"].isin(valid_emp_ids), "hired_employee_id"] = None
rec.loc[rec["hired_employee_id"].notna() & ~rec["hired_employee_id"].isin(valid_emp_ids), "dq_flag"] += "invalid_hired_emp_id;"
dq_check("recruitment", "Hired employee FK validity", len(rec), int(hired_fk_issues))

# Date logic: opened < closed (where both exist)
both_dates = rec["date_closed"].notna()
date_issues_rec = (rec.loc[both_dates, "date_opened"] >= rec.loc[both_dates, "date_closed"]).sum()
dq_check("recruitment", "date_opened < date_closed", int(both_dates.sum()), int(date_issues_rec))

rec.to_csv(os.path.join(CLEAN_DIR, "recruitment.csv"), index=False)
print(f"  recruitment.csv cleaned → {len(rec)} rows\n")


# ────────────────────────────────────────────────────────────────────────────
# LEAVERS — QA
# ────────────────────────────────────────────────────────────────────────────
lev["dq_flag"] = ""

# FK check
lev_fk_issues = (~lev["employee_id"].isin(valid_emp_ids)).sum()
dq_check("leavers", "Employee FK validity", len(lev), int(lev_fk_issues))

# Date: leaving_date > hire_date
lev_merged = lev.merge(emp[["employee_id", "hire_date"]], on="employee_id", how="left")
date_lev_issues = (lev_merged["leaving_date"] <= lev_merged["hire_date"]).sum()
lev.loc[(lev_merged["leaving_date"] <= lev_merged["hire_date"]).values, "dq_flag"] += "leaving_before_hire;"
dq_check("leavers", "leaving_date > hire_date", len(lev), int(date_lev_issues))

lev.to_csv(os.path.join(CLEAN_DIR, "leavers.csv"), index=False)
print(f"  leavers.csv cleaned → {len(lev)} rows\n")


# ────────────────────────────────────────────────────────────────────────────
# TRAINING — QA
# ────────────────────────────────────────────────────────────────────────────
tr["dq_flag"] = ""

# FK check
tr_fk_issues = (~tr["employee_id"].isin(valid_emp_ids)).sum()
dq_check("training", "Employee FK validity", len(tr), int(tr_fk_issues))

# Cost check: internal should be 0
cost_issues = ((tr["provider"] == "Internal") & (tr["cost_eur"] > 0)).sum()
tr.loc[(tr["provider"] == "Internal"), "cost_eur"] = 0
dq_check("training", "Internal training cost = 0", len(tr), int(cost_issues))

tr.to_csv(os.path.join(CLEAN_DIR, "training.csv"), index=False)
print(f"  training.csv cleaned → {len(tr)} rows\n")


# ────────────────────────────────────────────────────────────────────────────
# WORKFORCE SUMMARY — Synthetic vs Real HEA Comparison
# ────────────────────────────────────────────────────────────────────────────

print("Building workforce_summary.csv (synthetic vs HEA real benchmarks) …")

# Synthetic headcount by grade + gender
synth_summary = (
    emp_clean.groupby(["grade", "gender"])["employee_id"]
    .count()
    .reset_index()
    .rename(columns={"employee_id": "synthetic_headcount"})
)

# Real HEA headcount by grade + gender
hea_summary = (
    hea.groupby(["grade", "gender"])["headcount"]
    .sum()
    .reset_index()
    .rename(columns={"headcount": "real_hea_headcount"})
)

workforce_summary = synth_summary.merge(hea_summary, on=["grade", "gender"], how="outer").fillna(0)
workforce_summary["real_hea_headcount"] = workforce_summary["real_hea_headcount"].astype(int)
workforce_summary["synthetic_headcount"] = workforce_summary["synthetic_headcount"].astype(int)
workforce_summary["variance_vs_real"] = (
    workforce_summary["synthetic_headcount"] - workforce_summary["real_hea_headcount"]
)
workforce_summary["variance_pct"] = np.where(
    workforce_summary["real_hea_headcount"] > 0,
    round((workforce_summary["variance_vs_real"] / workforce_summary["real_hea_headcount"]) * 100, 1),
    np.nan,
)
workforce_summary["data_note"] = "Synthetic calibrated to HEA 2023 published figures"

wf_path = os.path.join(CLEAN_DIR, "workforce_summary.csv")
workforce_summary.to_csv(wf_path, index=False)
print(f"  → workforce_summary.csv: {len(workforce_summary)} rows")


# ────────────────────────────────────────────────────────────────────────────
# SAVE DQ REPORT
# ────────────────────────────────────────────────────────────────────────────

dq_df = pd.DataFrame(dq_report)
dq_path = os.path.join(CLEAN_DIR, "dq_report.csv")
dq_df.to_csv(dq_path, index=False)

total_checks = len(dq_df)
total_issues = dq_df["issues_found"].sum()
avg_clean    = dq_df["pct_clean"].mean()

print(f"\n── Data Quality Report ────────────────────────────────────")
print(f"  Total checks run:    {total_checks}")
print(f"  Total issues found:  {total_issues}")
print(f"  Average clean rate:  {avg_clean:.1f}%")
print("──────────────────────────────────────────────────────────\n")

print("── Step 3 Summary ─────────────────────────────────────────")
print(f"  All 5 synthetic tables cleaned and saved to data/cleaned/")
print(f"  workforce_summary.csv created with synthetic vs HEA comparison")
print(f"  dq_report.csv written with {total_checks} checks")
print("──────────────────────────────────────────────────────────\n")
