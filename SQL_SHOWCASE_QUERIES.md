# 40 SQL Showcase Queries (Basic to Advanced)

This document contains a curated list of 40 SQL queries specifically designed to demonstrate the depth, relational architecture, and advanced querying capabilities of the Portfolio Recommendation System. 

You can run these directly against NeonDB using your database client (like pgAdmin or DBeaver) to showcase the system's logic to your teacher.

---

## Part 1: Basic Queries (Familiarity & State)
*These demonstrate basic `SELECT`, `WHERE`, and system state inspection.*

**1. Retrieve all registered users ordered by newest first.**
```sql
SELECT user_id, name, email, created_at 
FROM users 
ORDER BY created_at DESC;
```

**2. Inspect all predefined Risk Profiles and their score boundaries.**
```sql
SELECT risk_profile_id, profile_name, min_score, max_score 
FROM risk_profiles 
ORDER BY min_score ASC;
```

**3. Find all users who have completed the financial questionnaire.**
```sql
SELECT user_id, risk_score, investment_amount 
FROM user_profiles 
WHERE risk_score IS NOT NULL;
```

**4. List all active financial instruments available in the system.**
```sql
SELECT instrument_id, name, ticker, instrument_type 
FROM instruments 
WHERE is_active = TRUE;
```

**5. View the system's Audit Log for a specific action (e.g., Portfolio Generation).**
```sql
SELECT log_id, user_id, metadata, created_at 
FROM audit_log 
WHERE action = 'PORTFOLIO_GENERATED' 
ORDER BY created_at DESC;
```

---

## Part 2: Intermediate Queries (Joins & Aggregations)
*These demonstrate `JOIN`s mapping foreign keys, aggregating data (`SUM`, `COUNT`), and `GROUP BY`.*

**6. Count how many users fall into each Risk Profile bucket.**
```sql
SELECT rp.profile_name, COUNT(up.user_id) AS total_users
FROM user_profiles up
JOIN risk_profiles rp ON up.risk_profile_id = rp.risk_profile_id
GROUP BY rp.profile_name
ORDER BY total_users DESC;
```

**7. Join Instruments with their parent Asset Classes.**
```sql
SELECT i.name AS instrument, i.ticker, ac.name AS asset_class
FROM instruments i
JOIN asset_classes ac ON i.asset_class_id = ac.asset_class_id;
```

**8. Calculate the total aggregate capital managed by the application.**
```sql
SELECT SUM(total_investment) AS total_assets_under_management 
FROM user_portfolios 
WHERE is_active = TRUE;
```

**9. Find the top 5 users with the largest monthly incomes.**
```sql
SELECT u.name, up.monthly_income, up.investment_amount
FROM users u
JOIN user_profiles up ON u.user_id = up.user_id
ORDER BY up.monthly_income DESC NULLS LAST
LIMIT 5;
```

**10. Count the number of available instruments per Asset Class.**
```sql
SELECT ac.name, COUNT(i.instrument_id) AS number_of_instruments
FROM asset_classes ac
LEFT JOIN instruments i ON ac.asset_class_id = i.asset_class_id
GROUP BY ac.name;
```

**11. Find the Average Risk Score of all users.**
```sql
SELECT ROUND(AVG(risk_score), 2) AS average_risk_score 
FROM user_profiles;
```

**12. View the exact line-item positions for a specific portfolio (e.g., Portfolio ID 1).**
```sql
SELECT i.name, upp.allocation_percentage, upp.allocated_amount
FROM user_portfolio_positions upp
JOIN instruments i ON upp.instrument_id = i.instrument_id
WHERE upp.portfolio_id = 1;
```

**13. Show which Model is most frequently assigned to active portfolios.**
```sql
SELECT pm.model_name, COUNT(up.portfolio_id) AS assignment_count
FROM user_portfolios up
JOIN portfolio_models pm ON up.model_id = pm.model_id
WHERE up.is_active = TRUE
GROUP BY pm.model_name
ORDER BY assignment_count DESC;
```

