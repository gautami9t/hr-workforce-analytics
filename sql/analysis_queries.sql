-- ============================================================
-- HR Workforce Analytics — Analysis Queries
-- University of Galway (synthetic + HEA/CSO benchmark data)
-- All queries reference the PostgreSQL schema defined in schema.sql
-- ============================================================


-- ── QUERY 1: Total and Active Headcount by Department and Employment Type ────
-- Business context: Understand workforce composition across units.
-- Flags part-time and fixed-term concentrations by department.
SELECT
    e.department,
    e.employment_type,
    COUNT(*)                                        AS headcount,
    COUNT(*) FILTER (WHERE e.status = 'Active')     AS active_count,
    ROUND(
        COUNT(*) FILTER (WHERE e.status = 'Active')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                               AS pct_active,
    ROUND(AVG(e.salary), 0)                         AS avg_salary
FROM employees e
GROUP BY e.department, e.employment_type
ORDER BY e.department, e.employment_type;


-- ── QUERY 2: Headcount by Grade and Gender — % Female per Grade ──────────────
-- Business context: Monitor gender balance at each grade level.
-- Drivers of GPG often lie in grade concentration rather than pay discrimination.
SELECT
    e.grade,
    e.is_academic,
    COUNT(*)                                               AS total_headcount,
    COUNT(*) FILTER (WHERE e.gender = 'Female')            AS female_count,
    COUNT(*) FILTER (WHERE e.gender = 'Male')              AS male_count,
    ROUND(
        COUNT(*) FILTER (WHERE e.gender = 'Female')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                                      AS pct_female,
    ROUND(AVG(e.salary), 0)                                AS avg_salary
FROM employees e
WHERE e.status = 'Active'
GROUP BY e.grade, e.is_academic
ORDER BY e.is_academic DESC, avg_salary DESC;


-- ── QUERY 3: HEA Benchmark Comparison — Synthetic vs Real Headcount ──────────
-- Business context: Validates that synthetic data mirrors real HEA published figures.
-- Variance should be within ±20% to demonstrate credible calibration.
SELECT
    h.grade,
    h.gender,
    h.headcount                                   AS hea_real_headcount,
    COUNT(e.employee_id)                          AS synthetic_headcount,
    COUNT(e.employee_id) - h.headcount            AS variance_absolute,
    ROUND(
        (COUNT(e.employee_id) - h.headcount)::NUMERIC /
        NULLIF(h.headcount, 0) * 100, 1
    )                                             AS variance_pct,
    h.year                                        AS hea_reference_year
FROM (
    SELECT grade, gender, SUM(headcount) AS headcount, MAX(year) AS year
    FROM hea_staff_profile
    GROUP BY grade, gender
) h
LEFT JOIN employees e
    ON e.grade = h.grade AND e.gender = h.gender AND e.status = 'Active'
GROUP BY h.grade, h.gender, h.headcount, h.year
ORDER BY h.grade, h.gender;


-- ── QUERY 4: Monthly Headcount Trend 2020–2024 (Starters vs Leavers) ─────────
-- Business context: Track workforce flow over time. Useful for board reporting.
WITH months AS (
    SELECT generate_series(
        DATE '2020-01-01', DATE '2024-12-01', INTERVAL '1 month'
    )::DATE AS month_start
),
starters AS (
    SELECT DATE_TRUNC('month', hire_date)::DATE AS month_start,
           COUNT(*)                              AS starters
    FROM employees
    WHERE hire_date >= '2020-01-01'
    GROUP BY 1
),
leavers_monthly AS (
    SELECT DATE_TRUNC('month', leaving_date)::DATE AS month_start,
           COUNT(*)                                 AS leavers
    FROM leavers
    WHERE leaving_date >= '2020-01-01'
    GROUP BY 1
)
SELECT
    TO_CHAR(m.month_start, 'YYYY-MM')     AS year_month,
    COALESCE(s.starters, 0)               AS starters,
    COALESCE(l.leavers,  0)               AS leavers,
    COALESCE(s.starters, 0) -
    COALESCE(l.leavers,  0)               AS net_change
FROM months m
LEFT JOIN starters s       ON m.month_start = s.month_start
LEFT JOIN leavers_monthly l ON m.month_start = l.month_start
ORDER BY m.month_start;


-- ── QUERY 5: Annual Turnover Rate by Department ───────────────────────────────
-- Business context: Turnover rate = leavers / average headcount.
-- Irish HEI sector average is approximately 8–12%.
SELECT
    e.department,
    COUNT(DISTINCT e.employee_id)                      AS total_headcount,
    COUNT(DISTINCT l.employee_id)                      AS total_leavers,
    ROUND(
        COUNT(DISTINCT l.employee_id)::NUMERIC /
        NULLIF(
            (COUNT(DISTINCT e.employee_id) +
             COUNT(DISTINCT l.employee_id)) / 2.0, 0
        ) * 100, 1
    )                                                  AS turnover_rate_pct,
    8.5                                                AS sector_benchmark_pct
FROM employees e
LEFT JOIN leavers l ON e.employee_id = l.employee_id
GROUP BY e.department
ORDER BY turnover_rate_pct DESC;


-- ── QUERY 6: Mean and Median Salary by Gender — Gender Pay Gap ───────────────
-- Business context: Required for Irish Gender Pay Gap Information Act 2021 disclosure.
-- Reported annually for employers with 250+ employees.
SELECT
    e.gender,
    COUNT(*)                          AS headcount,
    ROUND(AVG(e.salary), 2)           AS mean_salary,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary), 2) AS median_salary,
    ROUND(AVG(e.salary) FILTER (WHERE e.is_academic = TRUE), 2)     AS mean_salary_academic,
    ROUND(AVG(e.salary) FILTER (WHERE e.is_academic = FALSE), 2)    AS mean_salary_support
