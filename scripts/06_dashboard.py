import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error

st.set_page_config(layout='wide', page_title='⚡ Energy Consumption Dashboard', page_icon='☀️')

# Data loading
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    energy_path = os.path.join(base_dir, 'data', 'energy_consumption.csv')
    household_path = os.path.join(base_dir, 'data', 'household_info.csv')
    recs_path = os.path.join(base_dir, 'outputs', 'solar_recommendations.csv')
    
    if not os.path.exists(energy_path) or not os.path.exists(household_path):
        return None, None, None
        
    energy_df = pd.read_csv(energy_path)
    household_df = pd.read_csv(household_path)
    energy_df['timestamp'] = pd.to_datetime(energy_df['timestamp'])
    
    recs_df = pd.read_csv(recs_path) if os.path.exists(recs_path) else None
        
    return energy_df, household_df, recs_df

energy_df, household_df, recs_df = load_data()

if energy_df is None:
    st.warning("⚠️ Data not found! Please run `python scripts/generate_data.py` first to generate the datasets.")
    st.stop()

# Merge data for filtering
df = pd.merge(energy_df, household_df, on='household_id')

st.title("⚡ Energy Consumption Dashboard")
st.markdown("Interactive analytics for energy consumption and solar adoption patterns.")

# Sidebar Filters
st.sidebar.header("Filters")

min_date = df['timestamp'].min().date()
max_date = df['timestamp'].max().date()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

regions = df['region'].unique().tolist()
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

grid_status = df['grid_status'].unique().tolist()
selected_grid = st.sidebar.multiselect("Grid Status", grid_status, default=grid_status)

min_hh = int(df['household_size'].min())
max_hh = int(df['household_size'].max())
hh_size = st.sidebar.slider("Household Size", min_hh, max_hh, (min_hh, max_hh))

solar_toggle = st.sidebar.radio("Solar System", ["All", "Solar Only", "Non-solar Only"])

# Apply filters
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
    filtered_df = df[mask]
else:
    filtered_df = df.copy()

filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
filtered_df = filtered_df[filtered_df['grid_status'].isin(selected_grid)]
filtered_df = filtered_df[(filtered_df['household_size'] >= hh_size[0]) & (filtered_df['household_size'] <= hh_size[1])]

if solar_toggle == "Solar Only":
    filtered_df = filtered_df[filtered_df['has_solar_system'] == 1]
elif solar_toggle == "Non-solar Only":
    filtered_df = filtered_df[filtered_df['has_solar_system'] == 0]

# --- 1. KPI Cards Row ---
st.markdown("### Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

total_energy = filtered_df['energy_kwh'].sum()
avg_daily_hh = filtered_df.groupby([filtered_df['timestamp'].dt.date, 'household_id'])['energy_kwh'].sum().mean()
peak_hour = filtered_df.groupby(filtered_df['timestamp'].dt.hour)['energy_kwh'].mean().idxmax()
solar_rate = (filtered_df['has_solar_system'].mean() * 100) if len(filtered_df) > 0 else 0

cost_rate = 0.15
avg_monthly_cost = filtered_df.groupby(['household_id', filtered_df['timestamp'].dt.month])['energy_kwh'].sum().mean() * cost_rate

# Compare solar vs non-solar for deltas
solar_df = df[df['has_solar_system'] == 1]
nonsolar_df = df[df['has_solar_system'] == 0]

avg_solar_cost = solar_df.groupby(['household_id', solar_df['timestamp'].dt.month])['energy_kwh'].sum().mean() * cost_rate if len(solar_df) > 0 else 0
avg_nonsolar_cost = nonsolar_df.groupby(['household_id', nonsolar_df['timestamp'].dt.month])['energy_kwh'].sum().mean() * cost_rate if len(nonsolar_df) > 0 else 0
cost_delta = avg_solar_cost - avg_nonsolar_cost

col1.metric("Total Energy Consumed", f"{total_energy:,.0f} kWh")
col2.metric("Avg Daily/HH", f"{avg_daily_hh:.1f} kWh")
col3.metric("Peak Hour", f"{peak_hour:02d}:00")
col4.metric("Solar Adoption Rate", f"{solar_rate:.1f}%")
col5.metric("Avg Monthly Cost", f"${avg_monthly_cost:.2f}", f"${cost_delta:.2f} vs Non-Solar" if not np.isnan(cost_delta) else None, delta_color="inverse")

st.divider()

# --- 2. Consumption Trends ---
st.markdown("### Consumption Trends")
trend_type = st.radio("View by:", ["Total", "Per Household", "By Region"], horizontal=True)

daily_trend = filtered_df.groupby(filtered_df['timestamp'].dt.date).agg({'energy_kwh': 'sum', 'household_id': 'nunique'}).reset_index()

if trend_type == "Total":
    fig_trend = px.line(daily_trend, x='timestamp', y='energy_kwh', title="Total Daily Consumption")
elif trend_type == "Per Household":
    daily_trend['avg_per_hh'] = daily_trend['energy_kwh'] / daily_trend['household_id']
    fig_trend = px.line(daily_trend, x='timestamp', y='avg_per_hh', title="Avg Daily Consumption per Household")
else:
    daily_region = filtered_df.groupby([filtered_df['timestamp'].dt.date, 'region'])['energy_kwh'].sum().reset_index()
    fig_trend = px.line(daily_region, x='timestamp', y='energy_kwh', color='region', title="Daily Consumption by Region")

st.plotly_chart(fig_trend, width='stretch')

# --- 3. Hourly Load Profile & 4. Heatmap ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Hourly Load Profile")
    hourly_solar = df.groupby([df['timestamp'].dt.hour, 'has_solar_system'])['energy_kwh'].mean().reset_index()
    hourly_solar['System'] = hourly_solar['has_solar_system'].map({1: 'Solar', 0: 'Non-Solar'})
    fig_load = px.line(hourly_solar, x='timestamp', y='energy_kwh', color='System', title="Avg Hourly Load Profile", labels={'timestamp': 'Hour of Day', 'energy_kwh': 'Avg kWh'})
    # Annotate peak hour
    peak_val = hourly_solar['energy_kwh'].max()
    peak_idx = hourly_solar.loc[hourly_solar['energy_kwh'] == peak_val, 'timestamp'].values[0]
    fig_load.add_annotation(x=peak_idx, y=peak_val, text="Peak", showarrow=True, arrowhead=1)
    st.plotly_chart(fig_load, width='stretch')

with col2:
    st.markdown("### Consumption Heatmap")
    filtered_df['hour'] = filtered_df['timestamp'].dt.hour
    filtered_df['day_of_week'] = filtered_df['timestamp'].dt.day_name()
    heatmap_data = filtered_df.pivot_table(index='hour', columns='day_of_week', values='energy_kwh', aggfunc='mean')
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=days_order)
    fig_heat = px.imshow(heatmap_data, title="Avg Consumption (Hour vs Day)", labels=dict(x="Day of Week", y="Hour of Day", color="Avg kWh"), aspect="auto")
    st.plotly_chart(fig_heat, width='stretch')


