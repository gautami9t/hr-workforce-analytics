-- ============================================================
-- HR Workforce Analytics Platform — University Sector
-- PostgreSQL Schema
-- Institution: University of Galway (synthetic + real benchmark data)
-- Real data: HEA Staff Profiles 2023, CSO Earnings Q4 2024
-- Synthetic data: Individual-level operational records (calibrated)
-- ============================================================

-- ── DATA SOURCES REFERENCE TABLE ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS data_sources (
    source_id        SERIAL PRIMARY KEY,
    source_name      VARCHAR(120) NOT NULL,
    source_type      VARCHAR(20)  NOT NULL CHECK (source_type IN ('Real', 'Synthetic')),
    publication_year INTEGER,
    url              TEXT,
    description      TEXT,
    tables_populated TEXT[],
    created_at       TIMESTAMP DEFAULT NOW()
);

INSERT INTO data_sources (source_name, source_type, publication_year, url, description, tables_populated) VALUES
('HEA Staff Profiles by Gender 2023', 'Real', 2023,
 'https://hea.ie/policy/gender/statistics/higher-education-institutional-staff-profiles-by-sex-and-gender-2023/',
 'Annual HEA publication of Irish HEI staff headcount by grade, gender, and contract type',
 ARRAY['hea_staff_profile', 'workforce_summary']),
('CSO Earnings and Labour Costs Q4 2024', 'Real', 2024,
 'https://www.cso.ie/en/releasesandpublications/ep/p-elc/earningsandlabourcostsq42024/',
 'CSO quarterly earnings by sector including education sector hourly and weekly averages',
 ARRAY['cso_earnings_benchmark', 'employees']),
('Irish Gender Pay Gap Information Act 2021 benchmarks', 'Real', 2023,
 'https://www.gov.ie/en/publication/173e5-gender-pay-gap-information/',
 'Published HEI sector GPG disclosure benchmarks',
 ARRAY['gpg_benchmarks']),
('Synthetic individual-level HR records', 'Synthetic', 2024,
 NULL,
 'Generated using Faker + NumPy, calibrated to HEA 2023 gender/grade/contract distributions',
 ARRAY['employees', 'absences', 'recruitment', 'leavers', 'training']);


-- ── REAL BENCHMARK TABLES ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS hea_staff_profile (
    id               SERIAL PRIMARY KEY,
    institution      VARCHAR(120) NOT NULL,
    year             INTEGER      NOT NULL,
    staff_category   VARCHAR(80)  NOT NULL,
    grade            VARCHAR(80)  NOT NULL,
    gender           VARCHAR(10)  NOT NULL CHECK (gender IN ('Female', 'Male', 'Unknown')),
    headcount        INTEGER      NOT NULL CHECK (headcount >= 0),
    contract_type    VARCHAR(30),
    fte              NUMERIC(8,1)
);

CREATE TABLE IF NOT EXISTS cso_earnings_benchmark (
    id                          SERIAL PRIMARY KEY,
    year                        INTEGER      NOT NULL,
    quarter                     VARCHAR(5)   NOT NULL,
    sector                      VARCHAR(80)  NOT NULL,
    avg_hourly_earnings_eur     NUMERIC(8,2),
    avg_weekly_earnings_eur     NUMERIC(10,2),
    avg_total_labour_cost_eur   NUMERIC(8,2),
    source_url                  TEXT
);

CREATE TABLE IF NOT EXISTS gpg_benchmarks (
    id           SERIAL PRIMARY KEY,
    sector       VARCHAR(80)  NOT NULL,
    metric       VARCHAR(120) NOT NULL,
    value_pct    NUMERIC(5,1),
    direction    VARCHAR(30),
    source_note  TEXT
);


-- ── SYNTHETIC OPERATIONAL TABLES ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS employees (
    employee_id       VARCHAR(10)   PRIMARY KEY,   -- UOG0001 – UOG1500
    first_name        VARCHAR(60)   NOT NULL,
    last_name         VARCHAR(60)   NOT NULL,
    gender            VARCHAR(10)   CHECK (gender IN ('Female', 'Male', 'Non-Binary', 'Unknown')),
    date_of_birth     DATE,
    nationality       VARCHAR(60),
    hire_date         DATE          NOT NULL,
    department        VARCHAR(80)   NOT NULL,
    job_title         VARCHAR(100)  NOT NULL,
    employment_type   VARCHAR(20)   NOT NULL CHECK (employment_type IN ('Permanent', 'Fixed-Term', 'Part-Time')),
    grade             VARCHAR(80)   NOT NULL,
    salary            NUMERIC(10,2) NOT NULL CHECK (salary > 0),
    manager_id        VARCHAR(10)   REFERENCES employees(employee_id) ON DELETE SET NULL,
    campus            VARCHAR(40)   NOT NULL CHECK (campus IN ('Galway Main', 'Galway Hospital', 'Remote')),
    status            VARCHAR(20)   NOT NULL CHECK (status IN ('Active', 'Resigned', 'Retired', 'End of Contract')),
    is_academic       BOOLEAN       NOT NULL DEFAULT FALSE,
    benchmark_salary_band VARCHAR(30),
    dq_flag           TEXT          DEFAULT '',
    created_at        TIMESTAMP     DEFAULT NOW()
);