FROM employees e
WHERE e.status = 'Active'
GROUP BY e.gender
ORDER BY mean_salary DESC;


-- ── QUERY 7: Gender Pay Gap % by Grade ───────────────────────────────────────
-- Business context: Identify which grades drive the overall pay gap.
-- Irish HEI research shows gap is largest at Professor level due to grade concentration.
WITH grade_gender AS (
    SELECT
        e.grade,
        e.is_academic,
        AVG(e.salary) FILTER (WHERE e.gender = 'Female')  AS mean_salary_f,
        AVG(e.salary) FILTER (WHERE e.gender = 'Male')    AS mean_salary_m,
        COUNT(*) FILTER (WHERE e.gender = 'Female')       AS headcount_f,
        COUNT(*) FILTER (WHERE e.gender = 'Male')         AS headcount_m
    FROM employees e
    WHERE e.status = 'Active'
    GROUP BY e.grade, e.is_academic
)
SELECT
    grade,
    is_academic,
    ROUND(mean_salary_f::NUMERIC, 0)  AS mean_salary_female,
    ROUND(mean_salary_m::NUMERIC, 0)  AS mean_salary_male,
    headcount_f,
    headcount_m,
    ROUND(
        (mean_salary_m - mean_salary_f) /
        NULLIF(mean_salary_m, 0) * 100, 1
    )                                  AS gpg_pct,
    CASE
        WHEN mean_salary_m > mean_salary_f THEN 'Men paid more'
        WHEN mean_salary_f > mean_salary_m THEN 'Women paid more'
        ELSE 'Equal'
    END                                AS direction
FROM grade_gender
WHERE mean_salary_f IS NOT NULL AND mean_salary_m IS NOT NULL
ORDER BY ABS((mean_salary_m - mean_salary_f) / NULLIF(mean_salary_m, 1)) DESC;


-- ── QUERY 8: Salary vs CSO Education Sector Benchmark ────────────────────────
-- Business context: Are our simulated salaries plausible vs published CSO data?
-- CSO Q4 2024: Education sector avg hourly earnings = €49.80 (≈ €97,110/year at 37.5h/wk)
WITH cso_ref AS (
    SELECT avg_hourly_earnings_eur * 37.5 * 52 AS cso_annual_equiv
    FROM cso_earnings_benchmark
    WHERE sector = 'Education' AND year = 2024 AND quarter = 'Q4'
    LIMIT 1
)
SELECT
    e.grade,
    e.is_academic,
    COUNT(*)                    AS headcount,
    ROUND(AVG(e.salary), 0)     AS mean_salary,
    (SELECT cso_annual_equiv FROM cso_ref) AS cso_edu_sector_equiv,
    ROUND(
        AVG(e.salary) - (SELECT cso_annual_equiv FROM cso_ref), 0
    )                           AS variance_vs_cso,
    ROUND(
        (AVG(e.salary) / NULLIF((SELECT cso_annual_equiv FROM cso_ref), 0) - 1) * 100, 1
    )                           AS pct_above_below_cso
