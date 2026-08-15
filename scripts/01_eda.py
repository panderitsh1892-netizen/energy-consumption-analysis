import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def run_eda():
    os.makedirs('visualizations', exist_ok=True)
    
    print("Loading data...")
    consumption_df = pd.read_csv('data/energy_consumption.csv')
    household_df = pd.read_csv('data/household_info.csv')
    
    # Merge datasets
    df = pd.merge(consumption_df, household_df, on='household_id')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Daily Consumption Trend
    daily_consumption = df.groupby(df['timestamp'].dt.date)['energy_kwh'].sum()
    plt.figure(figsize=(12, 6))
    daily_consumption.plot()
    plt.title('Total Daily Energy Consumption (All Households)')
    plt.xlabel('Date')
    plt.ylabel('Total Energy (kWh)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('visualizations/daily_consumption_trend.png')
    plt.close()
    
    # 2. Hourly Load Profile
    hourly_avg = df.groupby(df['timestamp'].dt.hour)['energy_kwh'].mean()
    plt.figure(figsize=(10, 6))
    hourly_avg.plot(kind='line', marker='o')
    plt.title('Average Hourly Load Profile')
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Energy (kWh)')
    plt.grid(True)
    plt.xticks(range(0, 24))
    plt.tight_layout()
    plt.savefig('visualizations/hourly_load_profile.png')
    plt.close()
    
    # 3. Consumption Heatmap (Hour vs Day of Week)
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour
    heatmap_data = pd.pivot_table(df, values='energy_kwh', index='day_of_week', columns='hour', aggfunc='mean')
    
    # Reorder days
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(days)
    
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=False)
    plt.title('Average Energy Consumption: Hour vs Day of Week')
    plt.tight_layout()
    plt.savefig('visualizations/consumption_heatmap.png')
    plt.close()
    
    # 4. Consumption by Region (Box Plot)
    daily_hh_consumption = df.groupby(['household_id', 'region', df['timestamp'].dt.date])['energy_kwh'].sum().reset_index()
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='region', y='energy_kwh', data=daily_hh_consumption)
    plt.title('Daily Consumption Distribution by Region')
    plt.ylabel('Daily Energy (kWh)')
    plt.tight_layout()
    plt.savefig('visualizations/consumption_by_region.png')
    plt.close()
    
    # 5. Appliance Category Consumption
    appliance_consumption = df.groupby('appliance_category')['energy_kwh'].sum().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    appliance_consumption.plot(kind='bar', color='teal')
    plt.title('Total Energy Consumption by Appliance Category')
    plt.ylabel('Total Energy (kWh)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('visualizations/consumption_by_appliance.png')
    plt.close()
    
    print("EDA Visualizations generated in visualizations/ folder.")

if __name__ == "__main__":
    run_eda()
