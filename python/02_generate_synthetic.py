"""
Step 2: Generate Synthetic Individual-Level Data
Calibrated to match HEA University of Galway staff profile figures.
Produces: employees.csv, absences.csv, recruitment.csv, leavers.csv, training.csv
"""

import os
import random
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

random.seed(42)
np.random.seed(42)

# Multi-locale Faker for Irish/EU name mix
fakers = {
    "en_IE": Faker("en_IE"),
    "pl_PL": Faker("pl_PL"),
    "de_DE": Faker("de_DE"),
    "fr_FR": Faker("fr_FR"),
}
Faker.seed(42)

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def weighted_date(start: date, end: date) -> date:
    """Hire dates weighted toward more recent years."""
    total_days = (end - start).days
    weights = np.linspace(0.3, 1.0, total_days + 1)
    weights /= weights.sum()
    days_offset = np.random.choice(range(total_days + 1), p=weights)
    return start + timedelta(days=int(days_offset))

def pick_locale():
    """Nationality-weighted locale selection."""
    return random.choices(
        ["en_IE", "pl_PL", "de_DE", "fr_FR"],
        weights=[72, 10, 9, 9],
    )[0]

def fake_name(locale):
    f = fakers[locale]
    return f.first_name(), f.last_name()


# ────────────────────────────────────────────────────────────────────────────
# TABLE 1: EMPLOYEES (1,500 rows)
# ────────────────────────────────────────────────────────────────────────────

DEPARTMENTS = [
    "Academic Affairs", "Research", "Finance", "IT",
    "HR", "Student Services", "Estates & Facilities",
    "Library", "Registry", "Executive Office",
]

# Grade / title mappings
ACADEMIC_TITLES = [
    "Postdoctoral Researcher", "Research Fellow", "Lecturer",
    "Senior Lecturer", "Associate Professor", "Professor",
]
SUPPORT_TITLES = [
    "Administrator", "Senior Administrator", "Executive Officer",
    "Head of Function", "Director",
]

ACADEMIC_GRADES = [
    "Lecturer Below Bar", "Senior Lecturer Above Bar",
    "Associate Professor", "Professor", "Research Fellow / Postdoc",
]
SUPPORT_GRADES = ["Grade 3-4", "Grade 5", "Grade 6", "Grade 7", "Senior Management"]

SALARY_BANDS = {
    # grade: (min, max) — calibrated to Irish public sector pay scales
    "Grade 3-4":               (28000,  38000),
    "Grade 5":                 (35000,  50000),
    "Grade 6":                 (45000,  62000),
    "Grade 7":                 (56000,  75000),
    "Senior Management":       (72000, 110000),
    "Lecturer Below Bar":      (52000,  75000),
    "Senior Lecturer Above Bar":(72000,  95000),
    "Associate Professor":     (88000, 110000),
    "Professor":               (102000,130000),
    "Research Fellow / Postdoc":(40000,  68000),
}

# Gender probability by grade (female proportion) — calibrated to HEA figures
GRADE_FEMALE_PROB = {
    "Professor":               0.28,
    "Associate Professor":     0.35,
    "Senior Lecturer Above Bar":0.42,
    "Lecturer Below Bar":      0.52,
    "Research Fellow / Postdoc":0.48,
    "Senior Management":       0.45,
    "Grade 7":                 0.58,
    "Grade 6":                 0.62,
    "Grade 5":                 0.65,
    "Grade 3-4":               0.68,
}

DEPT_IS_ACADEMIC = {
    "Academic Affairs": True, "Research": True,
    "Finance": False, "IT": False, "HR": False,
    "Student Services": False, "Estates & Facilities": False,
    "Library": False, "Registry": False, "Executive Office": False,
}

DEPT_GRADE_POOL = {
    "Academic Affairs":     ACADEMIC_GRADES,
    "Research":             ACADEMIC_GRADES,
    "Finance":              SUPPORT_GRADES,
    "IT":                   SUPPORT_GRADES,
    "HR":                   SUPPORT_GRADES,
    "Student Services":     SUPPORT_GRADES,
    "Estates & Facilities": SUPPORT_GRADES,
    "Library":              SUPPORT_GRADES,
    "Registry":             SUPPORT_GRADES,
    "Executive Office":     SUPPORT_GRADES,
}