**14. View the macro asset-class splits for the "Aggressive Growth" model.**
```sql
SELECT pm.model_name, ac.name AS asset_class, pa.allocation_percentage
FROM portfolio_allocations pa
JOIN portfolio_models pm ON pa.model_id = pm.model_id
JOIN asset_classes ac ON pa.asset_class_id = ac.asset_class_id
WHERE pm.model_name = 'Aggressive Growth';
```

**15. Verify that all Portfolio Models perfectly add up to 100% allocation.**
```sql
SELECT pm.model_name, SUM(pa.allocation_percentage) AS total_percentage
FROM portfolio_allocations pa
JOIN portfolio_models pm ON pa.model_id = pm.model_id
GROUP BY pm.model_name
HAVING SUM(pa.allocation_percentage) != 100; -- Should return 0 rows!
```

---

## Part 3: Advanced Queries (Subqueries, JSONB, & Complexity)
*These queries showcase advanced SQL constraints, sub-selects, casting, and extracting data from JSON objects.*

**16. Extract the exact 'new_risk_score' natively from the JSONB audit log.**
```sql
SELECT user_id, created_at, 
       metadata->>'new_risk_score' AS new_score, 
       metadata->>'old_risk_score' AS old_score
FROM audit_log
WHERE action = 'RISK_SCORE_UPDATED';
```

**17. Find users who have an investment amount higher than the system average.**
```sql
SELECT u.name, up.investment_amount 
FROM users u
JOIN user_profiles up ON u.user_id = up.user_id
WHERE up.investment_amount > (
    SELECT AVG(investment_amount) FROM user_profiles
);
```

**18. Identify "Orphaned" instruments (Funds not used in any allocation template).**
```sql
SELECT i.name, i.ticker 
FROM instruments i
LEFT JOIN instrument_allocations ia ON i.instrument_id = ia.instrument_id
WHERE ia.inst_allocation_id IS NULL;
```

**19. Calculate the Investment-to-Income ratio for all users.**
```sql
SELECT u.name, up.monthly_income, up.investment_amount,
       ROUND((up.investment_amount / NULLIF(up.monthly_income, 0)) * 100, 2) AS investment_income_ratio_pct
FROM users u
JOIN user_profiles up ON u.user_id = up.user_id
WHERE up.monthly_income > 0;
```

**20. Find users who generated a portfolio but have since become inactive.**
```sql
SELECT u.name, u.email 
FROM users u
WHERE EXISTS (
    SELECT 1 FROM user_portfolios up WHERE up.user_id = u.user_id AND up.is_active = FALSE
) AND NOT EXISTS (
    SELECT 1 FROM user_portfolios up WHERE up.user_id = u.user_id AND up.is_active = TRUE
);
```

**21. Extract the specific 'portfolio_id' generated by a user directly from the JSON audit metadata trail.**
```sql
SELECT user_id, CAST(metadata->>'portfolio_id' AS INTEGER) AS generated_portfolio_id
FROM audit_log
WHERE action = 'PORTFOLIO_GENERATED';
```

**22. Calculate the historical spread (Max Return - Min Return) for 5-Year yields.**
```sql
SELECT MAX(return_percentage) - MIN(return_percentage) AS five_year_return_spread
FROM instrument_returns
WHERE period = '5Y';
```

**23. Find any users who updated their risk score more than 2 times.**
```sql
SELECT user_id, COUNT(*) as change_count
FROM audit_log
WHERE action = 'RISK_SCORE_UPDATED'
GROUP BY user_id
HAVING COUNT(*) > 2;
```

**24. List portfolios that rely heavily (>40%) on a single specific instrument.**
```sql
SELECT up.portfolio_id, i.name, upp.allocation_percentage
FROM user_portfolio_positions upp
JOIN instruments i ON upp.instrument_id = i.instrument_id
JOIN user_portfolios up ON upp.portfolio_id = up.portfolio_id
WHERE upp.allocation_percentage > 40;
```

**25. Find the underlying 'Fund House' managing the most system capital.**
```sql
SELECT i.fund_house, SUM(upp.allocated_amount) AS total_managed_dollars
FROM user_portfolio_positions upp
JOIN instruments i ON upp.instrument_id = i.instrument_id
GROUP BY i.fund_house
ORDER BY total_managed_dollars DESC;
```

---

