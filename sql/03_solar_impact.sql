-- 03_solar_impact.sql
-- Energy savings from solar: avg consumption solar vs non-solar
SELECT 
    has_solar_system,
    COUNT(DISTINCT c.household_id) as num_households,
    AVG(c.energy_kwh) as avg_hourly_kwh,
    AVG(c.energy_kwh) * 24 as avg_daily_kwh
FROM energy_consumption c
JOIN household_info h ON c.household_id = h.household_id
GROUP BY has_solar_system;

-- Cost savings estimation (assume $0.15/kWh grid cost)
WITH MonthlyConsumption AS (
    SELECT 
        h.household_id,
        h.has_solar_system,
        strftime('%Y-%m', c.timestamp) as month,
        SUM(c.energy_kwh) as total_kwh
    FROM energy_consumption c
    JOIN household_info h ON c.household_id = h.household_id
    GROUP BY h.household_id, h.has_solar_system, month
)
SELECT 
    has_solar_system,
    AVG(total_kwh) as avg_monthly_kwh,
    AVG(total_kwh) * 0.15 as est_monthly_cost_usd
FROM MonthlyConsumption
GROUP BY has_solar_system;

-- Solar ROI analysis by capacity tier
WITH SolarCapacityGroups AS (
    SELECT 
        h.solar_capacity_watts,
        COUNT(DISTINCT c.household_id) as num_households,
        AVG(c.energy_kwh) * 24 * 30 as avg_monthly_kwh
    FROM energy_consumption c
    JOIN household_info h ON c.household_id = h.household_id
    GROUP BY h.solar_capacity_watts
)
SELECT 
    solar_capacity_watts,
    num_households,
    avg_monthly_kwh,
    avg_monthly_kwh * 0.15 as grid_equivalent_cost_usd,
    -- Estimate solar generation: Capacity (kW) * 5 peak sun hours * 30 days
    (solar_capacity_watts / 1000.0) * 5 * 30 as est_monthly_generation_kwh,
    ((solar_capacity_watts / 1000.0) * 5 * 30) * 0.15 as est_monthly_savings_usd
FROM SolarCapacityGroups
ORDER BY solar_capacity_watts;

-- Which regions benefit most from solar?
SELECT 
    h.region,
    h.has_solar_system,
    AVG(c.energy_kwh) * 24 as avg_daily_kwh
FROM energy_consumption c
JOIN household_info h ON c.household_id = h.household_id
GROUP BY h.region, h.has_solar_system
ORDER BY h.region, h.has_solar_system;

-- Recommendation query: households that would benefit most from solar upgrade (high consumption + no solar + rural)
SELECT 
    h.household_id,
    h.region,
    h.income_level,
    h.monthly_energy_budget_usd,
    SUM(c.energy_kwh) as total_consumption,
    (SUM(c.energy_kwh) * 0.15) as est_total_cost_usd
FROM household_info h
JOIN energy_consumption c ON h.household_id = c.household_id
WHERE h.has_solar_system = 0 AND h.region = 'Rural'
GROUP BY h.household_id
HAVING est_total_cost_usd > h.monthly_energy_budget_usd
ORDER BY total_consumption DESC
LIMIT 15;