# Department size weights (total ~1500 staff)
DEPT_WEIGHTS = {
    "Academic Affairs":      0.28,
    "Research":              0.14,
    "Student Services":      0.12,
    "Estates & Facilities":  0.11,
    "Finance":               0.08,
    "IT":                    0.07,
    "Registry":              0.06,
    "Library":               0.06,
    "HR":                    0.05,
    "Executive Office":      0.03,
}


def pick_grade(dept):
    pool = DEPT_GRADE_POOL[dept]
    # Weight toward lower grades (more common)
    weights = [4, 3, 2, 1.5, 1] if len(pool) == 5 else [3, 2, 1.5, 1, 1]
    weights = weights[:len(pool)]
    return random.choices(pool, weights=weights, k=1)[0]


def grade_to_title(grade, dept):
    mapping = {
        "Lecturer Below Bar":       "Lecturer",
        "Senior Lecturer Above Bar": "Senior Lecturer",
        "Associate Professor":      "Associate Professor",
        "Professor":                "Professor",
        "Research Fellow / Postdoc": random.choice(["Research Fellow", "Postdoctoral Researcher"]),
        "Grade 3-4":    "Administrator",
        "Grade 5":      "Senior Administrator",
        "Grade 6":      "Executive Officer",
        "Grade 7":      "Head of Function",
        "Senior Management": "Director",
    }
    return mapping.get(grade, "Officer")


print("Generating employees.csv …")
employees = []
for i in range(1, 1501):
    emp_id = f"UOG{i:04d}"
    dept   = random.choices(DEPARTMENTS, weights=list(DEPT_WEIGHTS.values()))[0]
    is_acad = DEPT_IS_ACADEMIC[dept]
    grade  = pick_grade(dept)
    title  = grade_to_title(grade, dept)
    female_p = GRADE_FEMALE_PROB.get(grade, 0.50)
    gender = "Female" if random.random() < female_p else "Male"

    locale = pick_locale()
    first, last = fake_name(locale)
    nationality_pool = (
        ["Irish"] * 72 + ["Polish"] * 5 + ["German"] * 4 + ["French"] * 4 +
        ["Italian"] * 3 + ["Spanish"] * 2 + ["Indian"] * 3 + ["Chinese"] * 2 +
        ["Brazilian"] * 2 + ["Nigerian"] * 1 + ["American"] * 2
    )
    nationality = random.choice(nationality_pool)

    dob = rand_date(date(1958, 1, 1), date(2002, 12, 31))
    hire_date = weighted_date(date(2005, 1, 1), date(2024, 6, 30))
    # Ensure hire_date is after dob+22 (accounting for Feb 29 edge case)
    try:
        min_hire = date(dob.year + 22, dob.month, dob.day)
    except ValueError:
        min_hire = date(dob.year + 22, dob.month, 28)
    if hire_date < min_hire:
        hire_date = min_hire + timedelta(days=random.randint(0, 365))

    # Employment type calibrated to HEA: Permanent 58%, Fixed-Term 32%, Part-Time 10%
    emp_type = random.choices(
        ["Permanent", "Fixed-Term", "Part-Time"],
        weights=[58, 32, 10],
    )[0]

    sal_min, sal_max = SALARY_BANDS[grade]
    salary = round(random.uniform(sal_min, sal_max), -2)

    campus = random.choices(
        ["Galway Main", "Galway Hospital", "Remote"],
        weights=[80, 12, 8],
    )[0]

    status = random.choices(
        ["Active", "Resigned", "Retired", "End of Contract"],
        weights=[87, 6, 4, 3],
    )[0]

    employees.append({
        "employee_id":     emp_id,
        "first_name":      first,
        "last_name":       last,
        "gender":          gender,
        "date_of_birth":   dob,
        "nationality":     nationality,
        "hire_date":       hire_date,
        "department":      dept,
        "job_title":       title,
        "employment_type": emp_type,
        "grade":           grade,
        "salary":          salary,
        "manager_id":      None,
        "campus":          campus,
        "status":          status,
        "is_academic":     is_acad,
    })

