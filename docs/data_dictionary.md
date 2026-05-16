# Data Dictionary

## HR Workforce Analytics Platform — University of Galway

Legend:
- **Source:** `Real` = derived from HEA/CSO published data | `Synthetic` = generated
- **PK/FK:** Primary Key / Foreign Key

---

## Table: `employees` (Synthetic)

1,500 rows — simulated University of Galway staff population, calibrated to HEA 2023 figures.

| Field | Type | Description | Example | Business Rules | Source |
|-------|------|-------------|---------|----------------|--------|
| `employee_id` | VARCHAR(10) | Unique employee identifier. PK. | `UOG0001` | Format: UOG + 4-digit zero-padded number. Range: UOG0001–UOG1500 | Synthetic |
| `first_name` | VARCHAR(60) | Employee first name | `Siobhán` | Multi-locale: Irish, Polish, German, French. Weighted 72/10/9/9% | Synthetic |
| `last_name` | VARCHAR(60) | Employee surname | `Murphy` | Same locale mix as first_name | Synthetic |
| `gender` | VARCHAR(10) | Gender identity | `Female` | Values: Female, Male. Probabilities calibrated by grade to HEA 2023 figures | Synthetic (calibrated to Real) |
| `date_of_birth` | DATE | Date of birth | `1985-03-14` | Age at hire must be 18–70. Dates: 1958–2002 | Synthetic |
| `nationality` | VARCHAR(60) | Country of nationality | `Irish` | Irish ~72%, EU ~18%, non-EU ~10%. Reflects HEI international staff profile | Synthetic |
| `hire_date` | DATE | Date employee joined | `2018-07-01` | Range: 2005–2024. Weighted toward more recent years. Must be > date_of_birth + 18 years | Synthetic |
| `department` | VARCHAR(80) | Organisational department | `Academic Affairs` | Values: Academic Affairs, Research, Finance, IT, HR, Student Services, Estates & Facilities, Library, Registry, Executive Office | Synthetic |
| `job_title` | VARCHAR(100) | Job title within department | `Senior Lecturer` | Academic: Lecturer, Senior Lecturer, Associate Professor, Professor, Research Fellow, Postdoctoral Researcher. Support: Administrator, Senior Administrator, Executive Officer, Head of Function, Director | Synthetic |
| `employment_type` | VARCHAR(20) | Contract category | `Permanent` | Values: Permanent (~58%), Fixed-Term (~32%), Part-Time (~10%). Calibrated to HEA 2023 | Synthetic (calibrated to Real) |
| `grade` | VARCHAR(80) | Pay grade band | `Lecturer Below Bar` | Academic grades: Lecturer Below Bar, Senior Lecturer Above Bar, Associate Professor, Professor, Research Fellow / Postdoc. Support grades: Grade 3-4, Grade 5, Grade 6, Grade 7, Senior Management | Synthetic |
| `salary` | NUMERIC(10,2) | Annual gross salary in EUR | `72500.00` | Ranges: Grade 3-4 €28k–€38k; Professor €102k–€130k. Calibrated to CSO Education sector Q4 2024 (€49.80/hr avg) | Synthetic (calibrated to Real) |
| `manager_id` | VARCHAR(10) | Employee ID of direct line manager. FK → employees | `UOG0045` | Self-referencing hierarchy. NULL for top-level managers (Professor/Director grade) | Synthetic |
| `campus` | VARCHAR(40) | Primary work location | `Galway Main` | Values: Galway Main (~80%), Galway Hospital (~12%), Remote (~8%) | Synthetic |
| `status` | VARCHAR(20) | Current employment status | `Active` | Values: Active (~87%), Resigned (~6%), Retired (~4%), End of Contract (~3%) | Synthetic |
| `is_academic` | BOOLEAN | Whether role is academic | `TRUE` | TRUE for Academic Affairs and Research departments. FALSE for all support departments | Synthetic |
| `benchmark_salary_band` | VARCHAR(30) | CSO-derived salary band label | `€72,000–€95,000` | Added in Step 3 cleaning. References CSO/IUA public sector pay scales | Synthetic (enriched with Real) |
| `dq_flag` | TEXT | Data quality flag | `salary_out_of_range;` | Populated by 03_clean_and_merge.py. Empty string = clean record | Synthetic |

---

## Table: `absences` (Synthetic)

~4,500 rows — individual absence instances for active employees, 2021–2024.

