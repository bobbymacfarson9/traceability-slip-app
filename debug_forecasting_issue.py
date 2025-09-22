import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def debug_forecasting_issue():
    """Debug why all forecasting methods are only finding 8 products"""
    print("=== DEBUGGING FORECASTING ISSUE ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test on Week 39, 2024 Monday
    test_file = Path("Week 39 Loading Slip 2024.xlsx")
    day = "Mon"
    target_year = 2024
    target_week = 39
    
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
    
    # Sort by date
    day_data = day_data.sort_values(['year', 'week_num'])
    
    # Filter out data after target week
    day_data = day_data[
        (day_data['year'] < target_year) | 
        ((day_data['year'] == target_year) & (day_data['week_num'] < target_week))
    ]
    
    print(f"Historical data before Week {target_week}, {target_year}: {len(day_data)} records")
    
    # Show recent weeks
    recent_data = day_data.tail(8)
    print(f"\nLast 8 weeks of data:")
    for _, row in recent_data.iterrows():
        print(f"  Week {row['week_num']}, {row['year']}: {row['product']} - {row['boxes']} boxes")
    
    # Check unique products
    unique_products = day_data['product'].unique()
    print(f"\nUnique products in historical data: {len(unique_products)}")
    for product in sorted(unique_products):
        product_data = day_data[day_data['product'] == product]
        print(f"  {product}: {len(product_data)} records, avg: {product_data['boxes'].mean():.1f}")
    
    # Check if products from actual data exist in historical data
    print(f"\nProduct overlap analysis:")
    actual_products = set(actual_data['product'].unique())
    historical_products = set(day_data['product'].unique())
    
    missing_products = actual_products - historical_products
    if missing_products:
        print(f"  Products in actual but NOT in historical: {missing_products}")
    
    extra_products = historical_products - actual_products
    if extra_products:
        print(f"  Products in historical but NOT in actual: {extra_products}")
    
    common_products = actual_products & historical_products
    print(f"  Common products: {len(common_products)}")
    
    # Test simple forecasting on common products
    print(f"\nSimple forecasting test:")
    forecasts = []
    for product in common_products:
        product_data = day_data[day_data['product'] == product]
        if len(product_data) > 0:
            recent_product_data = product_data.tail(8)
            forecast = recent_product_data['boxes'].mean()
            actual = actual_data[actual_data['product'] == product]['boxes'].iloc[0] if product in actual_products else 0
            forecasts.append({
                'product': product,
                'forecast': forecast,
                'actual': actual,
                'error': abs(forecast - actual) / actual * 100 if actual > 0 else 0
            })
    
    for forecast in forecasts:
        print(f"  {forecast['product']}: Forecast {forecast['forecast']:.1f}, Actual {forecast['actual']}, Error {forecast['error']:.1f}%")
    
    total_forecast = sum([f['forecast'] for f in forecasts])
    total_actual = actual_data['boxes'].sum()
    total_error = abs(total_forecast - total_actual) / total_actual * 100
    
    print(f"\nTotal forecast: {total_forecast:.1f} boxes")
    print(f"Total actual: {total_actual} boxes")
    print(f"Total error: {total_error:.1f}%")

if __name__ == "__main__":
    debug_forecasting_issue()