emp_df = pd.DataFrame(employees)

# Build manager hierarchy: directors/heads are managers, others get one assigned
managers = emp_df[emp_df["grade"].isin(["Senior Management", "Grade 7", "Professor"])]["employee_id"].tolist()
dept_managers = {}
for dept in DEPARTMENTS:
    dept_mgrs = emp_df[(emp_df["department"] == dept) &
                       (emp_df["grade"].isin(["Senior Management", "Grade 7", "Professor"]))]["employee_id"].tolist()
    if not dept_mgrs:
        dept_mgrs = managers[:3]
    dept_managers[dept] = dept_mgrs

def assign_manager(row):
    if row["grade"] in ["Senior Management", "Professor"]:
        return None  # top of hierarchy
    mgrs = dept_managers.get(row["department"], managers)
    candidates = [m for m in mgrs if m != row["employee_id"]]
    return random.choice(candidates) if candidates else None

emp_df["manager_id"] = emp_df.apply(assign_manager, axis=1)

emp_path = os.path.join(RAW_DIR, "employees.csv")
emp_df.to_csv(emp_path, index=False)
print(f"  → employees.csv: {len(emp_df)} rows")


# ────────────────────────────────────────────────────────────────────────────
# TABLE 2: ABSENCES (~4,500 rows)
# ────────────────────────────────────────────────────────────────────────────

print("Generating absences.csv …")
active_emp_ids = emp_df[emp_df["status"] == "Active"]["employee_id"].tolist()

ABSENCE_TYPES = [
    "Certified Sick Leave", "Uncertified Sick Leave", "Annual Leave",
    "Maternity Leave", "Paternity Leave", "Parental Leave",
    "Force Majeure", "Study Leave", "Other",
]

ABSENCE_WEIGHTS = [20, 12, 35, 5, 3, 6, 4, 8, 7]

ABSENCE_DURATION = {
    "Certified Sick Leave":   (3, 14),
    "Uncertified Sick Leave": (1, 3),
    "Annual Leave":           (1, 20),
    "Maternity Leave":        (120, 182),
    "Paternity Leave":        (2, 14),
    "Parental Leave":         (5, 60),
    "Force Majeure":          (1, 3),
    "Study Leave":            (1, 5),
    "Other":                  (1, 7),
}

absences = []
abs_id = 1
target = 4500
attempts = 0

while len(absences) < target and attempts < 20000:
    attempts += 1
    emp_id = random.choice(active_emp_ids)
    abs_type = random.choices(ABSENCE_TYPES, weights=ABSENCE_WEIGHTS)[0]
    min_d, max_d = ABSENCE_DURATION[abs_type]
    days = random.randint(min_d, max_d)

    start = rand_date(date(2021, 1, 1), date(2024, 11, 30))
    end   = start + timedelta(days=days)
    if end > date(2024, 12, 31):
        end = date(2024, 12, 31)
        days = (end - start).days
    if days < 1:
        continue

    approved = random.random() < 0.97
    rtw = None
    if abs_type in ["Certified Sick Leave", "Uncertified Sick Leave"] and days >= 3:
        rtw = random.random() < 0.85

    absences.append({
        "absence_id":               f"ABS{abs_id:05d}",
        "employee_id":              emp_id,
        "absence_type":             abs_type,
        "start_date":               start,
        "end_date":                 end,
        "days_absent":              days,
        "approved":                 approved,
        "return_to_work_interview": rtw,
    })
    abs_id += 1

abs_df = pd.DataFrame(absences)
abs_path = os.path.join(RAW_DIR, "absences.csv")
abs_df.to_csv(abs_path, index=False)
print(f"  → absences.csv: {len(abs_df)} rows")


# ────────────────────────────────────────────────────────────────────────────
# TABLE 3: RECRUITMENT (400 rows)
# ────────────────────────────────────────────────────────────────────────────

print("Generating recruitment.csv …")

SOURCES_ACADEMIC = ["NUI Jobs", "Academic Positions EU", "LinkedIn", "Direct Application", "Internal Transfer"]
SOURCES_SUPPORT  = ["NUI Jobs", "IrishJobs", "LinkedIn", "Internal Transfer", "Direct Application"]