| Field | Type | Description | Example | Business Rules | Source |
|-------|------|-------------|---------|----------------|--------|
| `absence_id` | VARCHAR(10) | Unique absence record identifier. PK. | `ABS00001` | Format: ABS + 5-digit number | Synthetic |
| `employee_id` | VARCHAR(10) | FK → employees | `UOG0234` | Must exist in employees table | Synthetic |
| `absence_type` | VARCHAR(40) | Category of absence | `Certified Sick Leave` | Values: Certified Sick Leave, Uncertified Sick Leave, Annual Leave, Maternity Leave, Paternity Leave, Parental Leave, Force Majeure, Study Leave, Other | Synthetic |
| `start_date` | DATE | First day of absence | `2023-02-06` | Range: 2021–2024. Must be < end_date | Synthetic |
| `end_date` | DATE | Last day of absence | `2023-02-09` | Must be > start_date | Synthetic |
| `days_absent` | INTEGER | Calendar days of absence | `3` | Recalculated as (end_date - start_date) in cleaning step. Min: 1. | Synthetic |
| `approved` | BOOLEAN | Whether absence was approved | `TRUE` | 97% true for all absence types | Synthetic |
| `return_to_work_interview` | BOOLEAN | RTW interview completed | `TRUE` | Only populated for sick leave ≥ 3 days. 85% true. NULL for other absence types | Synthetic |
| `sector_avg_absence_rate_pct` | NUMERIC(4,1) | Reference benchmark | `4.5` | Irish public sector average absence rate. Constant reference value added in Step 3 | Real benchmark |
| `dq_flag` | TEXT | Data quality flag | `` | Empty = clean | Synthetic |

---

## Table: `recruitment` (Synthetic)

400 rows — job requisitions opened 2020–2024.

| Field | Type | Description | Example | Business Rules | Source |
|-------|------|-------------|---------|----------------|--------|
| `job_req_id` | VARCHAR(10) | Unique requisition ID. PK. | `JR0001` | Format: JR + 4-digit number | Synthetic |
| `job_title` | VARCHAR(100) | Title of the role being recruited | `Associate Professor` | Realistic Irish HEI job titles per department and grade | Synthetic |
| `department` | VARCHAR(80) | Hiring department | `Research` | Same values as employees[department] | Synthetic |
| `is_academic` | BOOLEAN | Whether role is academic | `TRUE` | Consistent with department classification | Synthetic |
| `date_opened` | DATE | Date requisition opened | `2022-03-15` | Range: 2020–2024 | Synthetic |
| `date_closed` | DATE | Date requisition closed (nullable) | `2022-07-20` | NULL for Ongoing outcomes. Must be > date_opened | Synthetic |
| `time_to_fill_days` | INTEGER | Days from opened to filled | `127` | NULL for non-Filled outcomes. Academic avg ~90 days; Support avg ~45 days | Synthetic |
| `source` | VARCHAR(60) | Advertising channel | `NUI Jobs` | Academic: NUI Jobs, Academic Positions EU, LinkedIn, Direct Application, Internal Transfer. Support: NUI Jobs, IrishJobs, LinkedIn, Internal Transfer, Direct Application | Synthetic |
| `outcome` | VARCHAR(20) | Final status of requisition | `Filled` | Values: Filled (~60%), Ongoing (~20%), Cancelled (~10%), Withdrawn (~10%) | Synthetic |
| `hired_employee_id` | VARCHAR(10) | FK → employees (nullable) | `UOG1234` | Only populated for Filled outcome. FK may be NULL if hired employee not in 2020+ cohort | Synthetic |
| `salary_band_min` | NUMERIC(10,2) | Advertised minimum salary | `88000.00` | Derived from grade-level salary band | Synthetic |
| `salary_band_max` | NUMERIC(10,2) | Advertised maximum salary | `110000.00` | Derived from grade-level salary band | Synthetic |
| `dq_flag` | TEXT | Data quality flag | `` | Empty = clean | Synthetic |

---

## Table: `leavers` (Synthetic)

~195 rows — employees whose status is Resigned, Retired, or End of Contract.

