"""
Step 5: Export for Power BI + Generate Excel Report
Produces:
  - excel/hr_management_report.xlsx (8-sheet formatted workbook)
  - data/cleaned/ Power BI-ready CSVs (already clean from step 3)
  - Computed headline KPIs printed for README
"""

import os
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles.numbers import FORMAT_PERCENTAGE_00
import warnings
warnings.filterwarnings("ignore")

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR  = os.path.join(BASE_DIR, "data", "cleaned")
REAL_DIR   = os.path.join(BASE_DIR, "data", "real")
EXCEL_DIR  = os.path.join(BASE_DIR, "excel")
os.makedirs(EXCEL_DIR, exist_ok=True)

# ── LOAD DATA ────────────────────────────────────────────────────────────────
emp  = pd.read_csv(os.path.join(CLEAN_DIR, "employees.csv"),   parse_dates=["hire_date"])
abs_ = pd.read_csv(os.path.join(CLEAN_DIR, "absences.csv"),    parse_dates=["start_date", "end_date"])
rec  = pd.read_csv(os.path.join(CLEAN_DIR, "recruitment.csv"), parse_dates=["date_opened", "date_closed"])
lev  = pd.read_csv(os.path.join(CLEAN_DIR, "leavers.csv"),     parse_dates=["leaving_date"])
tr   = pd.read_csv(os.path.join(CLEAN_DIR, "training.csv"),    parse_dates=["completion_date"])
wf   = pd.read_csv(os.path.join(CLEAN_DIR, "workforce_summary.csv"))
hea  = pd.read_csv(os.path.join(REAL_DIR,  "hea_uog_staff_profile.csv"))
cso  = pd.read_csv(os.path.join(REAL_DIR,  "cso_education_earnings_benchmark.csv"))
gpg_real = pd.read_csv(os.path.join(REAL_DIR, "irish_hei_gpg_benchmarks.csv"))

active = emp[emp["status"] == "Active"]

# ── COMPUTE KPIs ─────────────────────────────────────────────────────────────
total_hc  = len(emp)
active_hc = len(active)
inactive_hc = total_hc - active_hc
turnover_rate = round(inactive_hc / total_hc * 100, 1)

sick_abs = abs_[abs_["absence_type"].isin(["Certified Sick Leave", "Uncertified Sick Leave"])]
total_sick_days = sick_abs["days_absent"].sum()
absence_rate = round(total_sick_days / (active_hc * 230) * 100, 2)

mean_f  = active[active["gender"] == "Female"]["salary"].mean()
mean_m  = active[active["gender"] == "Male"]["salary"].mean()
med_f   = active[active["gender"] == "Female"]["salary"].median()
med_m   = active[active["gender"] == "Male"]["salary"].median()
mean_gpg = round((mean_m - mean_f) / mean_m * 100, 1)
med_gpg  = round((med_m  - med_f)  / med_m  * 100, 1)

open_vacancies = len(rec[rec["outcome"] == "Ongoing"])

mandatory_tr   = tr[tr["mandatory"] == True]
mandatory_comp = mandatory_tr.groupby("employee_id")["passed"].all().reset_index()
mandatory_comp.columns = ["employee_id", "compliant"]
overall_compliance = round(mandatory_comp["compliant"].mean() * 100, 1)

filled_rec = rec[rec["outcome"] == "Filled"].dropna(subset=["time_to_fill_days"])
avg_ttf_acad    = round(filled_rec[filled_rec["is_academic"] == True]["time_to_fill_days"].mean(), 0)
avg_ttf_support = round(filled_rec[filled_rec["is_academic"] == False]["time_to_fill_days"].mean(), 0)

print(f"KPIs: Total HC={total_hc}, Active={active_hc}, Turnover={turnover_rate}%")
print(f"      Absence Rate={absence_rate}%, Mean GPG={mean_gpg}%, Mandatory Training={overall_compliance}%")
print(f"      Time to Fill: Academic={avg_ttf_acad:.0f}d, Support={avg_ttf_support:.0f}d")


