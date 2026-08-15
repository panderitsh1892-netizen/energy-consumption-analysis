import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def run_solar_recommendation():
    print("Loading data for solar recommendations...")
    consumption_df = pd.read_csv('data/energy_consumption.csv')
    household_df = pd.read_csv('data/household_info.csv')
    
    # Calculate total energy per household
    total_energy = consumption_df.groupby('household_id')['energy_kwh'].sum().reset_index()
    
    # Merge with household info
    df = pd.merge(total_energy, household_df, on='household_id')
    
    # Focus on households without solar
    target_households = df[df['has_solar_system'] == 0].copy()
    
    # Calculate potential savings (Assume $0.15 / kWh grid cost and solar offsets 40% of their usage)
    grid_rate = 0.15
    target_households['est_monthly_cost'] = target_households['energy_kwh'] * grid_rate
    target_households['potential_monthly_savings'] = target_households['est_monthly_cost'] * 0.40
    
    # Ranking criteria: high savings potential and high budget pressure
    target_households['budget_pressure'] = target_households['est_monthly_cost'] / target_households['monthly_energy_budget_usd']
    target_households['recommendation_score'] = (target_households['potential_monthly_savings'] * 0.7) + (target_households['budget_pressure'] * 30)
    
    # Give boost to Rural regions
    target_households.loc[target_households['region'] == 'Rural', 'recommendation_score'] *= 1.2
    
    # Rank recommendations
    recommendations = target_households.sort_values(by='recommendation_score', ascending=False)
    top_10 = recommendations.head(10)
    
    print("\nTop 10 Households Recommended for Solar Upgrade:")
    print(top_10[['household_id', 'region', 'energy_kwh', 'potential_monthly_savings', 'recommendation_score']])
    
    # Save recommendations
    recommendations.to_csv('outputs/solar_recommendations.csv', index=False)
    
    # Visualization: Potential savings distribution
    plt.figure(figsize=(10, 6))
    plt.hist(target_households['potential_monthly_savings'], bins=15, color='orange', edgecolor='black')
    plt.title('Distribution of Potential Monthly Savings from Solar')
    plt.xlabel('Potential Savings (USD)')
    plt.ylabel('Number of Households')
    plt.axvline(target_households['potential_monthly_savings'].mean(), color='red', linestyle='dashed', linewidth=1, label=f"Mean: ${target_households['potential_monthly_savings'].mean():.2f}")
    plt.legend()
    plt.tight_layout()
    plt.savefig('visualizations/solar_savings_potential.png')
    plt.close()
    
    print("Recommendations generated and saved to outputs/solar_recommendations.csv.")

if __name__ == "__main__":
    run_solar_recommendation()
