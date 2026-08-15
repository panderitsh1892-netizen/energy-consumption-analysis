#!/bin/bash
source venv/bin/activate
echo "Running EDA..."
python3 scripts/01_eda.py
echo "Running SQL Analysis..."
python3 scripts/02_sql_analysis.py
echo "Running Pattern Analysis..."
python3 scripts/03_pattern_analysis.py
echo "Running Forecasting..."
python3 scripts/04_forecasting.py
echo "Running Solar Recommendation..."
python3 scripts/05_solar_recommendation.py
echo "All done!"