## Part 4: Expert Level (Window Functions, CTEs, & Dynamic Calculation)
*These showcase DBA-level queries using Common Table Expressions (`WITH`), `ROW_NUMBER()`, `RANK()`, and algorithmic pivoting.*

**26. Pivot instrument returns so 1Y, 3Y, and 5Y are columns (Simulating the App View).**
```sql
SELECT 
    i.ticker,
    MAX(CASE WHEN ir.period = '1Y' THEN ir.return_percentage END) AS "1Y_Return",
    MAX(CASE WHEN ir.period = '3Y' THEN ir.return_percentage END) AS "3Y_Return",
    MAX(CASE WHEN ir.period = '5Y' THEN ir.return_percentage END) AS "5Y_Return"
FROM instruments i
LEFT JOIN instrument_returns ir ON i.instrument_id = ir.instrument_id
GROUP BY i.ticker;
```

**27. Use a Window Function to Rank users by their total capital investment.**
```sql
SELECT 
    user_id, 
    total_investment,
    DENSE_RANK() OVER (ORDER BY total_investment DESC) AS investment_rank
FROM user_portfolios
WHERE is_active = TRUE;
```

**28. Use a Window Function to find the top performing Instrument per Asset Class (over 5 Years).**
```sql
WITH RankedInstruments AS (
    SELECT i.name, ac.name as asset_class, ir.return_percentage,
           ROW_NUMBER() OVER(PARTITION BY i.asset_class_id ORDER BY ir.return_percentage DESC) as rank
    FROM instruments i
    JOIN asset_classes ac ON i.asset_class_id = ac.asset_class_id
    JOIN instrument_returns ir ON i.instrument_id = ir.instrument_id
    WHERE ir.period = '5Y'
)
SELECT name, asset_class, return_percentage 
FROM RankedInstruments 
WHERE rank = 1;
```

**29. CTE: Identify users whose calculated risk profile ID mismatches their actual score (Data Integrity Check).**
```sql
WITH CalculatedProfiles AS (
    SELECT up.user_id, up.risk_score, up.risk_profile_id AS saved_profile,
           rp.risk_profile_id AS true_profile
    FROM user_profiles up
    JOIN risk_profiles rp ON up.risk_score BETWEEN rp.min_score AND rp.max_score
)
SELECT * FROM CalculatedProfiles 
WHERE saved_profile != true_profile; 
-- Should return 0 rows in a healthy system
```

**30. Calculate a Running Total (Cumulative Sum) of all active investments in the platform.**
```sql
SELECT 
    portfolio_id, 
    generated_at, 
    total_investment,
    SUM(total_investment) OVER (ORDER BY generated_at ASC) as cumulative_capital
FROM user_portfolios
WHERE is_active = TRUE;
```

**31. Mathematical Audit: Verify that the sub-items for a portfolio exactly equal the parent total.**
```sql
WITH PositionSums AS (
    SELECT portfolio_id, SUM(allocated_amount) as summed_amount
    FROM user_portfolio_positions
    GROUP BY portfolio_id
)
SELECT up.portfolio_id, up.total_investment, ps.summed_amount,
       (up.total_investment - ps.summed_amount) AS discrepancy
FROM user_portfolios up
JOIN PositionSums ps ON up.portfolio_id = ps.portfolio_id
WHERE ABS(up.total_investment - ps.summed_amount) > 0.01; 
-- Checks for rounding errors across thousands of dollars
```

**32. Identify "Risk Creep": Users whose current risk score is higher than their historical average.**
```sql
WITH HistoricalAvg AS (
    SELECT user_id, AVG(CAST(metadata->>'new_risk_score' AS NUMERIC)) as avg_hist_score
    FROM audit_log
    WHERE action = 'RISK_SCORE_UPDATED'
    GROUP BY user_id
)
SELECT up.user_id, up.risk_score AS current_score, ha.avg_hist_score
FROM user_profiles up
JOIN HistoricalAvg ha ON up.user_id = ha.user_id
WHERE up.risk_score > ha.avg_hist_score;
```