| Field | Type | Description | Example | Business Rules | Source |
|-------|------|-------------|---------|----------------|--------|
| `employee_id` | VARCHAR(10) | FK → employees. PK. | `UOG0089` | One record per leaver. Must exist in employees | Synthetic |
| `leaving_date` | DATE | Date employment ended | `2023-09-30` | Must be > hire_date. Range: 2018–2024 | Synthetic |
| `reason_for_leaving` | VARCHAR(60) | Reason categorisation | `Resignation` | Values: Resignation, Retirement, End of Fixed-Term Contract, Voluntary Redundancy, Dismissal, Death in Service | Synthetic |
| `years_of_service` | NUMERIC(5,1) | Calculated tenure in years | `8.4` | (leaving_date - hire_date) / 365.25 | Synthetic |
| `exit_interview_completed` | BOOLEAN | Whether exit interview was done | `TRUE` | 72% true across all leavers | Synthetic |
| `rehire_eligible` | BOOLEAN | Whether eligible for future re-hire | `TRUE` | FALSE for Dismissal reason only | Synthetic |
| `destination` | VARCHAR(60) | Where employee went after leaving | `Another HEI` | Values: Another HEI, Private Sector, Retired, Unknown, Another Public Sector | Synthetic |
| `dq_flag` | TEXT | Data quality flag | `` | Empty = clean | Synthetic |

---

## Table: `training` (Synthetic)

~3,000 rows — training completion records, 2021–2024.

| Field | Type | Description | Example | Business Rules | Source |
|-------|------|-------------|---------|----------------|--------|
| `training_id` | VARCHAR(10) | Unique training record ID. PK. | `TR00001` | Format: TR + 5-digit number | Synthetic |
| `employee_id` | VARCHAR(10) | FK → employees | `UOG0456` | Must exist in employees table | Synthetic |
| `course_name` | VARCHAR(120) | Name of training course | `GDPR Awareness` | Realistic Irish HEI course catalogue | Synthetic |
| `category` | VARCHAR(60) | Training category | `Statutory Compliance` | Values: Statutory Compliance, Health & Safety, Leadership & Management, IT & Digital Skills, Research Skills, Teaching & Learning, HR & People Management, Wellbeing | Synthetic |
| `provider` | VARCHAR(60) | Training provider | `Internal` | Values: Internal (~50%), External (~20%), Online - LinkedIn Learning (~20%), Skillnet Ireland (~10%) | Synthetic |
| `completion_date` | DATE | Date training was completed | `2023-05-12` | Range: 2021–2024 | Synthetic |
| `duration_hours` | INTEGER | Length of training in hours | `8` | Internal: 1–4h. Online: 1–8h. External: 4–24h | Synthetic |
| `passed` | BOOLEAN | Whether employee passed | `TRUE` | 94% true overall | Synthetic |
| `cost_eur` | NUMERIC(8,2) | Cost of training in EUR | `350.00` | Internal/Online: €0. External/Skillnet: €50–€2,000. Set to 0 for Internal in cleaning step | Synthetic |
| `mandatory` | BOOLEAN | Whether course is mandatory | `TRUE` | Mandatory courses: GDPR Awareness, Manual Handling, Fire Safety, Display Screen Equipment, Dignity at Work | Synthetic |
| `dq_flag` | TEXT | Data quality flag | `` | Empty = clean | Synthetic |

---

## Reference Table: `hea_staff_profile` (Real)

Rows aggregated from HEA 2023 published report. Source: HEA Staff Profiles by Gender 2023.

| Field | Type | Description | Example | Source |
|-------|------|-------------|---------|--------|
| `institution` | VARCHAR(120) | HEI name | `University of Galway` | Real |
| `year` | INTEGER | Report year | `2023` | Real |
| `staff_category` | VARCHAR(80) | Academic or Professional & Support | `Academic` | Real |
| `grade` | VARCHAR(80) | Staff grade | `Professor` | Real |
| `gender` | VARCHAR(10) | Gender | `Female` | Real |
| `headcount` | INTEGER | Published headcount | `56` | Real |
| `contract_type` | VARCHAR(30) | Permanent or Fixed-Term | `Permanent` | Real |
| `fte` | NUMERIC(8,1) | Full-time equivalent | `46.1` | Real (estimated) |

---

## Reference Table: `cso_earnings_benchmark` (Real)

CSO quarterly earnings by sector. Source: CSO Earnings and Labour Costs releases.

| Field | Type | Description | Example | Source |
|-------|------|-------------|---------|--------|
| `year` | INTEGER | Year of release | `2024` | Real |
| `quarter` | VARCHAR(5) | Quarter | `Q4` | Real |
| `sector` | VARCHAR(80) | Economic sector | `Education` | Real |
| `avg_hourly_earnings_eur` | NUMERIC(8,2) | Average hourly earnings | `49.80` | Real |
| `avg_weekly_earnings_eur` | NUMERIC(10,2) | Average weekly earnings | `1185.00` | Real |
| `avg_total_labour_cost_eur` | NUMERIC(8,2) | Total labour cost (incl. employer PRSI) | `50.20` | Real |
| `source_url` | TEXT | CSO publication URL | `https://www.cso.ie/...` | Real |
