import pandas as pd
import numpy as np
from pathlib import Path
from universal_daily_totals_parser import parse_daily_totals_universal
from egg_packing_predictor import forecast_weekday
import random

def extract_week_year(filename):
    """Extract week number and year from filename"""
    import re
    match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def universal_backtest():
    """Run backtest using the universal parser on multiple weeks"""
    print("=== UNIVERSAL PARSER BACKTEST ===")
    
    # Get all available files
    all_files = sorted(Path(".").glob("Week *Loading Slip*.xlsx"))
    available_weeks = []
    
    for file_path in all_files:
        week_num, year = extract_week_year(file_path.name)
        if week_num is not None and year is not None and year == 2025:
            available_weeks.append((week_num, year, file_path))
    
    print(f"Found {len(available_weeks)} weeks in 2025")
    
    # Select 3 random weeks for backtesting (excluding Week 24 which we already tested)
    test_weeks = [(w, y, f) for w, y, f in available_weeks if w != 24]
    if len(test_weeks) >= 3:
        selected_weeks = random.sample(test_weeks, 3)
    else:
        selected_weeks = test_weeks
    
    print(f"Testing weeks: {[w[0] for w in selected_weeks]}")
    
    results = []
    
    for week_num, year, file_path in selected_weeks:
        print(f"\n=== TESTING WEEK {week_num}, {year} ===")
        
        # Build historical data (exclude the test week)
        historical_data = []
        for hist_file in all_files:
            hist_week, hist_year = extract_week_year(hist_file.name)
            if (hist_week is None or hist_year is None or 
                hist_year > year or (hist_year == year and hist_week >= week_num)):
                continue
                
            try:
                for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
                    day_data = parse_daily_totals_universal(hist_file, day)
                    if not day_data.empty:
                        historical_data.append(day_data)
            except Exception as e:
                print(f"Error parsing {hist_file.name}: {e}")
        
        if not historical_data:
            print(f"No historical data for Week {week_num}")
            continue
        
        # Combine historical data
        history_df = pd.concat(historical_data, ignore_index=True)
        print(f"Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
        
        # Test each day of the week
        for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
            print(f"\n--- {day} ---")
            
            # Get actual data
            actual_data = parse_daily_totals_universal(file_path, day)
            if actual_data.empty:
                print(f"No actual data for {day}")
                continue
            
            # Generate forecast
            forecast = forecast_weekday(
                history_df, 
                day, 
                window=8, 
                alpha=0.7,
                target_week_num=week_num,
                target_year=year,
                use_last_year=True
            )
            
            if forecast.empty:
                print(f"No forecast generated for {day}")
                continue
            
            # Calculate accuracy
            total_forecast = forecast['forecast_boxes'].sum()
            total_actual = actual_data['boxes'].sum()
            
            if total_actual > 0:
                overall_error = abs(total_forecast - total_actual) / total_actual * 100
                accuracy = 100 - overall_error
            else:
                overall_error = 100 if total_forecast > 0 else 0
                accuracy = 0 if total_forecast > 0 else 100
            
            print(f"Forecast: {total_forecast:.0f} boxes")
            print(f"Actual: {total_actual:.0f} boxes")
            print(f"Accuracy: {accuracy:.1f}%")
            
            results.append({
                'week': week_num,
                'year': year,
                'day': day,
                'forecast': total_forecast,
                'actual': total_actual,
                'accuracy': accuracy,
                'error': overall_error
            })
    
    # Summary
    if results:
        print(f"\n=== BACKTEST SUMMARY ===")
        avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
        
        for result in results:
            print(f"Week {result['week']}, {result['day']}: {result['accuracy']:.1f}% accuracy")
        
        print(f"\nAverage accuracy: {avg_accuracy:.1f}%")
        
        if avg_accuracy < 80:
            print(f"\n⚠️  ACCURACY BELOW 80% THRESHOLD!")
            print(f"📋 Generating detailed Excel file for manual comparison...")
            
            # Generate detailed Excel file
            with pd.ExcelWriter('universal_backtest_detailed.xlsx', engine='openpyxl') as writer:
                for result in results:
                    week_num, year, day = result['week'], result['year'], result['day']
                    
                    # Get the actual data for this week/day
                    file_path = next(f for w, y, f in available_weeks if w == week_num and y == year)
                    actual_data = parse_daily_totals_universal(file_path, day)
                    
                    # Get the forecast (we'd need to regenerate this, but for now just show actuals)
                    sheet_name = f"Week{week_num}_{day}"
                    actual_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"📁 Excel file created: universal_backtest_detailed.xlsx")
        else:
            print(f"✅ ACCURACY ABOVE 80% THRESHOLD!")
    
    return results

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    universal_backtest()