CREATE INDEX idx_emp_dept      ON employees(department);
CREATE INDEX idx_emp_status    ON employees(status);
CREATE INDEX idx_emp_grade     ON employees(grade);
CREATE INDEX idx_emp_gender    ON employees(gender);
CREATE INDEX idx_emp_hire_date ON employees(hire_date);


CREATE TABLE IF NOT EXISTS absences (
    absence_id                VARCHAR(10)  PRIMARY KEY,
    employee_id               VARCHAR(10)  NOT NULL REFERENCES employees(employee_id),
    absence_type              VARCHAR(40)  NOT NULL,
    start_date                DATE         NOT NULL,
    end_date                  DATE         NOT NULL,
    days_absent               INTEGER      NOT NULL CHECK (days_absent > 0),
    approved                  BOOLEAN      NOT NULL DEFAULT TRUE,
    return_to_work_interview  BOOLEAN,
    sector_avg_absence_rate_pct NUMERIC(4,1) DEFAULT 4.5,
    dq_flag                   TEXT         DEFAULT '',
    CONSTRAINT abs_date_check CHECK (end_date > start_date)
);

CREATE INDEX idx_abs_emp_id    ON absences(employee_id);
CREATE INDEX idx_abs_type      ON absences(absence_type);
CREATE INDEX idx_abs_start     ON absences(start_date);


CREATE TABLE IF NOT EXISTS recruitment (
    job_req_id          VARCHAR(10)  PRIMARY KEY,
    job_title           VARCHAR(100) NOT NULL,
    department          VARCHAR(80)  NOT NULL,
    is_academic         BOOLEAN      NOT NULL DEFAULT FALSE,
    date_opened         DATE         NOT NULL,
    date_closed         DATE,
    time_to_fill_days   INTEGER      CHECK (time_to_fill_days > 0),
    source              VARCHAR(60),
    outcome             VARCHAR(20)  NOT NULL CHECK (outcome IN ('Filled', 'Cancelled', 'Ongoing', 'Withdrawn')),
    hired_employee_id   VARCHAR(10)  REFERENCES employees(employee_id) ON DELETE SET NULL,
    salary_band_min     NUMERIC(10,2),
    salary_band_max     NUMERIC(10,2),
    dq_flag             TEXT         DEFAULT '',
    CONSTRAINT rec_date_check CHECK (date_closed IS NULL OR date_closed > date_opened)
);

CREATE INDEX idx_rec_dept    ON recruitment(department);
CREATE INDEX idx_rec_outcome ON recruitment(outcome);


CREATE TABLE IF NOT EXISTS leavers (
    employee_id               VARCHAR(10)  PRIMARY KEY REFERENCES employees(employee_id),
    leaving_date              DATE         NOT NULL,
    reason_for_leaving        VARCHAR(60)  NOT NULL,
    years_of_service          NUMERIC(5,1),
    exit_interview_completed  BOOLEAN      NOT NULL DEFAULT FALSE,
    rehire_eligible           BOOLEAN      NOT NULL DEFAULT TRUE,
    destination               VARCHAR(60),
    dq_flag                   TEXT         DEFAULT ''
);

CREATE INDEX idx_lev_reason ON leavers(reason_for_leaving);


CREATE TABLE IF NOT EXISTS training (
    training_id       VARCHAR(10)  PRIMARY KEY,
    employee_id       VARCHAR(10)  NOT NULL REFERENCES employees(employee_id),
    course_name       VARCHAR(120) NOT NULL,
    category          VARCHAR(60)  NOT NULL,
    provider          VARCHAR(60)  NOT NULL,
    completion_date   DATE         NOT NULL,
    duration_hours    INTEGER      NOT NULL CHECK (duration_hours > 0),
    passed            BOOLEAN      NOT NULL DEFAULT TRUE,
    cost_eur          NUMERIC(8,2) NOT NULL DEFAULT 0 CHECK (cost_eur >= 0),
    mandatory         BOOLEAN      NOT NULL DEFAULT FALSE,
    dq_flag           TEXT         DEFAULT ''
);

CREATE INDEX idx_tr_emp_id      ON training(employee_id);
CREATE INDEX idx_tr_category    ON training(category);
CREATE INDEX idx_tr_mandatory   ON training(mandatory);
CREATE INDEX idx_tr_comp_date   ON training(completion_date);


-- ── VIEWS ─────────────────────────────────────────────────────────────────────

-- Active workforce snapshot
CREATE OR REPLACE VIEW v_active_workforce AS
SELECT
    e.employee_id, e.first_name, e.last_name, e.gender, e.department,
    e.job_title, e.grade, e.employment_type, e.salary,
    e.hire_date, e.campus, e.is_academic,
    DATE_PART('year', AGE(CURRENT_DATE, e.hire_date)) AS years_of_service,
    e.benchmark_salary_band
FROM employees e
WHERE e.status = 'Active';

-- Absence rate summary by department
CREATE OR REPLACE VIEW v_absence_rate_by_dept AS
SELECT
    e.department,
    COUNT(DISTINCT e.employee_id)      AS headcount,
    COALESCE(SUM(a.days_absent), 0)    AS total_days_absent,
    ROUND(
        COALESCE(SUM(a.days_absent), 0)::NUMERIC /
        NULLIF(COUNT(DISTINCT e.employee_id) * 230.0, 0) * 100,
    2) AS absence_rate_pct
FROM employees e
LEFT JOIN absences a ON e.employee_id = a.employee_id
WHERE e.status = 'Active'
GROUP BY e.department;