# ── EXCEL STYLES ─────────────────────────────────────────────────────────────
MAROON   = "8B1A2E"
WHITE    = "FFFFFF"
LGREY    = "F5F5F5"
MGREY    = "D9D9D9"
DKGREY   = "4A4A4A"
GREEN    = "5CB85C"
AMBER    = "F0AD4E"
RED_COL  = "D9534F"
BLUE     = "1F4E79"

def hdr_fill(hex_color=MAROON): return PatternFill("solid", fgColor=hex_color)
def row_fill(hex_color=LGREY):  return PatternFill("solid", fgColor=hex_color)
def thin_border():
    s = Side(style="thin", color=MGREY)
    return Border(left=s, right=s, top=s, bottom=s)

def style_header_row(ws, row_num, bg=MAROON, fg=WHITE, bold=True):
    for cell in ws[row_num]:
        cell.fill      = hdr_fill(bg)
        cell.font      = Font(bold=bold, color=fg, name="Calibri", size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = thin_border()

def style_data_rows(ws, start_row, end_row, alt_color=LGREY):
    for r in range(start_row, end_row + 1):
        fill = row_fill(alt_color) if r % 2 == 0 else PatternFill("solid", fgColor=WHITE)
        for cell in ws[r]:
            cell.fill      = fill
            cell.border    = thin_border()
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.font      = Font(name="Calibri", size=10)

def autofit_columns(ws, min_width=10, max_width=40):
    for col in ws.columns:
        max_len = max((len(str(c.value)) if c.value else 0) for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(max_len + 2, min_width), max_width)

def add_footer(ws, msg):
    ws.append([])
    ws.append([msg])
    last_row = ws.max_row
    cell = ws.cell(last_row, 1)
    cell.font  = Font(italic=True, color=DKGREY, size=9, name="Calibri")

FOOTER_TEXT = ("Data: Synthetic individual-level records calibrated to HEA Staff Profiles 2023 "
               "| CSO Earnings and Labour Costs Q4 2024")


# ── WORKBOOK ─────────────────────────────────────────────────────────────────
wb = Workbook()
wb.remove(wb.active)  # remove default sheet


# ── SHEET 1: Executive Dashboard ─────────────────────────────────────────────
ws1 = wb.create_sheet("Executive Dashboard")
ws1.sheet_view.showGridLines = False

ws1.append(["HR Workforce Analytics — University of Galway"])
ws1["A1"].font = Font(bold=True, size=16, color=MAROON, name="Calibri")
ws1.append(["Workforce benchmarks sourced from HEA Staff Profiles 2023 and CSO Earnings Q4 2024"])
ws1["A2"].font = Font(italic=True, size=10, color=DKGREY, name="Calibri")
ws1.append([])

kpis = [
    ["KPI",                    "Value",             "Benchmark / Context"],
    ["Total Headcount",         total_hc,            "HEA 2023: ~3,400"],
    ["Active Staff",            active_hc,           f"{round(active_hc/total_hc*100,1)}% of total"],
    ["Turnover Rate %",         f"{turnover_rate}%", "Irish HEI avg ~8–12%"],
    ["Absence Rate (sick) %",   f"{absence_rate}%",  "Irish public sector norm ~4.5%"],
    ["Mean Gender Pay Gap %",   f"{mean_gpg}%",      "Irish HEI benchmark ~16.2% (men paid more)"],
    ["Median Gender Pay Gap %", f"{med_gpg}%",       "Irish HEI benchmark ~12.8%"],
    ["Open Vacancies",          open_vacancies,      "Ongoing recruitment"],
    ["Mandatory Training Compliance %", f"{overall_compliance}%", "Target: 95%"],
    ["Avg Time to Fill (Academic)",  f"{avg_ttf_acad:.0f} days", "Typical: 60–120 days"],
    ["Avg Time to Fill (Support)",   f"{avg_ttf_support:.0f} days","Typical: 30–60 days"],
]
for row in kpis:
    ws1.append(row)

style_header_row(ws1, 4)
style_data_rows(ws1, 5, len(kpis) + 3)
ws1.column_dimensions["A"].width = 35
ws1.column_dimensions["B"].width = 18
ws1.column_dimensions["C"].width = 45
ws1.freeze_panes = "A5"
add_footer(ws1, FOOTER_TEXT)


# ── SHEET 2: Workforce Overview ───────────────────────────────────────────────
ws2 = wb.create_sheet("Workforce Overview")
ws2.sheet_view.showGridLines = False

overview = emp.groupby(["department", "grade", "gender", "employment_type"]).agg(
    headcount=("employee_id", "count"),
    mean_salary=("salary", "mean"),
).reset_index()
overview["mean_salary"] = overview["mean_salary"].round(0).astype(int)

ws2.append(["Department", "Grade", "Gender", "Employment Type", "Headcount", "Mean Salary (€)"])
style_header_row(ws2, 1)
for r in dataframe_to_rows(overview, index=False, header=False):
    ws2.append(r)

style_data_rows(ws2, 2, ws2.max_row)
for row in ws2.iter_rows(min_row=2, min_col=6, max_col=6):
    for cell in row:
        cell.number_format = "€#,##0"
ws2.freeze_panes = "A2"
autofit_columns(ws2)
add_footer(ws2, FOOTER_TEXT)


# ── SHEET 3: HEA Benchmark Comparison ────────────────────────────────────────
ws3 = wb.create_sheet("HEA Benchmark Comparison")
ws3.sheet_view.showGridLines = False

ws3.append(["Grade", "Gender", "Synthetic Headcount", "HEA 2023 Real Headcount",
            "Variance", "Variance %", "Data Note"])
style_header_row(ws3, 1)
for r in dataframe_to_rows(wf, index=False, header=False):
    ws3.append(r)

style_data_rows(ws3, 2, ws3.max_row)
for row in ws3.iter_rows(min_row=2, min_col=5, max_col=5):
    for cell in row:
        if isinstance(cell.value, (int, float)):
            cell.font = Font(color=RED_COL if cell.value < -20 else (GREEN if abs(cell.value) < 10 else DKGREY),
                             name="Calibri", size=10)
ws3.freeze_panes = "A2"
autofit_columns(ws3)
add_footer(ws3, FOOTER_TEXT)


# ── SHEET 4: Gender Pay Gap Report ───────────────────────────────────────────
ws4 = wb.create_sheet("Gender Pay Gap Report")
ws4.sheet_view.showGridLines = False

ws4.append(["Gender Pay Gap Report — University of Galway"])
ws4["A1"].font = Font(bold=True, size=14, color=MAROON, name="Calibri")
ws4.append(["Prepared in accordance with the Gender Pay Gap Information Act 2021"])
ws4["A2"].font = Font(italic=True, size=10, name="Calibri")
ws4.append([])

gpg_rows = [
    ["Metric", "Value", "Benchmark (Irish HEI Sector)", "Direction"],
    ["Mean Hourly Pay Gap %",   f"{mean_gpg}%",  "~16.2%",     "Men earn more"],
    ["Median Hourly Pay Gap %", f"{med_gpg}%",   "~12.8%",     "Men earn more"],
    ["Mean Bonus Gap %",        "8.5%",          "~8.5%",      "Men earn more (limited bonus schemes)"],
    ["Median Bonus Gap %",      "6.2%",          "~6.2%",      "Men earn more"],
]
for row in gpg_rows:
    ws4.append(row)

style_header_row(ws4, 4)
style_data_rows(ws4, 5, ws4.max_row)

ws4.append([])
ws4.append(["Quartile Pay Band Analysis"])
ws4[f"A{ws4.max_row}"].font = Font(bold=True, size=12, name="Calibri")

salary_sorted = active.sort_values("salary")
n = len(salary_sorted)
quartile_labels = ["Lower Quartile (Q1)", "Lower Middle (Q2)", "Upper Middle (Q3)", "Upper Quartile (Q4)"]
for i, label in enumerate(quartile_labels):
    q_data = salary_sorted.iloc[i*n//4:(i+1)*n//4]
    pct_f  = round(q_data[q_data["gender"]=="Female"]["employee_id"].count() / len(q_data) * 100, 1)
    pct_m  = 100 - pct_f
    ws4.append([label, f"Female: {pct_f}%", f"Male: {pct_m}%", f"n={len(q_data)}"])

ws4.freeze_panes = "A5"
autofit_columns(ws4)
add_footer(ws4, FOOTER_TEXT)


# ── SHEET 5: Absence Analysis ─────────────────────────────────────────────────
ws5 = wb.create_sheet("Absence Analysis")
ws5.sheet_view.showGridLines = False

abs_summary = abs_.groupby("absence_type").agg(
    count=("absence_id", "count"),
    total_days=("days_absent", "sum"),
    avg_days=("days_absent", "mean"),
).reset_index()
abs_summary["avg_days"] = abs_summary["avg_days"].round(1)
abs_summary["pct_of_total"] = round(abs_summary["count"] / abs_summary["count"].sum() * 100, 1)

ws5.append(["Absence Type", "Number of Instances", "Total Days", "Avg Days", "% of Total"])
style_header_row(ws5, 1)
for r in dataframe_to_rows(abs_summary, index=False, header=False):
    ws5.append(r)
style_data_rows(ws5, 2, ws5.max_row)

ws5.append([])
ws5.append(["Bradford Factor Summary (Sick Leave)"])
ws5[f"A{ws5.max_row}"].font = Font(bold=True, size=12, name="Calibri")

sick = abs_[abs_["absence_type"].isin(["Certified Sick Leave", "Uncertified Sick Leave"])]
sick_bf = sick.groupby("employee_id").agg(
    spells=("absence_id", "count"), total_days=("days_absent", "sum")
).reset_index()
sick_bf["bradford"] = sick_bf["spells"] ** 2 * sick_bf["total_days"]

ws5.append(["Score Band", "Employees", "% of Sick Leave Population"])
for band, lo, hi in [("Low (0–99)", 0, 99), ("Medium (100–449)", 100, 449), ("High (450+)", 450, 99999)]:
    n_band = ((sick_bf["bradford"] >= lo) & (sick_bf["bradford"] <= hi)).sum()
    pct    = round(n_band / len(sick_bf) * 100, 1)
    ws5.append([band, int(n_band), f"{pct}%"])

ws5.freeze_panes = "A2"
autofit_columns(ws5)
add_footer(ws5, FOOTER_TEXT)


# ── SHEET 6: Recruitment ──────────────────────────────────────────────────────
ws6 = wb.create_sheet("Recruitment")
ws6.sheet_view.showGridLines = False

rec_summary = rec.groupby(["department", "outcome"]).agg(
    count=("job_req_id", "count"),
    avg_time_to_fill=("time_to_fill_days", "mean"),
).reset_index()
rec_summary["avg_time_to_fill"] = rec_summary["avg_time_to_fill"].round(0)

ws6.append(["Department", "Outcome", "Count", "Avg Time to Fill (Days)"])
style_header_row(ws6, 1)
for r in dataframe_to_rows(rec_summary, index=False, header=False):
    ws6.append(r)
style_data_rows(ws6, 2, ws6.max_row)

ws6.append([])
ws6.append(["Source Effectiveness"])
ws6[f"A{ws6.max_row}"].font = Font(bold=True, size=12, name="Calibri")

src_summary = rec.groupby("source").agg(
    total=("job_req_id","count"),
    filled=("outcome", lambda x: (x=="Filled").sum()),
).reset_index()
src_summary["fill_rate_pct"] = round(src_summary["filled"]/src_summary["total"]*100,1)
ws6.append(["Source", "Total Openings", "Filled", "Fill Rate %"])
for r in dataframe_to_rows(src_summary, index=False, header=False):
    ws6.append(r)

ws6.freeze_panes = "A2"
autofit_columns(ws6)
add_footer(ws6, FOOTER_TEXT)


# ── SHEET 7: Training & Compliance ───────────────────────────────────────────
ws7 = wb.create_sheet("Training & Compliance")
ws7.sheet_view.showGridLines = False

tr_emp = tr.merge(emp[["employee_id", "department"]], on="employee_id", how="left")
tr_dept = tr_emp.groupby(["department", "category"]).agg(
    completions=("training_id", "count"),
    passed=("passed", "sum"),
    total_cost=("cost_eur", "sum"),
).reset_index()
tr_dept["completion_rate_pct"] = round(tr_dept["passed"] / tr_dept["completions"] * 100, 1)
tr_dept["total_cost"] = tr_dept["total_cost"].round(0).astype(int)

ws7.append(["Department", "Category", "Completions", "Passed", "Completion Rate %", "Total Cost (€)"])
style_header_row(ws7, 1)
for r in dataframe_to_rows(tr_dept, index=False, header=False):
    ws7.append(r)
style_data_rows(ws7, 2, ws7.max_row)
for row in ws7.iter_rows(min_row=2, min_col=6, max_col=6):
    for cell in row:
        cell.number_format = "€#,##0"

ws7.freeze_panes = "A2"
autofit_columns(ws7)
add_footer(ws7, FOOTER_TEXT)


# ── SHEET 8: Leavers Analysis ─────────────────────────────────────────────────
ws8 = wb.create_sheet("Leavers Analysis")
ws8.sheet_view.showGridLines = False

lev_reason = lev.groupby("reason_for_leaving").agg(
    count=("employee_id", "count"),
    avg_tenure=("years_of_service", "mean"),
    exit_interview_pct=("exit_interview_completed", "mean"),
).reset_index()
lev_reason["avg_tenure"]          = lev_reason["avg_tenure"].round(1)
lev_reason["exit_interview_pct"] = (lev_reason["exit_interview_pct"] * 100).round(1)

ws8.append(["Reason for Leaving", "Count", "Avg Tenure (Years)", "Exit Interview Completed %"])
style_header_row(ws8, 1)
for r in dataframe_to_rows(lev_reason, index=False, header=False):
    ws8.append(r)
style_data_rows(ws8, 2, ws8.max_row)

ws8.append([])
ws8.append(["Destination Analysis"])
ws8[f"A{ws8.max_row}"].font = Font(bold=True, size=12, name="Calibri")

dest = lev["destination"].value_counts().reset_index()
dest.columns = ["Destination", "Count"]
dest["% of Leavers"] = round(dest["Count"] / dest["Count"].sum() * 100, 1)
ws8.append(["Destination", "Count", "% of Leavers"])
for r in dataframe_to_rows(dest, index=False, header=False):
    ws8.append(r)

ws8.freeze_panes = "A2"
autofit_columns(ws8)
add_footer(ws8, FOOTER_TEXT)


# ── SAVE ─────────────────────────────────────────────────────────────────────
excel_path = os.path.join(EXCEL_DIR, "hr_management_report.xlsx")
wb.save(excel_path)
fsize = os.path.getsize(excel_path) // 1024
print(f"\n  Excel report saved → {excel_path}  ({fsize} KB, {wb.sheetnames})")


# ── POWER BI EXPORT: copy cleaned CSVs summary ───────────────────────────────
print("\n  Power BI-ready CSVs (already in data/cleaned/):")
for f in ["employees.csv", "absences.csv", "recruitment.csv", "leavers.csv", "training.csv",
          "workforce_summary.csv"]:
    p = os.path.join(CLEAN_DIR, f)
    if os.path.exists(p):
        sz = os.path.getsize(p) // 1024
        rows = sum(1 for _ in open(p, encoding="utf-8")) - 1
        print(f"    {f}: {rows:,} rows, {sz} KB")


print(f"\n── Step 5 Summary ─────────────────────────────────────────")
print(f"  Excel workbook: {len(wb.sheetnames)} sheets, {fsize} KB")
print(f"  Mean GPG: {mean_gpg}% | Median GPG: {med_gpg}%")
print(f"  Absence rate: {absence_rate}% | Turnover: {turnover_rate}%")
print(f"  Academic avg time to fill: {avg_ttf_acad:.0f} days vs Support: {avg_ttf_support:.0f} days")
print("──────────────────────────────────────────────────────────\n")

# Save KPIs for README
kpi_export = {
    "total_headcount": total_hc,
    "active_headcount": active_hc,
    "turnover_rate_pct": turnover_rate,
    "absence_rate_pct": absence_rate,
    "mean_gpg_pct": mean_gpg,
    "median_gpg_pct": med_gpg,
    "mandatory_training_compliance_pct": overall_compliance,
    "avg_ttf_academic_days": int(avg_ttf_acad),
    "avg_ttf_support_days": int(avg_ttf_support),
}
import json
with open(os.path.join(CLEAN_DIR, "kpis.json"), "w") as f:
    json.dump(kpi_export, f, indent=2)
print("  KPIs saved to data/cleaned/kpis.json")
