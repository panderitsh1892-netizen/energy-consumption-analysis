-- 02_pattern_analysis.sql
-- Hourly consumption profile (avg by hour of day)
SELECT 
    CAST(strftime('%H', timestamp) AS INTEGER) as hour_of_day,
    AVG(energy_kwh) as avg_consumption
FROM energy_consumption
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Daily consumption trend over time
SELECT 
    date(timestamp) as consumption_date,
    SUM(energy_kwh) as total_daily_consumption,
    AVG(energy_kwh) as avg_hourly_consumption
FROM energy_consumption
GROUP BY consumption_date
ORDER BY consumption_date;

-- Weekday vs weekend patterns
SELECT 
    CASE 
        WHEN CAST(strftime('%w', timestamp) AS INTEGER) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    CAST(strftime('%H', timestamp) AS INTEGER) as hour_of_day,
    AVG(energy_kwh) as avg_consumption
FROM energy_consumption
GROUP BY day_type, hour_of_day
ORDER BY day_type, hour_of_day;

-- Monthly consumption by appliance category
SELECT 
    strftime('%Y-%m', timestamp) as consumption_month,
    appliance_category,
    SUM(energy_kwh) as total_consumption
FROM energy_consumption
GROUP BY consumption_month, appliance_category
ORDER BY consumption_month, total_consumption DESC;

-- Solar vs non-solar household comparison using window functions
WITH HouseholdDaily AS (
    SELECT 
        c.household_id,
        h.has_solar_system,
        date(c.timestamp) as consumption_date,
        SUM(c.energy_kwh) as daily_kwh
    FROM energy_consumption c
    JOIN household_info h ON c.household_id = h.household_id
    GROUP BY c.household_id, h.has_solar_system, consumption_date
)
SELECT 
    has_solar_system,
    AVG(daily_kwh) as avg_daily_consumption,
    MIN(daily_kwh) as min_daily_consumption,
    MAX(daily_kwh) as max_daily_consumption
FROM HouseholdDaily
GROUP BY has_solar_system;

-- Anomaly detection: households with consumption > 2 std deviations from mean (using CTE + window functions)
WITH HouseholdStats AS (
    SELECT 
        household_id,
        SUM(energy_kwh) as total_consumption
    FROM energy_consumption
    GROUP BY household_id
),
GlobalStats AS (
    SELECT 
        AVG(total_consumption) as mean_consumption,
        -- Approximate STDEV in SQLite (requires extension usually, but we simulate variance here)
        SQRT(AVG(total_consumption * total_consumption) - AVG(total_consumption) * AVG(total_consumption)) as stddev_consumption
    FROM HouseholdStats
)
SELECT 
    h.household_id,
    h.total_consumption,
    g.mean_consumption,
    g.stddev_consumption,
    (h.total_consumption - g.mean_consumption) / g.stddev_consumption as z_score
FROM HouseholdStats h
CROSS JOIN GlobalStats g
WHERE h.total_consumption > g.mean_consumption + (2 * g.stddev_consumption)
ORDER BY z_score DESC;
