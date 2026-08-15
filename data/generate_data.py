import pandas as pd
import numpy as np
from datetime import timedelta
import os

np.random.seed(42)

def generate_data():
    num_households = 100
    days = 30
    
    # 1. Generate Household Info
    household_ids = [f'HH_{str(i).zfill(3)}' for i in range(1, num_households + 1)]
    
    regions = np.random.choice(['Urban', 'Semi-urban', 'Rural'], size=num_households, p=[0.2, 0.3, 0.5])
    sizes = np.random.randint(1, 9, size=num_households)
    
    # Income based on region
    incomes = []
    for r in regions:
        if r == 'Urban':
            incomes.append(np.random.choice(['Low', 'Medium', 'High'], p=[0.2, 0.5, 0.3]))
        elif r == 'Semi-urban':
            incomes.append(np.random.choice(['Low', 'Medium', 'High'], p=[0.4, 0.5, 0.1]))
        else:
            incomes.append(np.random.choice(['Low', 'Medium', 'High'], p=[0.7, 0.25, 0.05]))
            
    has_solar = np.random.choice([0, 1], size=num_households, p=[0.7, 0.3])
    solar_capacity = np.where(has_solar == 1, np.random.choice([50, 100, 200, 400], size=num_households), 0)
    
    budgets = np.random.normal(loc=15, scale=5, size=num_households)
    budgets = np.where(np.array(incomes) == 'High', budgets * 2, budgets)
    budgets = np.clip(budgets, 5, 100).round(2)
    
    household_info = pd.DataFrame({
        'household_id': household_ids,
        'region': regions,
        'household_size': sizes,
        'income_level': incomes,
        'has_solar_system': has_solar,
        'solar_capacity_watts': solar_capacity,
        'monthly_energy_budget_usd': budgets
    })
    
    household_info.to_csv('household_info.csv', index=False)
    
    # 2. Generate Energy Consumption Data
    start_date = pd.to_datetime('2024-01-01')
    timestamps = pd.date_range(start=start_date, periods=24 * days, freq='h')
    
    data = []
    reading_id = 1
    
    for i, hh in household_info.iterrows():
        hh_id = hh['household_id']
        solar = hh['has_solar_system']
        capacity = hh['solar_capacity_watts']
        region = hh['region']
        
        # Base consumption multiplier
        base_mult = 1.0
        if region == 'Rural': base_mult = 0.6
        if hh['income_level'] == 'High': base_mult *= 1.5
        
        grid_status = 'Off-grid' if region == 'Rural' and np.random.random() < 0.7 else ('Hybrid' if solar else 'On-grid')
        
        # Hourly profile pattern (base)
        # Night: low, Morning 6-9: high, Evening 18-22: high
        daily_pattern = np.array([0.2, 0.15, 0.1, 0.1, 0.1, 0.2, 0.8, 1.2, 1.0, 0.8, 0.6, 0.5, 
                                 0.5, 0.5, 0.6, 0.7, 0.8, 1.2, 1.5, 1.8, 1.6, 1.2, 0.8, 0.4])
                                 
        for t in timestamps:
            hour = t.hour
            
            # Consumption based on pattern + noise
            noise = np.random.normal(0, 0.1)
            consumption = max(0, (daily_pattern[hour] + noise) * base_mult * 0.5)
            
            # Solar impact during daytime (8 to 17)
            if solar and 8 <= hour <= 17:
                solar_reduction = min(consumption * 0.8, capacity / 1000.0)
                consumption = max(0.01, consumption - solar_reduction)
                
            # Random anomalies
            if np.random.random() < 0.001:
                consumption *= np.random.uniform(2, 5)
                
            # Voltage / Current
            voltage = np.random.normal(220 if grid_status == 'On-grid' else 12, 5 if grid_status == 'On-grid' else 0.5)
            current = consumption * 1000 / voltage if voltage > 0 else 0
            
            # Appliances
            categories = ['Lighting', 'Cooking', 'Cooling', 'Entertainment', 'Charging', 'Other']
            if hour in [18, 19, 20, 21]: probs = [0.3, 0.2, 0.1, 0.3, 0.05, 0.05]
            elif hour in [7, 8, 9]: probs = [0.1, 0.4, 0.1, 0.1, 0.2, 0.1]
            else: probs = [0.1, 0.1, 0.4, 0.1, 0.1, 0.2]
            
            appliance = np.random.choice(categories, p=probs)
            
            data.append([
                reading_id, hh_id, t, round(consumption, 4), round(voltage, 2), 
                round(current, 2), appliance, solar, grid_status
            ])
            reading_id += 1
            
    consumption_df = pd.DataFrame(data, columns=[
        'reading_id', 'household_id', 'timestamp', 'energy_kwh', 'voltage', 
        'current_amps', 'appliance_category', 'is_solar_powered', 'grid_status'
    ])
    
    consumption_df.to_csv('energy_consumption.csv', index=False)

if __name__ == "__main__":
    generate_data()
    print("Data generation complete.")
