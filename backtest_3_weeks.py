import pandas as pd
import numpy as np
import random
from pathlib import Path
from fixed_daily_totals_parser import parse_daily_totals_only
from egg_packing_predictor import forecast_weekday, _last_n_weekday, _same_week_last_year

def extract_week_year(filename):
    """Extract week number and year from filename"""
    import re
    match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def backtest_week(week_num, year, day="Mon"):
    """Back test a specific week and day"""
    print(f"\n{'='*60}")
    print(f"BACKTESTING WEEK {week_num}, {year} - {day}")
    print(f"{'='*60}")
    
    # Find the target file
    target_file = Path(f"Week {week_num} Loading Slip {year}.xlsx")
    if not target_file.exists():
        print(f"❌ File not found: {target_file}")
        return None
    
    print(f"📁 Testing file: {target_file}")
    
    # Parse actual data
    print(f"\n📊 PARSING ACTUAL DATA...")
    actual_data = parse_daily_totals_only(target_file, day)
    
    if actual_data.empty:
        print(f"❌ No actual data found for Week {week_num}, {year} {day}")
        return None
    
    print(f"✅ Found {len(actual_data)} products in actual data:")
    for _, row in actual_data.iterrows():
        print(f"   {row['product']:<30} {row['boxes']:>6} boxes")
    
    total_actual = actual_data['boxes'].sum()
    print(f"\n📈 Total actual boxes: {total_actual}")
    
    # Build historical data (exclude the target week)
    print(f"\n📚 BUILDING HISTORICAL DATA...")
    all_files = sorted(Path(".").glob("Week *Loading Slip*.xlsx"))
    historical_data = []
    
    for file_path in all_files:
        file_week, file_year = extract_week_year(file_path.name)
        if file_week is None or file_year is None:
            continue
            
        # Exclude the target week from historical data
        if file_year == year and file_week == week_num:
            continue
            
        # Only use data from before the target week
        if file_year > year or (file_year == year and file_week >= week_num):
            continue
            
        try:
            for test_day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
                day_data = parse_daily_totals_only(file_path, test_day)
                if not day_data.empty:
                    historical_data.append(day_data)
        except Exception as e:
            print(f"⚠️  Error parsing {file_path.name}: {e}")
    
    if not historical_data:
        print("❌ No historical data found")
        return None
    
    # Combine historical data
    history_df = pd.concat(historical_data, ignore_index=True)
    print(f"✅ Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
    print(f"📅 Weeks covered: {history_df['week_num'].min()} to {history_df['week_num'].max()}")
    print(f"📅 Years: {sorted(history_df['year'].unique())}")
    
    # Generate forecast
    print(f"\n🔮 GENERATING FORECAST...")
    forecast = forecast_weekday(
        history_df, 
        day, 
        window=8, 
        alpha=0.7,
        target_week_num=week_num,
        target_year=year,
        use_last_year=True
    )
    
    print(f"✅ Generated forecast for {len(forecast)} products:")
    for _, row in forecast.iterrows():
        print(f"   {row['product']:<30} {row['forecast_boxes']:>6} boxes")
    
    total_forecast = forecast['forecast_boxes'].sum()
    print(f"\n📈 Total forecast boxes: {total_forecast}")
    
    # Calculate accuracy
    print(f"\n📊 ACCURACY ANALYSIS...")
    
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
    
    print(f"🎯 Total forecast: {total_forecast:.0f} boxes")
    print(f"🎯 Total actual: {total_actual:.0f} boxes")
    print(f"📉 Overall error: {overall_error:.1f}%")
    print(f"✅ Accuracy: {accuracy:.1f}%")
    
    # Show top errors
    print(f"\n🔍 TOP 5 LARGEST ERRORS:")
    comparison_sorted = comparison.sort_values('abs_error', ascending=False)
    
    for i, (_, row) in enumerate(comparison_sorted.head(5).iterrows()):
        if row['forecast_boxes'] > 0 or row['actual_boxes'] > 0:
            error_pct = row['pct_error'] if row['actual_boxes'] > 0 else "N/A"
            if isinstance(error_pct, (int, float)):
                error_str = f"{error_pct:.1f}%"
            else:
                error_str = str(error_pct)
            print(f"   {i+1}. {row['product']:<25} Forecast: {row['forecast_boxes']:>4}, Actual: {row['actual_boxes']:>4}, Error: {row['abs_error']:>4} ({error_str})")
    
    # Save detailed results
    output_file = f'week{week_num}_{year}_{day}_comparison.csv'
    comparison.to_csv(output_file, index=False)
    print(f"\n💾 Detailed comparison saved to: {output_file}")
    
    return {
        'week': week_num,
        'year': year,
        'day': day,
        'accuracy': accuracy,
        'total_forecast': total_forecast,
        'total_actual': total_actual,
        'overall_error': overall_error,
        'comparison': comparison
    }

def main():
    print("🚀 BACKTESTING 3 RANDOM 2025 WEEKS")
    print("="*60)
    
    # Find all available 2025 weeks
    all_files = sorted(Path(".").glob("Week *Loading Slip 2025.xlsx"))
    available_weeks = []
    
    for file_path in all_files:
        week_num, year = extract_week_year(file_path.name)
        if week_num is not None and year == 2025:
            available_weeks.append(week_num)
    
    if len(available_weeks) < 3:
        print(f"❌ Only found {len(available_weeks)} weeks in 2025. Need at least 3 for backtesting.")
        return
    
    # Select 3 random weeks (excluding the last few weeks to ensure we have historical data)
    testable_weeks = [w for w in available_weeks if w <= max(available_weeks) - 3]
    if len(testable_weeks) < 3:
        testable_weeks = available_weeks[:-2]  # Exclude last 2 weeks
    
    selected_weeks = random.sample(testable_weeks, min(3, len(testable_weeks)))
    selected_weeks.sort()
    
    print(f"📅 Available 2025 weeks: {sorted(available_weeks)}")
    print(f"🎲 Randomly selected weeks for testing: {selected_weeks}")
    
    results = []
    
    # Test each selected week
    for week_num in selected_weeks:
        result = backtest_week(week_num, 2025, "Mon")
        if result:
            results.append(result)
    
    # Summary
    if results:
        print(f"\n{'='*60}")
        print("📊 BACKTEST SUMMARY")
        print(f"{'='*60}")
        
        total_accuracy = 0
        for result in results:
            print(f"Week {result['week']}, 2025: {result['accuracy']:.1f}% accuracy")
            total_accuracy += result['accuracy']
        
        average_accuracy = total_accuracy / len(results)
        print(f"\n🎯 AVERAGE ACCURACY: {average_accuracy:.1f}%")
        
        if average_accuracy < 80:
            print(f"\n⚠️  ACCURACY BELOW 80% THRESHOLD!")
            print(f"📋 Generating Excel file for manual comparison...")
            
            # Create comprehensive Excel file
            with pd.ExcelWriter('backtest_detailed_comparison.xlsx', engine='openpyxl') as writer:
                for result in results:
                    sheet_name = f"Week{result['week']}_{result['year']}"
                    result['comparison'].to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"📁 Excel file created: backtest_detailed_comparison.xlsx")
            print(f"   - Contains detailed forecast vs actual comparisons for all 3 weeks")
            print(f"   - Each week on a separate sheet")
        else:
            print(f"\n✅ ACCURACY ABOVE 80% THRESHOLD - SYSTEM PERFORMING WELL!")
    
    else:
        print("❌ No successful backtests completed")

if __name__ == "__main__":
    main()
