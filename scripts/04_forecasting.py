import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os

def run_forecasting():
    print("Loading data for forecasting...")
    df = pd.read_csv('data/energy_consumption.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Aggregate to daily total consumption
    daily_data = df.groupby(df['timestamp'].dt.date)['energy_kwh'].sum().reset_index()
    daily_data['timestamp'] = pd.to_datetime(daily_data['timestamp'])
    daily_data = daily_data.set_index('timestamp')
    
    # We only have ~30 days of data. Let's use last 7 days as test set.
    train_size = len(daily_data) - 7
    train, test = daily_data.iloc[:train_size], daily_data.iloc[train_size:]
    
    print(f"Train size: {len(train)} days, Test size: {len(test)} days")
    
    # Simple Moving Average (3 days)
    sma_pred = train['energy_kwh'].rolling(window=3).mean().iloc[-1]
    test_pred_sma = [sma_pred] * len(test)
    
    # Exponential Smoothing
    model = ExponentialSmoothing(train['energy_kwh'], trend='add', seasonal=None)
    fit_model = model.fit()
    test_pred_es = fit_model.forecast(len(test))
    
    # Calculate metrics
    mae_es = mean_absolute_error(test['energy_kwh'], test_pred_es)
    rmse_es = np.sqrt(mean_squared_error(test['energy_kwh'], test_pred_es))
    
    print(f"Exponential Smoothing MAE: {mae_es:.2f}")
    print(f"Exponential Smoothing RMSE: {rmse_es:.2f}")
    
    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(train.index, train['energy_kwh'], label='Train Data')
    plt.plot(test.index, test['energy_kwh'], label='Test Data')
    plt.plot(test.index, test_pred_es, color='red', label='Exponential Smoothing Forecast')
    
    plt.title('Daily Energy Consumption Forecast vs Actual')
    plt.xlabel('Date')
    plt.ylabel('Total Energy (kWh)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('visualizations/forecast_comparison.png')
    plt.close()
    
    print("Forecasting completed. Visualizations saved.")

if __name__ == "__main__":
    run_forecasting()
