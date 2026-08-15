-- 01_consumption_overview.sql
-- Total energy consumed, average daily consumption per household
SELECT 
    h.household_id,
    COUNT(c.reading_id) / 24.0 as days_recorded,
    SUM(c.energy_kwh) as total_energy_kwh,
    SUM(c.energy_kwh) / (COUNT(c.reading_id) / 24.0) as avg_daily_consumption_kwh
FROM household_info h
JOIN energy_consumption c ON h.household_id = c.household_id
GROUP BY h.household_id;

-- Peak vs off-peak consumption comparison
-- Assuming Peak: 06:00-09:00 and 18:00-22:00
WITH HourlyData AS (
    SELECT 
        energy_kwh,
        CAST(strftime('%H', timestamp) AS INTEGER) as hour_of_day
    FROM energy_consumption
)
SELECT 
    CASE 
        WHEN hour_of_day IN (6,7,8,18,19,20,21) THEN 'Peak'
        ELSE 'Off-Peak'
    END as period_type,
    AVG(energy_kwh) as avg_hourly_consumption,
    SUM(energy_kwh) as total_consumption
FROM HourlyData
GROUP BY period_type;

-- Consumption by grid status and region
SELECT 
    h.region,
    c.grid_status,
    COUNT(DISTINCT h.household_id) as num_households,
    AVG(c.energy_kwh) as avg_hourly_consumption,
    SUM(c.energy_kwh) as total_consumption
FROM household_info h
JOIN energy_consumption c ON h.household_id = c.household_id
GROUP BY h.region, c.grid_status
ORDER BY h.region, total_consumption DESC;

-- Top 10 highest consuming households
SELECT 
    h.household_id,
    h.region,
    h.income_level,
    h.has_solar_system,
    SUM(c.energy_kwh) as total_consumption_kwh
FROM household_info h
JOIN energy_consumption c ON h.household_id = c.household_id
GROUP BY h.household_id, h.region, h.income_level, h.has_solar_system
ORDER BY total_consumption_kwh DESC
LIMIT 10;
