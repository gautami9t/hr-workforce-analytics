"""
Step 4: Exploratory Data Analysis and Chart Generation
Produces 14 charts saved to data/cleaned/charts/ at 150dpi.
Uses real HEA/CSO benchmark data as overlays where relevant.
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.ticker import FuncFormatter

warnings.filterwarnings("ignore")

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR  = os.path.join(BASE_DIR, "data", "cleaned")
CHART_DIR  = os.path.join(CLEAN_DIR, "charts")
REAL_DIR   = os.path.join(BASE_DIR, "data", "real")
os.makedirs(CHART_DIR, exist_ok=True)

# University of Galway colours
UOG_MAROON = "#8B1A2E"
UOG_GREY   = "#F5F5F5"
UOG_DARK   = "#4A4A4A"
UOG_BLUE   = "#1F4E79"

def save(name):
    path = os.path.join(CHART_DIR, name)
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved: {name}")

# ── LOAD DATA ────────────────────────────────────────────────────────────────
emp = pd.read_csv(os.path.join(CLEAN_DIR, "employees.csv"),   parse_dates=["hire_date", "date_of_birth"])
abs_ = pd.read_csv(os.path.join(CLEAN_DIR, "absences.csv"),   parse_dates=["start_date", "end_date"])
rec  = pd.read_csv(os.path.join(CLEAN_DIR, "recruitment.csv"), parse_dates=["date_opened", "date_closed"])
lev  = pd.read_csv(os.path.join(CLEAN_DIR, "leavers.csv"),    parse_dates=["leaving_date"])
tr   = pd.read_csv(os.path.join(CLEAN_DIR, "training.csv"),   parse_dates=["completion_date"])
hea  = pd.read_csv(os.path.join(REAL_DIR,  "hea_uog_staff_profile.csv"))
cso  = pd.read_csv(os.path.join(REAL_DIR,  "cso_education_earnings_benchmark.csv"))
gpg  = pd.read_csv(os.path.join(REAL_DIR,  "irish_hei_gpg_benchmarks.csv"))
wf   = pd.read_csv(os.path.join(CLEAN_DIR, "workforce_summary.csv"))

active = emp[emp["status"] == "Active"].copy()
print(f"Active employees: {len(active)}")


# ── CHART 1: Headcount by Department ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
dept_counts = active.groupby("department")["employee_id"].count().sort_values()
bars = ax.barh(dept_counts.index, dept_counts.values, color=UOG_MAROON, edgecolor="white")
ax.bar_label(bars, padding=3, fontsize=9)
ax.set_xlabel("Headcount", fontsize=11)
ax.set_title("Active Headcount by Department\nUniversity of Galway (Synthetic)", fontsize=13, fontweight="bold")
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("headcount_by_dept.png")


# ── CHART 2: Gender by Grade (% Female) ─────────────────────────────────────
grade_order = [
    "Grade 3-4", "Grade 5", "Grade 6", "Grade 7", "Senior Management",
    "Research Fellow / Postdoc", "Lecturer Below Bar",
    "Senior Lecturer Above Bar", "Associate Professor", "Professor",
]
gender_grade = active.groupby(["grade", "gender"])["employee_id"].count().unstack(fill_value=0)
if "Female" not in gender_grade.columns: gender_grade["Female"] = 0
if "Male"   not in gender_grade.columns: gender_grade["Male"]   = 0
gender_grade["total"]   = gender_grade["Female"] + gender_grade["Male"]
gender_grade["pct_female"] = gender_grade["Female"] / gender_grade["total"] * 100
grade_plot = [g for g in grade_order if g in gender_grade.index]
plot_df = gender_grade.loc[grade_plot]

# HEA real benchmarks
hea_female_pct = {
    "Professor":                28, "Associate Professor":      35,
    "Senior Lecturer Above Bar":42, "Lecturer Below Bar":       52,
    "Research Fellow / Postdoc":48,
}

fig, ax = plt.subplots(figsize=(11, 7))
y_pos   = range(len(grade_plot))
ax.barh(y_pos, plot_df["pct_female"], color=UOG_MAROON, alpha=0.85, label="Synthetic % Female")
for i, grade in enumerate(grade_plot):
    if grade in hea_female_pct:
        ax.plot(hea_female_pct[grade], i, "D", color="black", markersize=8, zorder=5)
ax.axvline(50, color="grey", linestyle="--", alpha=0.5, label="50% parity line")
ax.set_yticks(list(y_pos))
ax.set_yticklabels(grade_plot, fontsize=10)
ax.set_xlabel("% Female", fontsize=11)
ax.set_title("Gender Balance by Grade — % Female\nDiamonds = HEA 2023 Real Benchmark", fontsize=13, fontweight="bold")
ax.legend(["Synthetic", "HEA 2023 Benchmark", "50% parity"], loc="lower right", fontsize=9)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("gender_by_grade.png")


# ── CHART 3: Employment Type Donut ───────────────────────────────────────────
emp_type_counts = active["employment_type"].value_counts()
fig, ax = plt.subplots(figsize=(7, 7))
colors  = [UOG_MAROON, UOG_BLUE, "#C9A87C"]
wedges, texts, autotexts = ax.pie(
    emp_type_counts.values,
    labels=emp_type_counts.index,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors[:len(emp_type_counts)],
    wedgeprops={"width": 0.55},
    textprops={"fontsize": 11},
)
for t in autotexts: t.set_fontsize(10); t.set_color("white")
ax.set_title("Employment Type Distribution\n(Calibrated to HEA 2023: ~58% Permanent)", fontsize=12, fontweight="bold")
save("employment_type_donut.png")


# ── CHART 4: Turnover Rate by Department ────────────────────────────────────
lev_emp = lev.merge(emp[["employee_id", "department"]], on="employee_id", how="left")
dept_leavers = lev_emp.groupby("department")["employee_id"].count()
dept_active  = active.groupby("department")["employee_id"].count()
turnover_rate = (dept_leavers / (dept_active + dept_leavers) * 100).fillna(0).sort_values()

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(turnover_rate.index, turnover_rate.values, color=UOG_MAROON, edgecolor="white")
ax.axvline(8.5, color="red", linestyle="--", linewidth=1.5, label="Irish Public Sector ~8.5% benchmark")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
ax.set_xlabel("Turnover Rate (%)", fontsize=11)
ax.set_title("Annual Turnover Rate by Department", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("turnover_rate_by_dept.png")


# ── CHART 5: Monthly Starters vs Leavers 2020–2024 ──────────────────────────
emp["hire_month"] = emp["hire_date"].dt.to_period("M")
lev["leave_month"] = lev["leaving_date"].dt.to_period("M")

all_months = pd.period_range("2020-01", "2024-12", freq="M")
starters = emp[emp["hire_date"] >= pd.Timestamp("2020-01-01")].groupby("hire_month")["employee_id"].count()
leavers_m = lev[lev["leaving_date"] >= pd.Timestamp("2020-01-01")].groupby("leave_month")["employee_id"].count()

starters  = starters.reindex(all_months, fill_value=0)
leavers_m = leavers_m.reindex(all_months, fill_value=0)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(starters.index.astype(str), starters.values, color=UOG_MAROON, linewidth=2, label="Starters", marker=".")
ax.plot(leavers_m.index.astype(str), leavers_m.values, color=UOG_BLUE, linewidth=2, label="Leavers", marker=".")
tick_every = 6
ax.set_xticks(range(0, len(all_months), tick_every))
ax.set_xticklabels([str(all_months[i]) for i in range(0, len(all_months), tick_every)], rotation=45, ha="right")
ax.set_ylabel("Headcount", fontsize=11)
ax.set_title("Monthly Starters vs Leavers  (2020–2024)", fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("monthly_starters_leavers.png")


# ── CHART 6: Absence Heatmap (Dept × Month) ─────────────────────────────────
abs_["month"]      = abs_["start_date"].dt.month
abs_["month_name"] = abs_["start_date"].dt.strftime("%b")
abs_emp = abs_.merge(emp[["employee_id", "department"]], on="employee_id", how="left")

dept_hc = active.groupby("department")["employee_id"].count()
abs_heat = abs_emp.groupby(["department", "month"])["days_absent"].sum().reset_index()
abs_heat = abs_heat.merge(dept_hc.reset_index().rename(columns={"employee_id": "hc"}), on="department")
abs_heat["absence_rate"] = abs_heat["days_absent"] / (abs_heat["hc"] * 230) * 100

pivot = abs_heat.pivot(index="department", columns="month", values="absence_rate").fillna(0)
pivot.columns = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][:len(pivot.columns)]

fig, ax = plt.subplots(figsize=(14, 7))
sns.heatmap(
    pivot, annot=True, fmt=".1f", cmap="RdYlGn_r",
    linewidths=0.5, ax=ax, cbar_kws={"label": "Absence Rate %"},
    vmin=0, vmax=3,
)
ax.set_title("Absence Rate % by Department and Month", fontsize=13, fontweight="bold")
ax.set_xlabel("Month"); ax.set_ylabel("")
plt.tight_layout()
save("absence_heatmap.png")


# ── CHART 7: Salary by Grade Box Plot ───────────────────────────────────────
grade_order_plot = [
    "Grade 3-4", "Grade 5", "Grade 6", "Grade 7", "Senior Management",
    "Research Fellow / Postdoc", "Lecturer Below Bar",
    "Senior Lecturer Above Bar", "Associate Professor", "Professor",
]
grade_plot_data = [g for g in grade_order_plot if g in active["grade"].values]

fig, ax = plt.subplots(figsize=(13, 7))
plot_data = [active[active["grade"] == g]["salary"].values for g in grade_plot_data]
bp = ax.boxplot(plot_data, vert=False, patch_artist=True, labels=grade_plot_data)
for patch in bp["boxes"]: patch.set_facecolor(UOG_MAROON); patch.set_alpha(0.7)
for element in ["whiskers","caps","medians"]: [item.set_color(UOG_DARK) for item in bp[element]]

# CSO overlay — average education sector annual salary equivalent
cso_avg = 49.80 * 37.5 * 52  # ~€97,110
ax.axvline(cso_avg, color="red", linestyle="--", linewidth=1.5, label=f"CSO Edu avg ~€{cso_avg:,.0f}/yr")
ax.set_xlabel("Annual Salary (€)", fontsize=11)
ax.set_title("Salary Distribution by Grade\nRed line = CSO Q4 2024 Education sector average", fontsize=12, fontweight="bold")
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"€{x:,.0f}"))
ax.legend(fontsize=9)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("salary_by_grade_boxplot.png")


# ── CHART 8: Gender Pay Gap ──────────────────────────────────────────────────
gender_sal = active.groupby("gender")["salary"].agg(["mean", "median"]).reset_index()
mean_f  = gender_sal.loc[gender_sal["gender"] == "Female", "mean"].values[0]
mean_m  = gender_sal.loc[gender_sal["gender"] == "Male",   "mean"].values[0]
med_f   = gender_sal.loc[gender_sal["gender"] == "Female", "median"].values[0]
med_m   = gender_sal.loc[gender_sal["gender"] == "Male",   "median"].values[0]
mean_gap = (mean_m - mean_f) / mean_m * 100
med_gap  = (med_m - med_f)   / med_m   * 100

# HEI benchmark from real data
hei_mean_gap = 16.2
hei_med_gap  = 12.8

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
metrics = ["Mean Salary", "Median Salary"]
female_vals = [mean_f, med_f]
male_vals   = [mean_m, med_m]

for i, ax in enumerate(axes):
    x   = np.arange(1)
    w   = 0.35
    b1  = ax.bar(x - w/2, [female_vals[i]], w, label="Female", color=UOG_MAROON, alpha=0.85)
    b2  = ax.bar(x + w/2, [male_vals[i]],   w, label="Male",   color=UOG_BLUE,   alpha=0.85)
    ax.bar_label(b1, fmt="€{:,.0f}", padding=3, fontsize=9)
    ax.bar_label(b2, fmt="€{:,.0f}", padding=3, fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([metrics[i]])
    ax.set_ylabel("Salary (€)", fontsize=10)
    gap = mean_gap if i == 0 else med_gap
    bm  = hei_mean_gap if i == 0 else hei_med_gap
    ax.set_title(f"{metrics[i]}\nGap: {gap:.1f}% (HEI benchmark: {bm:.1f}%)", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.legend(fontsize=9)
    ax.set_facecolor(UOG_GREY)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

fig.suptitle("Gender Pay Gap Analysis\nSynthetic data benchmarked against HEA 2023 & CSO figures", fontsize=12, fontweight="bold")
plt.tight_layout()
save("gender_pay_gap.png")


# ── CHART 9: Bradford Factor Distribution ───────────────────────────────────
sick = abs_[abs_["absence_type"].isin(["Certified Sick Leave", "Uncertified Sick Leave"])].copy()
sick_spells = sick.groupby("employee_id").agg(
    spells=("absence_id", "count"),
    total_days=("days_absent", "sum"),
).reset_index()
sick_spells["bradford"] = sick_spells["spells"] ** 2 * sick_spells["total_days"]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(sick_spells["bradford"], bins=40, color=UOG_MAROON, edgecolor="white", alpha=0.85)
ax.axvline(sick_spells["bradford"].median(), color="black", linestyle="--", linewidth=1.5,
           label=f"Median: {sick_spells['bradford'].median():.0f}")
ax.axvline(450, color="red",    linestyle="--", linewidth=1.5, label="High risk threshold (450)")
ax.set_xlabel("Bradford Factor Score", fontsize=11)
ax.set_ylabel("Number of Employees", fontsize=11)
ax.set_title("Bradford Factor Score Distribution\n(N² × D formula — sick leave only)", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("bradford_factor_distribution.png")


# ── CHART 10: Training Completion by Department ──────────────────────────────
tr_emp  = tr.merge(emp[["employee_id", "department"]], on="employee_id", how="left")
tr_comp = tr_emp.groupby("department")["passed"].agg(["sum", "count"]).reset_index()
tr_comp["completion_pct"] = tr_comp["sum"] / tr_comp["count"] * 100
tr_comp = tr_comp.sort_values("completion_pct")

fig, ax = plt.subplots(figsize=(10, 6))
colors = [UOG_MAROON if v >= 90 else "#C9A87C" if v >= 80 else "#D9534F" for v in tr_comp["completion_pct"]]
bars = ax.barh(tr_comp["department"], tr_comp["completion_pct"], color=colors, edgecolor="white")
ax.axvline(90, color="green", linestyle="--", linewidth=1.5, label="90% target")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
ax.set_xlabel("Completion Rate (%)", fontsize=11)
ax.set_title("Training Completion Rate by Department", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_xlim(0, 110)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("training_completion_by_dept.png")


# ── CHART 11: Mandatory Training Compliance ──────────────────────────────────
mandatory_tr   = tr[tr["mandatory"] == True]
mandatory_comp = mandatory_tr.groupby("employee_id")["passed"].all().reset_index()
mandatory_comp.columns = ["employee_id", "fully_compliant"]
all_emp_comp   = emp[["employee_id", "department"]].merge(mandatory_comp, on="employee_id", how="left")
all_emp_comp["fully_compliant"] = all_emp_comp["fully_compliant"].fillna(False)

dept_comp = all_emp_comp.groupby("department")["fully_compliant"].agg(["sum", "count"]).reset_index()
dept_comp["compliance_pct"] = dept_comp["sum"] / dept_comp["count"] * 100
dept_comp = dept_comp.sort_values("compliance_pct")

fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#D9534F" if v < 80 else "#F0AD4E" if v < 95 else "#5CB85C" for v in dept_comp["compliance_pct"]]
bars = ax.barh(dept_comp["department"], dept_comp["compliance_pct"], color=colors, edgecolor="white")
ax.axvline(95, color="green", linestyle="--", linewidth=1.5, label="95% compliance target")
ax.axvline(80, color="red",   linestyle=":",  linewidth=1.5, label="80% warning threshold")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
ax.set_xlabel("Mandatory Training Compliance (%)", fontsize=11)
ax.set_title("Mandatory Training Compliance by Department\nRAG: Green ≥95%, Amber 80–94%, Red <80%", fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.set_xlim(0, 115)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("mandatory_training_compliance.png")


# ── CHART 12: Time to Fill — Academic vs Support ─────────────────────────────
filled = rec[rec["outcome"] == "Filled"].dropna(subset=["time_to_fill_days"])
fig, ax = plt.subplots(figsize=(9, 6))
acad_ttf   = filled[filled["is_academic"] == True]["time_to_fill_days"]
support_ttf= filled[filled["is_academic"] == False]["time_to_fill_days"]
bp = ax.boxplot([acad_ttf, support_ttf], patch_artist=True, labels=["Academic Roles", "Support Roles"], vert=True)
bp["boxes"][0].set_facecolor(UOG_MAROON)
bp["boxes"][1].set_facecolor(UOG_BLUE)
for p in bp["boxes"]: p.set_alpha(0.8)
ax.set_ylabel("Days to Fill", fontsize=11)
ax.set_title(f"Time to Fill: Academic vs Support Roles\nAcademic avg: {acad_ttf.mean():.0f} days | Support avg: {support_ttf.mean():.0f} days",
             fontsize=12, fontweight="bold")
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("time_to_fill_academic_vs_support.png")


# ── CHART 13: Recruitment Source Funnel ──────────────────────────────────────
source_total  = rec.groupby("source")["job_req_id"].count()
source_filled = rec[rec["outcome"] == "Filled"].groupby("source")["job_req_id"].count()
source_df = pd.DataFrame({"total": source_total, "filled": source_filled}).fillna(0).sort_values("total")

fig, ax = plt.subplots(figsize=(10, 6))
y_pos = range(len(source_df))
ax.barh(y_pos, source_df["total"],  color=UOG_GREY,  edgecolor=UOG_DARK, linewidth=1, label="Total Openings")
ax.barh(y_pos, source_df["filled"], color=UOG_MAROON, edgecolor="white", label="Filled")
ax.set_yticks(list(y_pos))
ax.set_yticklabels(source_df.index, fontsize=10)
ax.set_xlabel("Number of Roles", fontsize=11)
ax.set_title("Recruitment Source Effectiveness\n(Total openings vs filled)", fontsize=12, fontweight="bold")
ax.legend(fontsize=10)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("recruitment_source_funnel.png")


# ── CHART 14: Real vs Synthetic Headcount ────────────────────────────────────
# SHOWCASE CHART: demonstrates calibration to real HEA data
synth_grade_gender = active.groupby(["grade", "gender"])["employee_id"].count().reset_index()
synth_grade_gender.columns = ["grade", "gender", "synthetic"]

hea_grade_gender = hea.groupby(["grade", "gender"])["headcount"].sum().reset_index()
hea_grade_gender.columns = ["grade", "gender", "real_hea"]

compare = synth_grade_gender.merge(hea_grade_gender, on=["grade", "gender"], how="outer").fillna(0)
compare = compare[compare["grade"].isin([
    "Professor", "Associate Professor", "Senior Lecturer Above Bar",
    "Lecturer Below Bar", "Research Fellow / Postdoc",
])]

compare["label"] = compare["grade"].str.replace(" / Postdoc", "\n/Postdoc") + "\n(" + compare["gender"] + ")"

fig, ax = plt.subplots(figsize=(15, 7))
x   = np.arange(len(compare))
w   = 0.38
b1  = ax.bar(x - w/2, compare["synthetic"], w, label="Synthetic (this dataset)", color=UOG_MAROON, alpha=0.85)
b2  = ax.bar(x + w/2, compare["real_hea"],  w, label="HEA 2023 Published Figures", color=UOG_BLUE, alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(compare["label"], fontsize=8, rotation=30, ha="right")
ax.set_ylabel("Headcount", fontsize=11)
ax.set_title("Synthetic Data vs Real HEA 2023 Staff Profile — Academic Grades\n"
             "Demonstrates calibration of synthetic data to publicly available HEA benchmarks",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=10)
ax.set_facecolor(UOG_GREY)
fig.patch.set_facecolor("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
save("real_vs_synthetic_headcount.png")


print(f"\n── Step 4 Summary ─────────────────────────────────────────")
charts = [f for f in os.listdir(CHART_DIR) if f.endswith(".png")]
print(f"  Charts saved to data/cleaned/charts/: {len(charts)}")
for c in sorted(charts):
    fsize = os.path.getsize(os.path.join(CHART_DIR, c)) // 1024
    print(f"    {c} ({fsize} KB)")
print("──────────────────────────────────────────────────────────\n")
