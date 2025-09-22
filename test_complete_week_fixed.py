import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history

def test_complete_week_fixed():
    """Test the complete week with fixed parser"""
    print("=== TESTING COMPLETE WEEK WITH FIXED PARSER ===")
    
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    # Build historical data
    print("\n=== BUILDING HISTORICAL DATASET ===")
    history_df = load_all_history(".")
    print(f"Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
    
    # Process each day
    daily_summaries = []
    
    for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
        print(f"\n=== PROCESSING {day.upper()} ===")
        
        # 1. Parse actual data
        actual_data = parse_daily_totals_universal(test_file, day)
        
        if actual_data.empty:
            print(f"No actual data found for {day}")
            daily_summaries.append({
                'Day': day,
                'Total_Forecast': 0,
                'Total_Actual': 0,
                'Overall_Error_%': 0,
                'Accuracy_%': 0,
                'Products_Forecast': 0,
                'Products_Actual': 0,
                'Perfect_Matches': 0,
                'High_Error_Products': 0
            })
            continue
        
        print(f"Found {len(actual_data)} products in actual data:")
        for _, row in actual_data.iterrows():
            print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
        
        total_actual = actual_data['boxes'].sum()
        print(f"Total actual boxes: {total_actual}")
        
        # 2. Generate forecast
        forecast = forecast_weekday(
            history_df, 
            day, 
            window=8, 
            alpha=0.7,
            target_week_num=24,
            target_year=2025,
            use_last_year=True,
            conservative_mode=True
        )
        
        print(f"Generated forecast for {len(forecast)} products:")
        for _, row in forecast.iterrows():
            print(f"  {row['product']:<30} {row['forecast_boxes']:>6} boxes")
        
        total_forecast = forecast['forecast_boxes'].sum()
        print(f"Total forecast boxes: {total_forecast}")
        
        # 3. Create comparison
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
        
        # Calculate overall accuracy for this day
        overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
        accuracy = 100 - overall_error
        
        print(f"Day accuracy: {accuracy:.1f}%")
        
        # Store daily summary
        daily_summaries.append({
            'Day': day,
            'Total_Forecast': total_forecast,
            'Total_Actual': total_actual,
            'Overall_Error_%': overall_error,
            'Accuracy_%': accuracy,
            'Products_Forecast': len(forecast),
            'Products_Actual': len(actual_data),
            'Perfect_Matches': len(comparison[comparison['abs_error'] == 0]),
            'High_Error_Products': len(comparison[comparison['pct_error'] > 50])
        })
    
    # Print overall summary
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS WITH FIXED PARSER")
    print(f"{'='*60}")
    
    total_forecast_all = sum([s['Total_Forecast'] for s in daily_summaries])
    total_actual_all = sum([s['Total_Actual'] for s in daily_summaries])
    overall_weekly_error = abs(total_forecast_all - total_actual_all) / total_actual_all * 100 if total_actual_all > 0 else 0
    
    print(f"📊 WEEKLY SUMMARY:")
    print(f"   Total Forecast (All Days): {total_forecast_all:.0f} boxes")
    print(f"   Total Actual (All Days): {total_actual_all:.0f} boxes")
    print(f"   Overall Weekly Error: {overall_weekly_error:.1f}%")
    print(f"   Overall Weekly Accuracy: {100 - overall_weekly_error:.1f}%")
    
    print(f"\n📋 DAILY BREAKDOWN:")
    for summary in daily_summaries:
        print(f"   {summary['Day']}: {summary['Accuracy_%']:.1f}% accuracy ({summary['Total_Forecast']:.0f} vs {summary['Total_Actual']:.0f} boxes) - {summary['Products_Actual']} products")
    
    # Calculate average accuracy (excluding days with no data)
    valid_days = [s for s in daily_summaries if s['Total_Actual'] > 0]
    if valid_days:
        avg_accuracy = sum([s['Accuracy_%'] for s in valid_days]) / len(valid_days)
        print(f"\n🎯 AVERAGE ACCURACY: {avg_accuracy:.1f}%")
        
        if avg_accuracy >= 80:
            print("✅ EXCELLENT! Parser is working very well!")
        elif avg_accuracy >= 70:
            print("✅ GOOD! Parser is working well with room for improvement")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Parser accuracy below 70%")
    
    return daily_summaries

if __name__ == "__main__":
    test_complete_week_fixed()