**33. Dynamically calculate the theoretical 1Y dollar return for every active user.**
```sql
SELECT 
    u.name,
    up.total_investment,
    ROUND(SUM(upp.allocated_amount * (ir.return_percentage / 100)), 2) AS projected_1y_gain,
    ROUND(up.total_investment + SUM(upp.allocated_amount * (ir.return_percentage / 100)), 2) AS projected_1y_balance
FROM user_portfolios up
JOIN users u ON up.user_id = u.user_id
JOIN user_portfolio_positions upp ON up.portfolio_id = upp.portfolio_id
JOIN instrument_returns ir ON upp.instrument_id = ir.instrument_id
WHERE up.is_active = TRUE AND ir.period = '1Y'
GROUP BY u.name, up.total_investment;
```

**34. Dynamic Percentage Re-assembly (Macro * Micro).**
Wait, how exactly does the system know the VOO percentage? It multiplies the Model's Equity % by the Template's VOO %. Let's recreate that logic natively in SQL:
```sql
SELECT 
    pm.model_name,
    ac.name AS asset_class,
    i.ticker,
    pa.allocation_percentage AS macro_pct,
    ia.allocation_percentage AS micro_pct,
    (pa.allocation_percentage * ia.allocation_percentage / 100) AS true_portfolio_pct
FROM portfolio_models pm
JOIN portfolio_allocations pa ON pm.model_id = pa.model_id
JOIN asset_classes ac ON pa.asset_class_id = ac.asset_class_id
JOIN sub_allocation_templates sat ON pm.model_id = sat.model_id AND ac.asset_class_id = sat.asset_class_id
JOIN instrument_allocations ia ON sat.template_id = ia.template_id
JOIN instruments i ON ia.instrument_id = i.instrument_id
ORDER BY pm.model_id, true_portfolio_pct DESC;
```

**35. Lead/Lag Window Analysis: Find days between consecutive portfolio generations.**
```sql
SELECT 
    user_id, 
    generated_at,
    LAG(generated_at) OVER (PARTITION BY user_id ORDER BY generated_at ASC) as previous_generation,
    EXTRACT(DAY FROM (generated_at - LAG(generated_at) OVER (PARTITION BY user_id ORDER BY generated_at ASC))) as days_between
FROM user_portfolios;
```

**36. Determine the percentile of a user's investment amount compared to the entire system.**
```sql
SELECT 
    user_id, 
    investment_amount,
    ROUND(CUME_DIST() OVER (ORDER BY investment_amount ASC) * 100, 2) AS wealth_percentile
FROM user_profiles;
```

**37. Recreate the precise `views.sql` aggregate manually.**
```sql
SELECT 
    up.portfolio_id,
    ac.name AS asset_category,
    SUM(upp.allocation_percentage) AS bucket_percentage
FROM user_portfolios up
JOIN user_portfolio_positions upp ON up.portfolio_id = upp.portfolio_id
JOIN instruments i ON upp.instrument_id = i.instrument_id
JOIN asset_classes ac ON i.asset_class_id = ac.asset_class_id
GROUP BY up.portfolio_id, ac.name
ORDER BY up.portfolio_id, bucket_percentage DESC;
```

**38. Evaluate system stability: Detect any portfolios that have no underlying positions.**
```sql
SELECT up.portfolio_id, up.user_id, up.total_investment
FROM user_portfolios up
LEFT JOIN user_portfolio_positions upp ON up.portfolio_id = upp.portfolio_id
WHERE upp.position_id IS NULL; 
-- A properly functioning system will return 0 rows.
```

**39. Detect Asset Class overlap inside sub-allocation templates.**
```sql
SELECT sat.model_id, sat.asset_class_id, COUNT(ia.instrument_id) as instruments_in_bucket
FROM sub_allocation_templates sat
JOIN instrument_allocations ia ON sat.template_id = ia.template_id
GROUP BY sat.model_id, sat.asset_class_id
HAVING COUNT(ia.instrument_id) > 5; -- Flags extremely complex buckets holding > 5 tickers
```

**40. Calculate the System-Wide Standard Deviation of Risk Scores.**
```sql
SELECT 
    ROUND(AVG(risk_score), 2) AS mean_risk,
    ROUND(STDDEV(risk_score), 2) AS risk_standard_deviation,
    MIN(risk_score) AS lowest_risk,
    MAX(risk_score) AS highest_risk
FROM user_profiles;
```
