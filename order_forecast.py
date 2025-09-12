#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def generate_synthetic_orders():
    """Generate synthetic order data from 2025-01-01 to 2025-09-12"""
    
    # Create date range
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 9, 12)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    np.random.seed(42)  # For reproducible results
    
    orders_data = []
    
    for date in dates:
        # Base order count (growing trend over time)
        days_since_start = (date - start_date).days
        base_orders = 50 + (days_since_start * 0.3)  # Growing trend
        
        # Weekly seasonality (higher on weekends)
        weekday = date.weekday()
        if weekday in [5, 6]:  # Saturday, Sunday
            weekend_multiplier = 1.4
        elif weekday in [4]:  # Friday
            weekend_multiplier = 1.2
        else:
            weekend_multiplier = 1.0
        
        # Monthly seasonality (slightly higher at month beginning/end)
        day_of_month = date.day
        if day_of_month <= 5 or day_of_month >= 25:
            monthly_multiplier = 1.1
        else:
            monthly_multiplier = 1.0
        
        # Holiday effects (simulate special occasions)
        holiday_multiplier = 1.0
        if date.month == 2 and date.day == 14:  # Valentine's Day
            holiday_multiplier = 1.8
        elif date.month == 3 and date.day in range(15, 22):  # Spring break period
            holiday_multiplier = 1.3
        elif date.month == 7 and date.day == 4:  # Independence Day
            holiday_multiplier = 1.6
        elif date.month == 8 and date.day in range(1, 15):  # Summer vacation
            holiday_multiplier = 1.2
        
        # Random noise
        noise = np.random.normal(0, 8)
        
        # Calculate final order count
        orders = max(0, int(base_orders * weekend_multiplier * monthly_multiplier * holiday_multiplier + noise))
        
        orders_data.append({
            'ds': date,
            'y': orders
        })
    
    return pd.DataFrame(orders_data)

def create_forecast_plot(df, forecast, periods=30):
    """Create a comprehensive forecast plot"""
    
    plt.figure(figsize=(15, 10))
    
    # Main forecast plot
    plt.subplot(2, 2, 1)
    plt.plot(df['ds'], df['y'], 'ko', markersize=3, label='Historical Orders', alpha=0.7)
    plt.plot(forecast['ds'], forecast['yhat'], 'b-', label='Forecast', linewidth=2)
    plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], 
                     alpha=0.3, color='blue', label='Confidence Interval')
    
    # Highlight forecast period
    forecast_start = df['ds'].max() + timedelta(days=1)
    future_forecast = forecast[forecast['ds'] >= forecast_start]
    plt.plot(future_forecast['ds'], future_forecast['yhat'], 'r-', 
             label='Future Forecast', linewidth=3)
    plt.fill_between(future_forecast['ds'], future_forecast['yhat_lower'], 
                     future_forecast['yhat_upper'], alpha=0.5, color='red')
    
    plt.axvline(x=forecast_start, color='red', linestyle='--', alpha=0.7, 
                label='Forecast Start')
    plt.title('Order Forecasting with Prophet Model', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Number of Orders')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # Weekly seasonality
    plt.subplot(2, 2, 2)
    weekly_component = forecast.set_index('ds')['weekly'].resample('D').mean()
    weekly_avg = weekly_component.groupby(weekly_component.index.dayofweek).mean()
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    plt.bar(days, weekly_avg.values, color='skyblue', alpha=0.7)
    plt.title('Weekly Seasonality Pattern', fontsize=12, fontweight='bold')
    plt.ylabel('Effect on Orders')
    plt.grid(True, alpha=0.3)
    
    # Trend component
    plt.subplot(2, 2, 3)
    plt.plot(forecast['ds'], forecast['trend'], 'g-', linewidth=2)
    plt.title('Overall Trend', fontsize=12, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Trend Component')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # Recent vs Future comparison
    plt.subplot(2, 2, 4)
    recent_data = df.tail(30)
    future_data = future_forecast.head(30)
    
    plt.plot(range(len(recent_data)), recent_data['y'], 'bo-', 
             label='Last 30 Days (Actual)', markersize=4)
    plt.plot(range(len(recent_data), len(recent_data) + len(future_data)), 
             future_data['yhat'], 'ro-', label='Next 30 Days (Forecast)', markersize=4)
    plt.fill_between(range(len(recent_data), len(recent_data) + len(future_data)),
                     future_data['yhat_lower'], future_data['yhat_upper'],
                     alpha=0.3, color='red')
    
    plt.axvline(x=len(recent_data)-1, color='red', linestyle='--', alpha=0.7)
    plt.title('Recent vs Future Orders', fontsize=12, fontweight='bold')
    plt.xlabel('Days')
    plt.ylabel('Number of Orders')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return future_data

def print_forecast_summary(df, future_forecast):
    """Print summary statistics of the forecast"""
    
    print("=" * 60)
    print("ORDER FORECASTING SUMMARY")
    print("=" * 60)
    
    # Historical data summary
    print(f"Historical Period: {df['ds'].min().strftime('%Y-%m-%d')} to {df['ds'].max().strftime('%Y-%m-%d')}")
    print(f"Total Historical Days: {len(df)}")
    print(f"Average Daily Orders (Historical): {df['y'].mean():.1f}")
    print(f"Historical Range: {df['y'].min()} - {df['y'].max()} orders")
    
    print("\n" + "-" * 40)
    
    # Forecast summary
    print(f"Forecast Period: {future_forecast['ds'].min().strftime('%Y-%m-%d')} to {future_forecast['ds'].max().strftime('%Y-%m-%d')}")
    print(f"Average Predicted Daily Orders: {future_forecast['yhat'].mean():.1f}")
    print(f"Predicted Range: {future_forecast['yhat'].min():.1f} - {future_forecast['yhat'].max():.1f} orders")
    
    # Weekly insights
    future_forecast['weekday'] = future_forecast['ds'].dt.day_name()
    weekly_avg = future_forecast.groupby('weekday')['yhat'].mean().sort_values(ascending=False)
    
    print(f"\nExpected busiest days:")
    for day, avg in weekly_avg.head(3).items():
        print(f"  {day}: {avg:.1f} orders")
    
    # Growth projection
    historical_avg = df['y'].mean()
    forecast_avg = future_forecast['yhat'].mean()
    growth_rate = ((forecast_avg - historical_avg) / historical_avg) * 100
    
    print(f"\nProjected Growth: {growth_rate:+.1f}% compared to historical average")
    
    print("=" * 60)

def main():
    print("Generating synthetic order data...")
    
    # Generate synthetic data
    df = generate_synthetic_orders()
    
    print(f"Generated {len(df)} days of order data from {df['ds'].min().strftime('%Y-%m-%d')} to {df['ds'].max().strftime('%Y-%m-%d')}")
    
    # Create and fit Prophet model
    print("Training Prophet model...")
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        interval_width=0.95
    )
    
    model.fit(df)
    
    # Create future dataframe for 30 days
    future = model.make_future_dataframe(periods=30)
    
    # Make predictions
    print("Generating forecast...")
    forecast = model.predict(future)
    
    # Create plots
    print("Creating forecast visualization...")
    future_forecast = create_forecast_plot(df, forecast)
    
    # Print summary
    print_forecast_summary(df, future_forecast)
    
    # Save results
    forecast_results = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(30)
    forecast_results.to_csv('order_forecast_results.csv', index=False)
    print(f"\nForecast results saved to 'order_forecast_results.csv'")

if __name__ == "__main__":
    main()