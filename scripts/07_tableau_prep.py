import pandas as pd
import numpy as np
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    tableau_dir = os.path.join(base_dir, 'tableau_data')
    os.makedirs(tableau_dir, exist_ok=True)
    
    # Read CSVs
    df_cons = pd.read_csv(os.path.join(data_dir, 'energy_consumption.csv'))
    df_info = pd.read_csv(os.path.join(data_dir, 'household_info.csv'))
    
    # 1. consumption_enriched.csv
    df_cons['timestamp'] = pd.to_datetime(df_cons['timestamp'])
    df_cons['date'] = df_cons['timestamp'].dt.date
    df_cons['hour'] = df_cons['timestamp'].dt.hour
    df_cons['day_of_week'] = df_cons['timestamp'].dt.day_name()
    df_cons['is_weekend'] = df_cons['timestamp'].dt.dayofweek >= 5
    
    def time_period(h):
        if 5 <= h < 12: return 'Morning'
        elif 12 <= h < 17: return 'Afternoon'
        elif 17 <= h < 22: return 'Evening'
        else: return 'Night'
    df_cons['time_period'] = df_cons['hour'].apply(time_period)
    
    df_cons['is_peak_hour'] = df_cons['hour'].apply(lambda h: (6 <= h <= 9) or (18 <= h <= 22))
    
    # Join with info
    df_merged = pd.merge(df_cons, df_info, on='household_id', how='left')
    # Save enriched
    df_merged.to_csv(os.path.join(tableau_dir, 'consumption_enriched.csv'), index=False)
    
    # 2. daily_summary.csv
    daily_df = df_merged.groupby(['date', 'household_id', 'region', 'has_solar_system']).agg(
        total_kwh=('energy_kwh', 'sum'),
    ).reset_index()
    
    daily_df = daily_df.rename(columns={'has_solar_system': 'has_solar'})
    
    peak_df = df_merged[df_merged['is_peak_hour']].groupby(['date', 'household_id'])['energy_kwh'].sum().reset_index(name='peak_kwh')
    offpeak_df = df_merged[~df_merged['is_peak_hour']].groupby(['date', 'household_id'])['energy_kwh'].sum().reset_index(name='off_peak_kwh')
    
    daily_df = pd.merge(daily_df, peak_df, on=['date', 'household_id'], how='left')
    daily_df = pd.merge(daily_df, offpeak_df, on=['date', 'household_id'], how='left')
    daily_df.fillna(0, inplace=True)
    
    # Cost & savings
    # Assume 0.15/kWh off-peak, 0.25/kWh peak
    daily_df['estimated_cost_usd'] = daily_df['peak_kwh'] * 0.25 + daily_df['off_peak_kwh'] * 0.15
    # Dummy solar savings
    daily_df['solar_savings_usd'] = np.where(daily_df['has_solar'], daily_df['total_kwh'] * 0.05, 0)
    
    daily_df.to_csv(os.path.join(tableau_dir, 'daily_summary.csv'), index=False)
    
    # 3. household_profiles.csv
    profile_df = df_merged.groupby(['household_id', 'region', 'income_level', 'has_solar_system', 'solar_capacity_watts']).agg(
        avg_daily_kwh=('energy_kwh', lambda x: x.sum() / df_merged['date'].nunique()),
        total_cost_usd=('energy_kwh', lambda x: x.sum() * 0.2)  # Simplified cost
    ).reset_index()
    
    profile_df = profile_df.rename(columns={'has_solar_system': 'has_solar', 'solar_capacity_watts': 'solar_capacity'})
    
    # Find peak consumption hour per household
    peak_hr = df_merged.groupby(['household_id', 'hour'])['energy_kwh'].sum().reset_index()
    peak_hr = peak_hr.loc[peak_hr.groupby('household_id')['energy_kwh'].idxmax()]
    
    profile_df = pd.merge(profile_df, peak_hr[['household_id', 'hour']], on='household_id', how='left')
    profile_df = profile_df.rename(columns={'hour': 'peak_consumption_hour'})
    
    profile_df['potential_solar_savings_usd'] = np.where(~profile_df['has_solar'], profile_df['total_cost_usd'] * 0.3, 0)
    
    def get_priority(row):
        if not row['has_solar'] and row['avg_daily_kwh'] > 30: return 'High'
        elif not row['has_solar'] and row['avg_daily_kwh'] > 15: return 'Medium'
        return 'Low'
    profile_df['recommendation_priority'] = profile_df.apply(get_priority, axis=1)
    
    profile_df.to_csv(os.path.join(tableau_dir, 'household_profiles.csv'), index=False)

if __name__ == "__main__":
    main()
