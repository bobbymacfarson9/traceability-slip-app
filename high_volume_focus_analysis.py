import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history
from smart_bias_forecaster import HybridForecaster

def analyze_high_volume_focus():
    """Analyze forecasting performance specifically on high-volume days"""
    print("=== HIGH-VOLUME DAY FOCUS ANALYSIS ===")
    print("Focusing on days where forecasting accuracy matters most...")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test weeks (same as our study)
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Initialize method
    method = HybridForecaster()
    
    # Collect all day results
    all_day_results = []
    
    for week_info in test_weeks:
        week_file = week_info['week_file']
        week_num = week_info['week_num']
        year = week_info['year']
        
        test_file = Path(week_file)
        if not test_file.exists():
            continue
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                continue
            
            day_actual = actual_data['boxes'].sum()
            
            # Get forecast
            forecast_data = method.forecast_weekday(history_df, day, year, week_num)
            day_forecast = forecast_data['forecast_boxes'].sum()
            
            # Calculate error
            day_error = abs(day_forecast - day_actual) / day_actual * 100 if day_actual > 0 else 0
            
            all_day_results.append({
                'week_file': week_file,
                'day': day,
                'actual': day_actual,
                'forecast': day_forecast,
                'error': day_error
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(all_day_results)
    
    if df.empty:
        print("❌ No data found for analysis")
        return
    
    print(f"\n📊 OVERALL PERFORMANCE:")
    print(f"   Total days analyzed: {len(df)}")
    print(f"   Average error: {df['error'].mean():.1f}%")
    print(f"   Median error: {df['error'].median():.1f}%")
    print(f"   Error std: {df['error'].std():.1f}%")
    
    # Focus on high-volume days (≥1000 boxes)
    high_volume_days = df[df['actual'] >= 1000].copy()
    
    print(f"\n🎯 HIGH-VOLUME DAYS ANALYSIS (≥1000 boxes):")
    print(f"   High-volume days: {len(high_volume_days)} out of {len(df)} total days")
    print(f"   Percentage: {len(high_volume_days)/len(df)*100:.1f}% of all days")
    
    if not high_volume_days.empty:
        high_volume_accuracy = (1 - abs(high_volume_days['forecast'] - high_volume_days['actual']).sum() / high_volume_days['actual'].sum()) * 100
        
        print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
        print(f"   High-volume error: {abs(high_volume_days['forecast'] - high_volume_days['actual']).sum():.0f} boxes")
        print(f"   High-volume actual: {high_volume_days['actual'].sum():.0f} boxes")
        print(f"   High-volume forecast: {high_volume_days['forecast'].sum():.0f} boxes")
        
        # Show individual high-volume days
        print(f"\n   Individual high-volume days:")
        for _, row in high_volume_days.iterrows():
            print(f"     {row['week_file']} {row['day']}: {row['actual']:.0f} actual, {row['forecast']:.0f} forecast, {row['error']:.1f}% error")
        
        # Day-of-week analysis for high-volume days
        print(f"\n   High-volume performance by day of week:")
        day_analysis = high_volume_days.groupby('day').agg({
            'error': ['mean', 'count'],
            'actual': 'mean'
        }).round(1)
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            if day in day_analysis.index:
                mean_error = day_analysis.loc[day, ('error', 'mean')]
                count = day_analysis.loc[day, ('error', 'count')]
                avg_actual = day_analysis.loc[day, ('actual', 'mean')]
                print(f"     {day}: {mean_error:.1f}% error ({count} tests, avg {avg_actual:.0f} boxes)")
    
    # Very high-volume days (≥2000 boxes)
    very_high_volume_days = df[df['actual'] >= 2000].copy()
    
    if not very_high_volume_days.empty:
        print(f"\n🚀 VERY HIGH-VOLUME DAYS ANALYSIS (≥2000 boxes):")
        print(f"   Very high-volume days: {len(very_high_volume_days)}")
        
        very_high_accuracy = (1 - abs(very_high_volume_days['forecast'] - very_high_volume_days['actual']).sum() / very_high_volume_days['actual'].sum()) * 100
        
        print(f"   Very high-volume accuracy: {very_high_accuracy:.1f}%")
        print(f"   Very high-volume error: {abs(very_high_volume_days['forecast'] - very_high_volume_days['actual']).sum():.0f} boxes")
        print(f"   Very high-volume actual: {very_high_volume_days['actual'].sum():.0f} boxes")
        
        # Show individual very high-volume days
        print(f"\n   Individual very high-volume days:")
        for _, row in very_high_volume_days.iterrows():
            print(f"     {row['week_file']} {row['day']}: {row['actual']:.0f} actual, {row['forecast']:.0f} forecast, {row['error']:.1f}% error")
    
    # Business impact analysis
    print(f"\n💼 BUSINESS IMPACT ANALYSIS:")
    
    # Calculate total volume and errors
    total_actual = df['actual'].sum()
    total_forecast = df['forecast'].sum()
    total_error_boxes = abs(df['forecast'] - df['actual']).sum()
    overall_accuracy = (1 - total_error_boxes/total_actual)*100
    
    print(f"   Total actual boxes: {total_actual:.0f}")
    print(f"   Total forecast boxes: {total_forecast:.0f}")
    print(f"   Total error: {total_error_boxes:.0f} boxes")
    print(f"   Overall accuracy: {overall_accuracy:.1f}%")
    
    # High-volume specific accuracy
    if not high_volume_days.empty:
        high_volume_actual = high_volume_days['actual'].sum()
        high_volume_error = abs(high_volume_days['forecast'] - high_volume_days['actual']).sum()
        high_volume_accuracy = (1 - high_volume_error/high_volume_actual)*100
        
        print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
        print(f"   High-volume error: {high_volume_error:.0f} boxes")
        print(f"   High-volume actual: {high_volume_actual:.0f} boxes")
        print(f"   High-volume % of total: {high_volume_actual/total_actual*100:.1f}%")
    
    return df, high_volume_days

def create_high_volume_recommendations(df, high_volume_days):
    """Create specific recommendations for high-volume forecasting"""
    print(f"\n{'='*80}")
    print(f"HIGH-VOLUME FORECASTING RECOMMENDATIONS")
    print(f"{'='*80}")
    
    if high_volume_days.empty:
        print("❌ No high-volume days found for analysis")
        return None
    
    # Analyze high-volume days
    high_volume_accuracy = (1 - abs(high_volume_days['forecast'] - high_volume_days['actual']).sum() / high_volume_days['actual'].sum()) * 100
    
    print(f"\n🎯 KEY FINDINGS:")
    print(f"   • High-volume accuracy: {high_volume_accuracy:.1f}%")
    print(f"   • High-volume days: {len(high_volume_days)} out of {len(df)} total days")
    print(f"   • High-volume % of total volume: {high_volume_days['actual'].sum()/df['actual'].sum()*100:.1f}%")
    
    # Best and worst performing high-volume days
    best_day = high_volume_days.loc[high_volume_days['error'].idxmin()]
    worst_day = high_volume_days.loc[high_volume_days['error'].idxmax()]
    
    print(f"   • Best high-volume day: {best_day['day']} ({best_day['error']:.1f}% error)")
    print(f"   • Worst high-volume day: {worst_day['day']} ({worst_day['error']:.1f}% error)")
    
    # Day-of-week patterns for high-volume days
    day_errors = high_volume_days.groupby('day')['error'].mean()
    if not day_errors.empty:
        best_day_of_week = day_errors.idxmin()
        worst_day_of_week = day_errors.idxmax()
        
        print(f"   • Best day of week: {best_day_of_week} ({day_errors[best_day_of_week]:.1f}% avg error)")
        print(f"   • Worst day of week: {worst_day_of_week} ({day_errors[worst_day_of_week]:.1f}% avg error)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if high_volume_accuracy >= 90:
        print(f"   🎉 EXCELLENT! High-volume forecasting is outstanding ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ✅ System is ready for production use")
        print(f"   ✅ This level of accuracy is exceptional for demand forecasting")
    elif high_volume_accuracy >= 85:
        print(f"   ✅ EXCELLENT! High-volume forecasting is very good ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ✅ System is ready for production use")
        print(f"   ✅ This is excellent performance for demand forecasting")
    elif high_volume_accuracy >= 80:
        print(f"   ✅ GOOD! High-volume forecasting is good ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ✅ System is ready for production use")
        print(f"   ⚠️  Consider minor improvements for worst-performing days")
    elif high_volume_accuracy >= 75:
        print(f"   ⚠️  ACCEPTABLE! High-volume forecasting is acceptable ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ⚠️  Consider improvements before production deployment")
        print(f"   ⚠️  Focus on improving worst-performing days")
    else:
        print(f"   ❌ NEEDS IMPROVEMENT! High-volume forecasting needs work ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ❌ Do not deploy to production yet")
        print(f"   ❌ Focus on improving forecasting algorithms")
    
    # Specific recommendations
    print(f"\n🔧 SPECIFIC IMPROVEMENTS:")
    
    if not day_errors.empty:
        worst_day_of_week = day_errors.idxmax()
        if worst_day_of_week == 'Wed':
            print(f"   • Wednesday forecasting needs attention")
            print(f"   • Consider day-specific adjustments")
        elif worst_day_of_week == 'Fri':
            print(f"   • Friday forecasting needs attention")
            print(f"   • Consider end-of-week patterns")
    
    # Volume-specific recommendations
    very_high_days = df[df['actual'] >= 2000]
    if not very_high_days.empty:
        very_high_accuracy = (1 - abs(very_high_days['forecast'] - very_high_days['actual']).sum() / very_high_days['actual'].sum()) * 100
        print(f"   • Very high-volume days (≥2000 boxes): {very_high_accuracy:.1f}% accuracy")
        
        if very_high_accuracy < 80:
            print(f"   • Consider special handling for very high-volume days")
            print(f"   • Use longer historical windows for high-volume forecasting")
    
    return high_volume_accuracy

if __name__ == "__main__":
    df, high_volume_days = analyze_high_volume_focus()
    if df is not None:
        high_volume_accuracy = create_high_volume_recommendations(df, high_volume_days)
        
        print(f"\n{'='*80}")
        print(f"FINAL ASSESSMENT")
        print(f"{'='*80}")
        
        if high_volume_accuracy is not None:
            if high_volume_accuracy >= 80:
                print(f"🎉 SYSTEM READY FOR PRODUCTION!")
                print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
                print(f"   This is excellent for demand forecasting!")
                print(f"   You can confidently use this system when you're low on eggs!")
            else:
                print(f"⚠️  SYSTEM NEEDS IMPROVEMENT")
                print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
                print(f"   Focus on high-volume forecasting before deployment")
        else:
            print(f"❌ No high-volume days found for analysis")
            print(f"   All test days had low volume")
            print(f"   Need more high-volume test data")
