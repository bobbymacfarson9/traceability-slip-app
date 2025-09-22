import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def deep_debug_forecasting():
    """Deep debug of the forecasting issue"""
    print("=== DEEP DEBUG OF FORECASTING ISSUE ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test on Week 45, 2024 Monday
    test_file = Path("Week 45 Loading Slip 2024.xlsx")
    day = "Mon"
    target_year = 2024
    target_week = 45
    
    print(f"Testing: {test_file.name} - {day}")
    
    # Get actual data
    actual_data = parse_daily_totals_universal(test_file, day)
    print(f"\nActual data: {len(actual_data)} products, {actual_data['boxes'].sum()} total boxes")
    print("Actual products:")
    for _, row in actual_data.iterrows():
        print(f"  {row['product']}: {row['boxes']} boxes")
    
    # Get historical data for this day
    day_data = history_df[history_df['day'] == day].copy()
    print(f"\nHistorical data for {day}: {len(day_data)} records")
    
    # Show all historical data for this day
    print(f"\nAll historical data for {day}:")
    for _, row in day_data.iterrows():
        print(f"  Week {row['week_num']}, {row['year']}: {row['product']} - {row['boxes']} boxes")
    
    # Sort by date
    day_data = day_data.sort_values(['year', 'week_num'])
    
    # Filter out data after target week
    day_data = day_data[
        (day_data['year'] < target_year) | 
        ((day_data['year'] == target_year) & (day_data['week_num'] < target_week))
    ]
    
    print(f"\nHistorical data before Week {target_week}, {target_year}: {len(day_data)} records")
    
    # Show filtered data
    print(f"\nFiltered historical data:")
    for _, row in day_data.iterrows():
        print(f"  Week {row['week_num']}, {row['year']}: {row['product']} - {row['boxes']} boxes")
    
    # Get last 6 weeks
    recent_data = day_data.tail(6)
    print(f"\nLast 6 weeks of data:")
    for _, row in recent_data.iterrows():
        print(f"  Week {row['week_num']}, {row['year']}: {row['product']} - {row['boxes']} boxes")
    
    # Check unique products in recent data
    unique_products = recent_data['product'].unique()
    print(f"\nUnique products in recent data: {len(unique_products)}")
    for product in sorted(unique_products):
        product_data = recent_data[recent_data['product'] == product]
        print(f"  {product}: {len(product_data)} records, avg: {product_data['boxes'].mean():.1f}")
    
    # Test simple forecasting
    print(f"\nSimple forecasting test:")
    forecasts = recent_data.groupby('product')['boxes'].mean().round().astype(int).reset_index()
    forecasts = forecasts.rename(columns={'boxes': 'forecast_boxes'})
    
    print(f"Forecast results:")
    for _, row in forecasts.iterrows():
        print(f"  {row['product']}: {row['forecast_boxes']} boxes")
    
    total_forecast = forecasts['forecast_boxes'].sum()
    total_actual = actual_data['boxes'].sum()
    total_error = abs(total_forecast - total_actual) / total_actual * 100
    
    print(f"\nTotal forecast: {total_forecast} boxes")
    print(f"Total actual: {total_actual} boxes")
    print(f"Total error: {total_error:.1f}%")
    
    # Check if we're missing products that should be forecasted
    print(f"\nProduct coverage analysis:")
    actual_products = set(actual_data['product'].unique())
    forecast_products = set(forecasts['product'].unique())
    
    missing_products = actual_products - forecast_products
    if missing_products:
        print(f"  Products in actual but NOT in forecast: {missing_products}")
        
        # Check if these products exist in historical data at all
        for product in missing_products:
            product_historical = day_data[day_data['product'] == product]
            if len(product_historical) > 0:
                print(f"    {product}: Found in historical data ({len(product_historical)} records)")
            else:
                print(f"    {product}: NOT found in historical data")
    
    extra_products = forecast_products - actual_products
    if extra_products:
        print(f"  Products in forecast but NOT in actual: {extra_products}")

if __name__ == "__main__":
    deep_debug_forecasting()