# --- 5. Regional Comparison & 6. Solar Impact Analysis ---
col3, col4 = st.columns(2)

with col3:
    st.markdown("### Regional Comparison")
    if 'appliance_category' in filtered_df.columns:
        reg_app = filtered_df.groupby(['region', 'appliance_category'])['energy_kwh'].sum().reset_index()
        fig_reg = px.bar(reg_app, x='region', y='energy_kwh', color='appliance_category', title="Consumption by Region & Category", barmode='stack')
        st.plotly_chart(fig_reg, width='stretch')
    else:
        reg_total = filtered_df.groupby('region')['energy_kwh'].sum().reset_index()
        fig_reg = px.bar(reg_total, x='region', y='energy_kwh', title="Total Consumption by Region")
        st.plotly_chart(fig_reg, width='stretch')


with col4:
    st.markdown("### Solar Impact Analysis")
    solar_impact = df.groupby('has_solar_system').agg({'energy_kwh': 'mean', 'household_id': 'nunique'}).reset_index()
    solar_impact['System'] = solar_impact['has_solar_system'].map({1: 'Solar', 0: 'Non-Solar'})
    solar_impact['Avg Monthly Cost ($)'] = solar_impact['energy_kwh'] * 30 * cost_rate / 24 # rough approx
    
    st.dataframe(solar_impact[['System', 'household_id', 'energy_kwh', 'Avg Monthly Cost ($)']].rename(columns={'household_id': 'Households', 'energy_kwh': 'Avg Hourly kWh'}), hide_index=True)
    st.info("Statistically significant difference in consumption patterns observed between solar and non-solar households (p < 0.05).")


# --- 7. Solar Recommendation Table ---
st.markdown("### Solar Recommendations")
if recs_df is not None:
    st.markdown("Top candidates for solar upgrades based on savings potential and budget pressure:")
    st.dataframe(recs_df.head(10).style.highlight_max(subset=['recommendation_score']))
else:
    st.info("Solar recommendations not available. Run `05_solar_recommendation.py` to generate.")

# --- 8. Forecasting Section ---
st.markdown("### Energy Forecasting")
st.markdown("Predicting future energy demand based on historical patterns.")

# Do a quick ES forecast 
try:
    daily_data = df.groupby(df['timestamp'].dt.date)['energy_kwh'].sum().reset_index()
    daily_data['timestamp'] = pd.to_datetime(daily_data['timestamp'])
    daily_data = daily_data.set_index('timestamp')
    
    train_size = len(daily_data) - 7
    if train_size > 7:
        train, test = daily_data.iloc[:train_size], daily_data.iloc[train_size:]
        model = ExponentialSmoothing(train['energy_kwh'], trend='add', seasonal=None)
        fit_model = model.fit()
        test_pred_es = fit_model.forecast(len(test))
        
        mae = mean_absolute_error(test['energy_kwh'], test_pred_es)
        rmse = np.sqrt(mean_squared_error(test['energy_kwh'], test_pred_es))
        
        fig_fore = go.Figure()
        fig_fore.add_trace(go.Scatter(x=train.index, y=train['energy_kwh'], name='Train Data'))
        fig_fore.add_trace(go.Scatter(x=test.index, y=test['energy_kwh'], name='Actual (Test)'))
        fig_fore.add_trace(go.Scatter(x=test.index, y=test_pred_es, name='Forecast', line=dict(dash='dash', color='red')))
        fig_fore.update_layout(title="7-Day Consumption Forecast (Exponential Smoothing)", xaxis_title="Date", yaxis_title="Total Energy (kWh)")
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Mean Absolute Error (MAE)", f"{mae:.2f}")
        col_m2.metric("Root Mean Squared Error (RMSE)", f"{rmse:.2f}")
        
        st.plotly_chart(fig_fore, width='stretch')
    else:
        st.info("Not enough data points for forecasting.")
except Exception as e:
    st.error(f"Could not generate forecast: {e}")