OUTCOMES = ["Filled", "Cancelled", "Ongoing", "Withdrawn"]
OUTCOME_W = [60, 10, 20, 10]

hired_ids = emp_df[(emp_df["status"] == "Active") & (emp_df["hire_date"] >= date(2020, 1, 1))]["employee_id"].tolist()

recruitment = []
for i in range(1, 401):
    dept      = random.choice(DEPARTMENTS)
    is_acad   = DEPT_IS_ACADEMIC[dept]
    grade     = pick_grade(dept)
    title     = grade_to_title(grade, dept)
    opened    = rand_date(date(2020, 1, 1), date(2024, 6, 30))
    outcome   = random.choices(OUTCOMES, weights=OUTCOME_W)[0]

    avg_fill  = 90 if is_acad else 45
    ttf       = max(14, int(np.random.normal(avg_fill, avg_fill * 0.3)))

    if outcome == "Filled":
        closed = opened + timedelta(days=ttf)
    elif outcome == "Ongoing":
        closed = None
        ttf    = None
    else:
        closed = opened + timedelta(days=random.randint(5, 30))
        ttf    = None

    source = random.choice(SOURCES_ACADEMIC if is_acad else SOURCES_SUPPORT)

    hired_id = None
    if outcome == "Filled" and hired_ids:
        hired_id = random.choice(hired_ids)

    sal_min, sal_max = SALARY_BANDS[grade]

    recruitment.append({
        "job_req_id":       f"JR{i:04d}",
        "job_title":        title,
        "department":       dept,
        "is_academic":      is_acad,
        "date_opened":      opened,
        "date_closed":      closed,
        "time_to_fill_days": ttf,
        "source":           source,
        "outcome":          outcome,
        "hired_employee_id": hired_id,
        "salary_band_min":  sal_min,
        "salary_band_max":  sal_max,
    })

rec_df = pd.DataFrame(recruitment)
rec_path = os.path.join(RAW_DIR, "recruitment.csv")
rec_df.to_csv(rec_path, index=False)
print(f"  → recruitment.csv: {len(rec_df)} rows")


# ────────────────────────────────────────────────────────────────────────────
# TABLE 4: LEAVERS (~195 rows)
# ────────────────────────────────────────────────────────────────────────────

print("Generating leavers.csv …")

LEAVE_REASONS = [
    "Resignation", "Retirement", "End of Fixed-Term Contract",
    "Voluntary Redundancy", "Dismissal", "Death in Service",
]

DESTINATIONS = [
    "Another HEI", "Private Sector", "Retired", "Unknown",
    "Another Public Sector",
]

inactive = emp_df[emp_df["status"] != "Active"].copy()
leavers  = []

for _, row in inactive.iterrows():
    hire = row["hire_date"] if isinstance(row["hire_date"], date) else pd.to_datetime(row["hire_date"]).date()
    leave_start = max(hire + timedelta(days=180), date(2018, 1, 1))
    leave_end   = date(2024, 12, 31)
    if leave_start >= leave_end:
        leave_start = date(2022, 1, 1)
    leave_date = rand_date(leave_start, leave_end)
    yos = round((leave_date - hire).days / 365.25, 1)

    if row["status"] == "Retired":
        reason = "Retirement"
        dest   = "Retired"
    elif row["status"] == "End of Contract":
        reason = "End of Fixed-Term Contract"
        dest   = random.choice(["Another HEI", "Private Sector", "Unknown", "Another Public Sector"])
    else:
        reason = random.choices(
            ["Resignation", "Voluntary Redundancy", "Dismissal", "Death in Service"],
            weights=[70, 15, 10, 5],
        )[0]
        dest = random.choice(DESTINATIONS)

    leavers.append({
        "employee_id":             row["employee_id"],
        "leaving_date":            leave_date,
        "reason_for_leaving":      reason,
        "years_of_service":        yos,
        "exit_interview_completed": random.random() < 0.72,
        "rehire_eligible":         reason not in ["Dismissal"],
        "destination":             dest,
    })

leavers_df = pd.DataFrame(leavers)
leavers_path = os.path.join(RAW_DIR, "leavers.csv")
leavers_df.to_csv(leavers_path, index=False)
print(f"  → leavers.csv: {len(leavers_df)} rows")


