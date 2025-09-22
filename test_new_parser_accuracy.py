import pandas as pd
import numpy as np
from pathlib import Path
from egg_loading_slip_parser import parse_folder
from egg_packing_predictor import forecast_weekday, _last_n_weekday, _same_week_last_year

def test_new_parser_accuracy():
    print("=== TESTING NEW PARSER FORECASTING ACCURACY ===\n")
    
    # Load new parsed data
    new_data = parse_folder()
    print(f"New parser loaded {len(new_data)} total records")
    
    # Convert to the format expected by the forecasting functions
    # We'll use DAILY_TOTALS section and rename columns to match old format
    forecast_data = new_data[new_data['section'] == 'DAILY_TOTALS'].copy()
    forecast_data = forecast_data.rename(columns={'qty': 'boxes'})
    
    # Add week_num and year columns (extract from filename)
    def extract_week_year(filename):
        import re
        match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None
    
    forecast_data['week_num'] = forecast_data['file'].apply(lambda x: extract_week_year(x)[0])
    forecast_data['year'] = forecast_data['file'].apply(lambda x: extract_week_year(x)[1])
    
    # Remove rows without valid week/year
    forecast_data = forecast_data.dropna(subset=['week_num', 'year'])
    
    print(f"Forecast-ready data: {len(forecast_data)} records")
    print(f"Weeks covered: {forecast_data['week_num'].min()} to {forecast_data['week_num'].max()}")
    print(f"Years: {sorted(forecast_data['year'].unique())}")
    
    # Test forecasting for a recent week (Week 24, 2025)
    test_week = 24
    test_year = 2025
    test_day = 'Mon'
    
    print(f"\n=== FORECASTING TEST: Week {test_week}, {test_year}, {test_day} ===")
    
    # Generate forecast
    forecast = forecast_weekday(
        forecast_data, 
        test_day, 
        window=8, 
        alpha=0.7,
        target_week_num=test_week,
        target_year=test_year,
        use_last_year=True
    )
    
    print(f"Forecast generated: {len(forecast)} products")
    print("\nTop 10 forecasted products:")
    for _, row in forecast.head(10).iterrows():
        print(f"  {row['product']:<25} {row['forecast_boxes']:>6}")
    
    # Get actuals for comparison
    actuals = forecast_data[
        (forecast_data['day'] == test_day) & 
        (forecast_data['week_num'] == test_week) & 
        (forecast_data['year'] == test_year)
    ].copy()
    
    if not actuals.empty:
        actuals = actuals.groupby('product')['boxes'].sum().reset_index()
        actuals = actuals.rename(columns={'boxes': 'actual_boxes'})
        
        print(f"\nActuals found: {len(actuals)} products")
        print("\nTop 10 actual products:")
        for _, row in actuals.head(10).iterrows():
            print(f"  {row['product']:<25} {row['actual_boxes']:>6}")
        
        # Compare forecast vs actuals
        comparison = forecast.merge(actuals, on='product', how='outer')
        comparison = comparison.fillna(0)
        
        # Calculate accuracy metrics
        comparison['abs_error'] = abs(comparison['forecast_boxes'] - comparison['actual_boxes'])
        comparison['pct_error'] = np.where(
            comparison['actual_boxes'] > 0,
            comparison['abs_error'] / comparison['actual_boxes'] * 100,
            np.where(comparison['forecast_boxes'] > 0, 100, 0)
        )
        
        # Overall accuracy
        total_forecast = comparison['forecast_boxes'].sum()
        total_actual = comparison['actual_boxes'].sum()
        overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
        
        print(f"\n=== ACCURACY RESULTS ===")
        print(f"Total forecast: {total_forecast:.0f} boxes")
        print(f"Total actual: {total_actual:.0f} boxes")
        print(f"Overall error: {overall_error:.1f}%")
        print(f"Accuracy: {100 - overall_error:.1f}%")
        
        # Show products with largest errors
        comparison['error_rank'] = comparison['abs_error'].rank(ascending=False)
        large_errors = comparison[comparison['error_rank'] <= 5].sort_values('abs_error', ascending=False)
        
        print(f"\nTop 5 largest errors:")
        for _, row in large_errors.iterrows():
            print(f"  {row['product']:<25} Forecast: {row['forecast_boxes']:>4}, Actual: {row['actual_boxes']:>4}, Error: {row['abs_error']:>4}")
        
    else:
        print(f"\nNo actuals found for Week {test_week}, {test_year}, {test_day}")
        print("Available weeks for this day:")
        available = forecast_data[forecast_data['day'] == test_day][['week_num', 'year']].drop_duplicates().sort_values(['year', 'week_num'])
        for _, row in available.tail(10).iterrows():
            print(f"  Week {row['week_num']}, {row['year']}")

if __name__ == "__main__":
    test_new_parser_accuracy()