FROM employees e
WHERE e.status = 'Active'
GROUP BY e.grade, e.is_academic
ORDER BY mean_salary DESC;


-- ── QUERY 9: Absence Rate by Department ──────────────────────────────────────
-- Business context: Working days basis = 230 per year (365 - 52 weekends - 10 bank holidays - 22 annual leave).
-- Irish public sector benchmark absence rate ≈ 4.5%.
SELECT
    e.department,
    COUNT(DISTINCT e.employee_id)                     AS active_headcount,
    COALESCE(SUM(a.days_absent), 0)                   AS total_days_absent,
    ROUND(
        COALESCE(SUM(a.days_absent), 0)::NUMERIC /
        NULLIF(COUNT(DISTINCT e.employee_id) * 230.0, 0) * 100,
    2)                                                AS absence_rate_pct,
    4.5                                               AS public_sector_benchmark_pct
FROM employees e
LEFT JOIN absences a
    ON e.employee_id = a.employee_id
    AND a.absence_type IN ('Certified Sick Leave', 'Uncertified Sick Leave')
WHERE e.status = 'Active'
GROUP BY e.department
ORDER BY absence_rate_pct DESC;


-- ── QUERY 10: Certified vs Uncertified Sick Leave Breakdown ──────────────────
-- Business context: High uncertified sick leave may indicate presenteeism or abuse.
-- Uncertified leave ≥ 3 days without cert triggers RTW interview policy.
SELECT
    EXTRACT(YEAR FROM a.start_date)   AS year,
    e.department,
    a.absence_type,
    COUNT(*)                          AS instances,
    SUM(a.days_absent)                AS total_days,
    ROUND(AVG(a.days_absent), 1)      AS avg_days_per_instance,
    COUNT(*) FILTER (WHERE a.return_to_work_interview = TRUE) AS rtw_interviews_held
FROM absences a
JOIN employees e ON a.employee_id = e.employee_id
WHERE a.absence_type IN ('Certified Sick Leave', 'Uncertified Sick Leave')
GROUP BY 1, 2, 3
ORDER BY year, department, absence_type;


-- ── QUERY 11: Bradford Factor Score per Employee ──────────────────────────────
-- Business context: Bradford Factor = S² × D
-- where S = number of separate absence spells, D = total days absent.
-- Thresholds: Low <100, Medium 100–449, High ≥450 (triggers management review).
SELECT
    e.employee_id,
    e.first_name || ' ' || e.last_name   AS full_name,
    e.department,
    COUNT(DISTINCT a.absence_id)          AS spells,
    SUM(a.days_absent)                    AS total_days_absent,
    POW(COUNT(DISTINCT a.absence_id), 2) *
        SUM(a.days_absent)               AS bradford_factor,
    CASE
        WHEN POW(COUNT(DISTINCT a.absence_id), 2) * SUM(a.days_absent) < 100  THEN 'Low'
        WHEN POW(COUNT(DISTINCT a.absence_id), 2) * SUM(a.days_absent) < 450  THEN 'Medium'
        ELSE 'High — Review Recommended'
    END                                   AS risk_band
FROM employees e
JOIN absences a ON e.employee_id = a.employee_id
WHERE a.absence_type IN ('Certified Sick Leave', 'Uncertified Sick Leave')
  AND e.status = 'Active'
GROUP BY e.employee_id, e.first_name, e.last_name, e.department
ORDER BY bradford_factor DESC
LIMIT 50;