# ────────────────────────────────────────────────────────────────────────────
# TABLE 5: TRAINING (~3,000 rows)
# ────────────────────────────────────────────────────────────────────────────

print("Generating training.csv …")

CATEGORIES = [
    "Statutory Compliance", "Health & Safety", "Leadership & Management",
    "IT & Digital Skills", "Research Skills", "Teaching & Learning",
    "HR & People Management", "Wellbeing",
]

COURSES = {
    "Statutory Compliance":      ["GDPR Awareness", "Data Protection Essentials", "FOI Training"],
    "Health & Safety":           ["Manual Handling", "Fire Safety", "Display Screen Equipment", "First Aid"],
    "Leadership & Management":   ["Leading Teams", "Performance Management", "Strategic Leadership", "Coaching Skills"],
    "IT & Digital Skills":       ["Microsoft 365 Essentials", "Power BI Foundations", "Python for Data", "Cybersecurity Basics"],
    "Research Skills":           ["Research Integrity", "Grant Writing", "Ethics in Research", "Open Science Practices"],
    "Teaching & Learning":       ["Instructional Design", "Moodle Administration", "Assessment Design", "Universal Design for Learning"],
    "HR & People Management":    ["Recruitment Best Practice", "Dignity at Work", "Probation Management", "HR Systems Training"],
    "Wellbeing":                 ["Mindfulness at Work", "Stress Management", "Mental Health Awareness", "Resilience Building"],
}

PROVIDERS = ["Internal", "External", "Online - LinkedIn Learning", "Skillnet Ireland"]
PROV_W    = [50, 20, 20, 10]

MANDATORY_COURSES = {"GDPR Awareness", "Manual Handling", "Fire Safety", "Display Screen Equipment", "Dignity at Work"}

training = []
tr_id = 1
all_emp_ids = emp_df["employee_id"].tolist()

while len(training) < 3000:
    emp_id   = random.choice(all_emp_ids)
    category = random.choice(CATEGORIES)
    course   = random.choice(COURSES[category])
    provider = random.choices(PROVIDERS, weights=PROV_W)[0]
    comp_dt  = rand_date(date(2021, 1, 1), date(2024, 12, 31))
    passed   = random.random() < 0.94
    mandatory = course in MANDATORY_COURSES

    if provider == "Internal":
        cost = 0
        duration = random.choice([1, 2, 3, 4])
    elif provider == "Online - LinkedIn Learning":
        cost = 0
        duration = random.choice([1, 2, 4, 8])
    else:
        cost = round(random.uniform(50, 2000), -1)
        duration = random.choice([4, 8, 16, 24])

    training.append({
        "training_id":      f"TR{tr_id:05d}",
        "employee_id":      emp_id,
        "course_name":      course,
        "category":         category,
        "provider":         provider,
        "completion_date":  comp_dt,
        "duration_hours":   duration,
        "passed":           passed,
        "cost_eur":         cost,
        "mandatory":        mandatory,
    })
    tr_id += 1

tr_df = pd.DataFrame(training)
tr_path = os.path.join(RAW_DIR, "training.csv")
tr_df.to_csv(tr_path, index=False)
print(f"  → training.csv: {len(tr_df)} rows")


print("\n── Step 2 Summary ─────────────────────────────────────────")
print(f"  employees.csv:   {len(emp_df):,} rows | {len(emp_df.columns)} columns")
print(f"  absences.csv:    {len(abs_df):,} rows | {len(abs_df.columns)} columns")
print(f"  recruitment.csv: {len(rec_df):,} rows | {len(rec_df.columns)} columns")
print(f"  leavers.csv:     {len(leavers_df):,} rows | {len(leavers_df.columns)} columns")
print(f"  training.csv:    {len(tr_df):,} rows | {len(tr_df.columns)} columns")
total = len(emp_df)+len(abs_df)+len(rec_df)+len(leavers_df)+len(tr_df)
print(f"  TOTAL SYNTHETIC: {total:,} rows")
print("  Data calibrated to HEA 2023 gender/grade/contract figures.")
print("──────────────────────────────────────────────────────────\n")
