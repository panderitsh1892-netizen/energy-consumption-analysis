import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os

def run_pattern_analysis():
    print("Loading data...")
    consumption_df = pd.read_csv('data/energy_consumption.csv')
    household_df = pd.read_csv('data/household_info.csv')
    
    df = pd.merge(consumption_df, household_df, on='household_id')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Solar vs Non-Solar Statistical Test (t-test)
    solar_users = df[df['has_solar_system'] == 1].groupby('household_id')['energy_kwh'].sum()
    nonsolar_users = df[df['has_solar_system'] == 0].groupby('household_id')['energy_kwh'].sum()
    
    t_stat, p_val = stats.ttest_ind(solar_users, nonsolar_users)
    print(f"\nT-test for Solar vs Non-Solar Total Consumption:")
    print(f"T-statistic: {t_stat:.4f}, p-value: {p_val:.4e}")
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x=['Solar', 'Non-Solar'], y=[solar_users.mean(), nonsolar_users.mean()])
    plt.title('Average Total Consumption: Solar vs Non-Solar')
    plt.ylabel('Total Energy (kWh)')
    plt.tight_layout()
    plt.savefig('visualizations/solar_vs_nonsolar.png')
    plt.close()
    
    # 2. Clustering Households by Consumption Patterns (K-Means)
    print("\nClustering households based on hourly consumption profiles...")
    df['hour'] = df['timestamp'].dt.hour
    hourly_profiles = pd.pivot_table(df, values='energy_kwh', index='household_id', columns='hour', aggfunc='mean').fillna(0)
    
    scaler = StandardScaler()
    scaled_profiles = scaler.fit_transform(hourly_profiles)
    
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(scaled_profiles)
    hourly_profiles['Cluster'] = clusters
    
    plt.figure(figsize=(12, 6))
    for i in range(3):
        cluster_data = hourly_profiles[hourly_profiles['Cluster'] == i].drop('Cluster', axis=1).mean()
        plt.plot(cluster_data.index, cluster_data.values, marker='o', label=f'Cluster {i}')
        
    plt.title('Household Clusters based on Hourly Consumption Profile')
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Energy (kWh)')
    plt.legend()
    plt.grid(True)
    plt.xticks(range(0, 24))
    plt.tight_layout()
    plt.savefig('visualizations/household_clusters.png')
    plt.close()
    
    print("Pattern analysis completed. Visualizations saved.")

if __name__ == "__main__":
    run_pattern_analysis()