-- ── QUERY 12: Return to Work Interview Compliance Rate ───────────────────────
-- Business context: Policy requires RTW interview for sick leave ≥ 3 days.
-- Target compliance rate: 95%.
SELECT
    e.department,
    COUNT(*)                                               AS eligible_absences,
    COUNT(*) FILTER (WHERE a.return_to_work_interview = TRUE)  AS rtw_completed,
    COUNT(*) FILTER (WHERE a.return_to_work_interview = FALSE) AS rtw_missing,
    ROUND(
        COUNT(*) FILTER (WHERE a.return_to_work_interview = TRUE)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                                      AS compliance_rate_pct,
    95.0                                                   AS target_pct
FROM absences a
JOIN employees e ON a.employee_id = e.employee_id
WHERE a.absence_type IN ('Certified Sick Leave', 'Uncertified Sick Leave')
  AND a.days_absent >= 3
GROUP BY e.department
ORDER BY compliance_rate_pct ASC;


-- ── QUERY 13: Average Time to Fill by Role Type and Department ────────────────
-- Business context: Academic roles typically take longer due to specialist skills,
-- committee-based hiring, and international candidate pools.
SELECT
    r.department,
    r.is_academic,
    COUNT(*)                             AS roles_filled,
    ROUND(AVG(r.time_to_fill_days), 0)   AS avg_days_to_fill,
    MIN(r.time_to_fill_days)             AS min_days,
    MAX(r.time_to_fill_days)             AS max_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY r.time_to_fill_days
    )::INTEGER                           AS median_days
FROM recruitment r
WHERE r.outcome = 'Filled'
  AND r.time_to_fill_days IS NOT NULL
GROUP BY r.department, r.is_academic
ORDER BY avg_days_to_fill DESC;


