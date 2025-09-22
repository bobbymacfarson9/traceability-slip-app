import pandas as pd
import numpy as np
from pathlib import Path
from fixed_daily_totals_parser import parse_daily_totals_only
from egg_packing_predictor import forecast_weekday, _last_n_weekday, _same_week_last_year

def test_week32_accuracy():
    print("=== TESTING WEEK 32, 2025 ACCURACY ===\n")
    
    # First, let's see what data we have available
    test_file = Path("Week 32 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Week 32, 2025 file not found: {test_file}")
        print("Available files:")
        for f in Path(".").glob("Week *Loading Slip*.xlsx"):
            print(f"  {f.name}")
        return
    
    print(f"Testing file: {test_file}")
    
    # Parse the actual data for Week 32, 2025 Monday
    print("\n=== ACTUAL DATA FOR WEEK 32, 2025 MONDAY ===")
    actual_data = parse_daily_totals_only(test_file, "Mon")
    
    if actual_data.empty:
        print("No actual data found for Week 32, 2025 Monday")
        return
    
    print(f"Found {len(actual_data)} products in actual data:")
    for _, row in actual_data.iterrows():
        print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
    
    total_actual = actual_data['boxes'].sum()
    print(f"\nTotal actual boxes: {total_actual}")
    
    # Now let's build historical data from all previous weeks
    print("\n=== BUILDING HISTORICAL DATA ===")
    all_files = sorted(Path(".").glob("Week *Loading Slip*.xlsx"))
    historical_data = []
    
    for file_path in all_files:
        week_num, year = extract_week_year(file_path.name)
        if week_num is None or year is None:
            continue
            
        # Only use data from before Week 32, 2025
        if year > 2025 or (year == 2025 and week_num >= 32):
            continue
            
        try:
            for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
                day_data = parse_daily_totals_only(file_path, day)
                if not day_data.empty:
                    historical_data.append(day_data)
        except Exception as e:
            print(f"Error parsing {file_path.name}: {e}")
    
    if not historical_data:
        print("No historical data found")
        return
    
    # Combine all historical data
    history_df = pd.concat(historical_data, ignore_index=True)
    print(f"Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
    print(f"Weeks covered: {history_df['week_num'].min()} to {history_df['week_num'].max()}")
    print(f"Years: {sorted(history_df['year'].unique())}")
    
    # Generate forecast for Week 32, 2025 Monday
    print("\n=== GENERATING FORECAST ===")
    forecast = forecast_weekday(
        history_df, 
        "Mon", 
        window=8, 
        alpha=0.7,
        target_week_num=32,
        target_year=2025,
        use_last_year=True
    )
    
    print(f"Generated forecast for {len(forecast)} products:")
    for _, row in forecast.iterrows():
        print(f"  {row['product']:<30} {row['forecast_boxes']:>6} boxes")
    
    total_forecast = forecast['forecast_boxes'].sum()
    print(f"\nTotal forecast boxes: {total_forecast}")
    
    # Compare forecast vs actuals
    print("\n=== ACCURACY COMPARISON ===")
    
    # Merge forecast and actuals
    comparison = forecast.merge(actual_data, on='product', how='outer')
    comparison = comparison.fillna(0)
    comparison = comparison.rename(columns={'boxes': 'actual_boxes'})
    
    # Calculate errors
    comparison['abs_error'] = abs(comparison['forecast_boxes'] - comparison['actual_boxes'])
    comparison['pct_error'] = np.where(
        comparison['actual_boxes'] > 0,
        comparison['abs_error'] / comparison['actual_boxes'] * 100,
        np.where(comparison['forecast_boxes'] > 0, 100, 0)
    )
    
    # Overall accuracy
    overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
    accuracy = 100 - overall_error
    
    print(f"Total forecast: {total_forecast:.0f} boxes")
    print(f"Total actual: {total_actual:.0f} boxes")
    print(f"Overall error: {overall_error:.1f}%")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Show detailed comparison
    print(f"\n=== DETAILED PRODUCT COMPARISON ===")
    comparison_sorted = comparison.sort_values('abs_error', ascending=False)
    
    for _, row in comparison_sorted.iterrows():
        if row['forecast_boxes'] > 0 or row['actual_boxes'] > 0:
            error_pct = row['pct_error'] if row['actual_boxes'] > 0 else "N/A"
            if isinstance(error_pct, (int, float)):
                error_str = f"{error_pct:.1f}%"
            else:
                error_str = str(error_pct)
            print(f"  {row['product']:<30} Forecast: {row['forecast_boxes']:>4}, Actual: {row['actual_boxes']:>4}, Error: {row['abs_error']:>4} ({error_str})")
    
    # Save detailed results
    comparison.to_csv('week32_forecast_comparison.csv', index=False)
    print(f"\nDetailed comparison saved to: week32_forecast_comparison.csv")

def extract_week_year(filename):
    """Extract week number and year from filename"""
    import re
    match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

if __name__ == "__main__":
    test_week32_accuracy()
