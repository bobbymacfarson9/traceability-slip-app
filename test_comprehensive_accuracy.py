import pandas as pd
import numpy as np
from pathlib import Path
from comprehensive_egg_parser import parse_folder_comprehensive
from egg_packing_predictor import forecast_weekday, _last_n_weekday, _same_week_last_year

def test_comprehensive_accuracy():
    print("=== TESTING COMPREHENSIVE PARSER FORECASTING ACCURACY ===\n")
    
    # Load comprehensive parsed data
    comprehensive_data = parse_folder_comprehensive()
    print(f"Comprehensive parser loaded {len(comprehensive_data)} total records")
    
    # Convert to the format expected by the forecasting functions
    # We'll use all sections and rename columns to match old format
    forecast_data = comprehensive_data.copy()
    forecast_data = forecast_data.rename(columns={'qty': 'boxes'})
    
    print(f"Forecast-ready data: {len(forecast_data)} records")
    print(f"Weeks covered: {forecast_data['week_num'].min()} to {forecast_data['week_num'].max()}")
    print(f"Years: {sorted(forecast_data['year'].unique())}")
    print(f"Unique products: {forecast_data['product'].nunique()}")
    
    # Test forecasting for Week 24, 2025 Monday
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
    print("\nTop 15 forecasted products:")
    for _, row in forecast.head(15).iterrows():
        print(f"  {row['product']:<30} {row['forecast_boxes']:>6}")
    
    # Get actuals for comparison
    actuals = forecast_data[
        (forecast_data['day'] == test_day) & 
        (forecast_data['week_num'] == test_week) & 
        (forecast_data['year'] == test_year)
    ].copy()
    
    if not actuals.empty:
        # Group by product and sum quantities
        actuals = actuals.groupby('product')['boxes'].sum().reset_index()
        actuals = actuals.rename(columns={'boxes': 'actual_boxes'})
        
        print(f"\nActuals found: {len(actuals)} products")
        print("\nTop 15 actual products:")
        for _, row in actuals.head(15).iterrows():
            print(f"  {row['product']:<30} {row['actual_boxes']:>6}")
        
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
        large_errors = comparison[comparison['error_rank'] <= 10].sort_values('abs_error', ascending=False)
        
        print(f"\nTop 10 largest errors:")
        for _, row in large_errors.iterrows():
            print(f"  {row['product']:<30} Forecast: {row['forecast_boxes']:>4}, Actual: {row['actual_boxes']:>4}, Error: {row['abs_error']:>4}")
        
        # Save detailed comparison
        comparison.to_csv('comprehensive_forecast_comparison.csv', index=False)
        print(f"\nDetailed comparison saved to: comprehensive_forecast_comparison.csv")
        
    else:
        print(f"\nNo actuals found for Week {test_week}, {test_year}, {test_day}")
        print("Available weeks for this day:")
        available = forecast_data[forecast_data['day'] == test_day][['week_num', 'year']].drop_duplicates().sort_values(['year', 'week_num'])
        for _, row in available.tail(10).iterrows():
            print(f"  Week {row['week_num']}, {row['year']}")

if __name__ == "__main__":
    test_comprehensive_accuracy()