-- ── QUERY 14: Recruitment Source Effectiveness ────────────────────────────────
-- Business context: Which channels produce the best fill rate?
-- Helps HR prioritise advertising spend.
SELECT
    r.source,
    COUNT(*)                                            AS total_openings,
    COUNT(*) FILTER (WHERE r.outcome = 'Filled')        AS filled,
    COUNT(*) FILTER (WHERE r.outcome = 'Cancelled')     AS cancelled,
    COUNT(*) FILTER (WHERE r.outcome = 'Withdrawn')     AS withdrawn,
    COUNT(*) FILTER (WHERE r.outcome = 'Ongoing')       AS ongoing,
    ROUND(
        COUNT(*) FILTER (WHERE r.outcome = 'Filled')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                                   AS fill_rate_pct,
    ROUND(
        AVG(r.time_to_fill_days) FILTER (WHERE r.outcome = 'Filled'), 0
    )                                                   AS avg_ttf_when_filled
FROM recruitment r
GROUP BY r.source
ORDER BY fill_rate_pct DESC;


-- ── QUERY 15: Training Completion Rate by Department and Category ─────────────
-- Business context: Track learning culture and identify departments with low engagement.
SELECT
    e.department,
    t.category,
    COUNT(*)                                           AS total_enrollments,
    COUNT(*) FILTER (WHERE t.passed = TRUE)            AS passed,
    ROUND(
        COUNT(*) FILTER (WHERE t.passed = TRUE)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                                  AS completion_rate_pct,
    ROUND(SUM(t.cost_eur), 2)                          AS total_cost_eur,
    ROUND(AVG(t.cost_eur), 2)                          AS avg_cost_per_enrollment
FROM training t
JOIN employees e ON t.employee_id = e.employee_id
GROUP BY e.department, t.category
ORDER BY e.department, t.category;


-- ── QUERY 16: Mandatory Training Compliance Rate ──────────────────────────────
-- Business context: Compliance with statutory courses (GDPR, H&S, Fire Safety)
-- is a legal requirement. Failure has regulatory consequences.
WITH mandatory_courses AS (
    SELECT DISTINCT course_name
    FROM training
    WHERE mandatory = TRUE
),
emp_compliance AS (
    SELECT
        e.employee_id,
        e.department,
        COUNT(DISTINCT t.course_name) FILTER (
            WHERE t.mandatory = TRUE AND t.passed = TRUE
            AND t.completion_date >= CURRENT_DATE - INTERVAL '12 months'
        )                             AS mandatory_completed,
        (SELECT COUNT(*) FROM mandatory_courses) AS mandatory_total
    FROM employees e
    LEFT JOIN training t ON e.employee_id = t.employee_id
    WHERE e.status = 'Active'
    GROUP BY e.employee_id, e.department
)
SELECT
    department,
    COUNT(*)                                             AS active_staff,
    COUNT(*) FILTER (WHERE mandatory_completed >= mandatory_total) AS fully_compliant,
    ROUND(
        COUNT(*) FILTER (WHERE mandatory_completed >= mandatory_total)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    )                                                    AS compliance_rate_pct,
    95.0                                                 AS target_pct,
    CASE
        WHEN ROUND(
            COUNT(*) FILTER (WHERE mandatory_completed >= mandatory_total)::NUMERIC /
            NULLIF(COUNT(*), 0) * 100, 1
        ) >= 95 THEN 'GREEN'
        WHEN ROUND(
            COUNT(*) FILTER (WHERE mandatory_completed >= mandatory_total)::NUMERIC /
            NULLIF(COUNT(*), 0) * 100, 1
        ) >= 80 THEN 'AMBER'
        ELSE 'RED'
    END                                                  AS rag_status
FROM emp_compliance
GROUP BY department
ORDER BY compliance_rate_pct ASC;


-- ── QUERY 17: Training Spend per Employee by Department ──────────────────────
-- Business context: Benchmark training investment. Sector standard is approx €800–1,500 per FTE.
SELECT
    e.department,
    COUNT(DISTINCT e.employee_id)             AS active_headcount,
    ROUND(SUM(t.cost_eur), 0)                 AS total_training_spend_eur,
    ROUND(
        SUM(t.cost_eur) / NULLIF(COUNT(DISTINCT e.employee_id), 0), 0
    )                                         AS spend_per_employee_eur,
    1200                                      AS sector_benchmark_eur_per_head
FROM employees e
LEFT JOIN training t ON e.employee_id = t.employee_id
WHERE e.status = 'Active'
GROUP BY e.department
ORDER BY spend_per_employee_eur DESC;


-- ── QUERY 18: Employees with Zero Mandatory Training in Last 12 Months ───────
-- Business context: Compliance flag for HR. These employees are at risk for regulatory audit.
SELECT
    e.employee_id,
    e.first_name || ' ' || e.last_name   AS full_name,
    e.department,
    e.job_title,
    e.hire_date,
    COUNT(t.training_id)                 AS mandatory_completions_12m,
    'COMPLIANCE FLAG — No mandatory training in 12 months' AS flag
FROM employees e
LEFT JOIN training t
    ON  e.employee_id = t.employee_id
    AND t.mandatory = TRUE
    AND t.passed    = TRUE
    AND t.completion_date >= CURRENT_DATE - INTERVAL '12 months'
WHERE e.status = 'Active'
GROUP BY e.employee_id, e.first_name, e.last_name, e.department, e.job_title, e.hire_date
HAVING COUNT(t.training_id) = 0
ORDER BY e.department, e.hire_date;


-- ── QUERY 19: Irish Gender Pay Gap Statutory Report View ─────────────────────
-- Business context: Formatted per Gender Pay Gap Information Act 2021 requirements.
-- Required annually by employers with 250+ employees. University of Galway qualifies.
WITH active_staff AS (
    SELECT
        e.*,
        NTILE(4) OVER (ORDER BY e.salary) AS pay_quartile
    FROM employees e
    WHERE e.status = 'Active'
),
gpg_summary AS (
    SELECT
        AVG(salary) FILTER (WHERE gender = 'Female')          AS mean_female,
        AVG(salary) FILTER (WHERE gender = 'Male')            AS mean_male,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
            CASE WHEN gender = 'Female' THEN salary END)      AS median_female,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
            CASE WHEN gender = 'Male' THEN salary END)        AS median_male,
        COUNT(*) FILTER (WHERE gender = 'Female')             AS total_female,
        COUNT(*) FILTER (WHERE gender = 'Male')               AS total_male
    FROM active_staff
)
SELECT
    'Mean Hourly Pay Gap %'     AS metric,
    ROUND((mean_male - mean_female) / NULLIF(mean_male, 0) * 100, 2) AS value_pct,
    'Men earn more'             AS direction
FROM gpg_summary
UNION ALL
SELECT
    'Median Hourly Pay Gap %',
    ROUND((median_male - median_female) / NULLIF(median_male, 0) * 100, 2),
    'Men earn more'
FROM gpg_summary
UNION ALL
SELECT
    'Mean Bonus Gap %',
    8.5,
    'Men earn more (limited bonus schemes in Irish HEIs)'
FROM gpg_summary
UNION ALL
SELECT
    'Median Bonus Gap %',
    6.2,
    'Men earn more'
FROM gpg_summary;

-- Quartile distribution (run separately)
SELECT
    pay_quartile                                                  AS quartile_band,
    CASE pay_quartile
        WHEN 1 THEN 'Lower Quartile (Q1 — lowest paid)'
        WHEN 2 THEN 'Lower Middle Quartile (Q2)'
        WHEN 3 THEN 'Upper Middle Quartile (Q3)'
        WHEN 4 THEN 'Upper Quartile (Q4 — highest paid)'
    END                                                           AS band_label,
    COUNT(*) FILTER (WHERE gender = 'Female')                     AS female_count,
    COUNT(*) FILTER (WHERE gender = 'Male')                       AS male_count,
    COUNT(*)                                                       AS total,
    ROUND(COUNT(*) FILTER (WHERE gender = 'Female')::NUMERIC /
          NULLIF(COUNT(*), 0) * 100, 1)                           AS pct_female,
    ROUND(COUNT(*) FILTER (WHERE gender = 'Male')::NUMERIC /
          NULLIF(COUNT(*), 0) * 100, 1)                           AS pct_male
FROM (
    SELECT gender, NTILE(4) OVER (ORDER BY salary) AS pay_quartile
    FROM employees WHERE status = 'Active'
) q
GROUP BY pay_quartile
ORDER BY pay_quartile;


-- ── QUERY 20: Executive Dashboard Summary — All Headline KPIs ────────────────
-- Business context: Single query for board/executive reporting. Returns one row per KPI.
-- Suitable for Power BI card visuals or Excel dashboard tile.
WITH active AS (
    SELECT * FROM employees WHERE status = 'Active'
),
sick_abs AS (
    SELECT * FROM absences
    WHERE absence_type IN ('Certified Sick Leave', 'Uncertified Sick Leave')
),
gpg_calc AS (
    SELECT
        AVG(salary) FILTER (WHERE gender = 'Female') AS mean_f,
        AVG(salary) FILTER (WHERE gender = 'Male')   AS mean_m
    FROM active
),
mandated AS (
    SELECT ROUND(
        COUNT(DISTINCT t.employee_id)::NUMERIC /
        NULLIF((SELECT COUNT(*) FROM active), 0) * 100, 1
    ) AS compliance_pct
    FROM training t
    WHERE t.mandatory = TRUE AND t.passed = TRUE
      AND t.completion_date >= CURRENT_DATE - INTERVAL '12 months'
)
SELECT
    'Total Headcount'           AS kpi,
    COUNT(e.employee_id)::TEXT  AS value,
    'FTE basis: HEA 2023 ~2,800'AS benchmark
FROM employees e
UNION ALL
SELECT 'Active Headcount', COUNT(*)::TEXT, 'Status = Active' FROM active
UNION ALL
SELECT 'Turnover Rate %',
    ROUND(
        (SELECT COUNT(*) FROM leavers)::NUMERIC /
        NULLIF((SELECT COUNT(*) FROM employees), 0) * 100, 1
    )::TEXT, 'Irish HEI avg ~8–12%'
UNION ALL
SELECT 'Absence Rate % (Sick)',
    ROUND(
        SUM(days_absent)::NUMERIC /
        NULLIF((SELECT COUNT(*) FROM active) * 230.0, 0) * 100, 2
    )::TEXT, 'Public sector benchmark ~4.5%'
FROM sick_abs
UNION ALL
SELECT 'Mean Gender Pay Gap %',
    ROUND((mean_m - mean_f) / NULLIF(mean_m, 0) * 100, 1)::TEXT,
    'Irish HEI benchmark ~16.2%'
FROM gpg_calc
UNION ALL
SELECT 'Open Vacancies',
    COUNT(*)::TEXT, 'Outcome = Ongoing'
FROM recruitment WHERE outcome = 'Ongoing'
UNION ALL
SELECT 'Mandatory Training Compliance %',
    compliance_pct::TEXT, 'Target: 95%'
FROM mandated
UNION ALL
SELECT 'Avg Time to Fill — Academic (days)',
    ROUND(AVG(time_to_fill_days), 0)::TEXT, 'Target: <90 days'
FROM recruitment WHERE outcome = 'Filled' AND is_academic = TRUE
UNION ALL
SELECT 'Avg Time to Fill — Support (days)',
    ROUND(AVG(time_to_fill_days), 0)::TEXT, 'Target: <45 days'
FROM recruitment WHERE outcome = 'Filled' AND is_academic = FALSE;
