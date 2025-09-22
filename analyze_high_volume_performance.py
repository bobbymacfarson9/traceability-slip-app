import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history
from smart_bias_forecaster import HybridForecaster

def analyze_high_volume_performance():
    """Analyze forecasting performance specifically on high-volume weeks"""
    print("=== HIGH-VOLUME WEEK PERFORMANCE ANALYSIS ===")
    print("Focusing on weeks where forecasting accuracy matters most...")
    
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
    
    # Collect results
    all_results = []
    
    for week_info in test_weeks:
        week_file = week_info['week_file']
        week_num = week_info['week_num']
        year = week_info['year']
        
        test_file = Path(week_file)
        if not test_file.exists():
            continue
        
        print(f"\n📊 Analyzing {week_file}...")
        
        week_total_actual = 0
        week_total_forecast = 0
        day_results = []
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                continue
            
            day_actual = actual_data['boxes'].sum()
            week_total_actual += day_actual
            
            # Get forecast
            forecast_data = method.forecast_weekday(history_df, day, year, week_num)
            day_forecast = forecast_data['forecast_boxes'].sum()
            week_total_forecast += day_forecast
            
            # Calculate error
            day_error = abs(day_forecast - day_actual) / day_actual * 100 if day_actual > 0 else 0
            
            day_results.append({
                'week_file': week_file,
                'day': day,
                'actual': day_actual,
                'forecast': day_forecast,
                'error': day_error
            })
        
        # Week-level analysis
        week_error = abs(week_total_forecast - week_total_actual) / week_total_actual * 100 if week_total_actual > 0 else 0
        
        all_results.extend(day_results)
        
        print(f"   Week Total: {week_total_actual:.0f} boxes")
        print(f"   Week Forecast: {week_total_forecast:.0f} boxes")
        print(f"   Week Error: {week_error:.1f}%")
        
        # Categorize by volume
        if week_total_actual >= 2000:
            volume_category = "Very High (2000+)"
        elif week_total_actual >= 1500:
            volume_category = "High (1500-1999)"
        elif week_total_actual >= 1000:
            volume_category = "Medium (1000-1499)"
        else:
            volume_category = "Low (<1000)"
        
        print(f"   Volume Category: {volume_category}")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(all_results)
    
    if df.empty:
        print("❌ No data found for analysis")
        return
    
    # Volume analysis
    print(f"\n{'='*80}")
    print(f"HIGH-VOLUME PERFORMANCE ANALYSIS")
    print(f"{'='*80}")
    
    # Categorize by volume
    df['volume_category'] = pd.cut(df['actual'], 
                                  bins=[0, 500, 1000, 1500, 2000, np.inf], 
                                  labels=['Very Low (<500)', 'Low (500-999)', 'Medium (1000-1499)', 'High (1500-1999)', 'Very High (2000+)'])
    
    print(f"\n📦 PERFORMANCE BY VOLUME CATEGORY:")
    volume_analysis = df.groupby('volume_category').agg({
        'error': ['mean', 'std', 'count'],
        'actual': ['mean', 'sum'],
        'forecast': ['mean', 'sum']
    }).round(1)
    
    for category in volume_analysis.index:
        if pd.isna(category):
            continue
            
        mean_error = volume_analysis.loc[category, ('error', 'mean')]
        std_error = volume_analysis.loc[category, ('error', 'std')]
        count = volume_analysis.loc[category, ('error', 'count')]
        avg_actual = volume_analysis.loc[category, ('actual', 'mean')]
        total_actual = volume_analysis.loc[category, ('actual', 'sum')]
        
        print(f"   {category}:")
        print(f"     Error: {mean_error:.1f}% ± {std_error:.1f}%")
        print(f"     Tests: {count}")
        print(f"     Avg Daily: {avg_actual:.0f} boxes")
        print(f"     Total Volume: {total_actual:.0f} boxes")
        print()
    
    # Focus on high-volume days
    high_volume_days = df[df['actual'] >= 1000].copy()
    
    if not high_volume_days.empty:
        print(f"🎯 HIGH-VOLUME DAYS ANALYSIS (≥1000 boxes):")
        print(f"   Total high-volume days: {len(high_volume_days)}")
        print(f"   Average error: {high_volume_days['error'].mean():.1f}%")
        print(f"   Error std: {high_volume_days['error'].std():.1f}%")
        print(f"   Best day: {high_volume_days.loc[high_volume_days['error'].idxmin(), 'day']} ({high_volume_days['error'].min():.1f}% error)")
        print(f"   Worst day: {high_volume_days.loc[high_volume_days['error'].idxmax(), 'day']} ({high_volume_days['error'].max():.1f}% error)")
        
        # Show individual high-volume days
        print(f"\n   Individual high-volume days:")
        for _, row in high_volume_days.iterrows():
            print(f"     {row['week_file']} {row['day']}: {row['actual']:.0f} actual, {row['forecast']:.0f} forecast, {row['error']:.1f}% error")
    
    # Very high-volume days (≥2000 boxes)
    very_high_volume_days = df[df['actual'] >= 2000].copy()
    
    if not very_high_volume_days.empty:
        print(f"\n🚀 VERY HIGH-VOLUME DAYS ANALYSIS (≥2000 boxes):")
        print(f"   Total very high-volume days: {len(very_high_volume_days)}")
        print(f"   Average error: {very_high_volume_days['error'].mean():.1f}%")
        print(f"   Error std: {very_high_volume_days['error'].std():.1f}%")
        
        # Show individual very high-volume days
        print(f"\n   Individual very high-volume days:")
        for _, row in very_high_volume_days.iterrows():
            print(f"     {row['week_file']} {row['day']}: {row['actual']:.0f} actual, {row['forecast']:.0f} forecast, {row['error']:.1f}% error")
    
    # Day-of-week analysis for high-volume days
    print(f"\n📅 HIGH-VOLUME PERFORMANCE BY DAY OF WEEK:")
    high_volume_day_analysis = high_volume_days.groupby('day').agg({
        'error': ['mean', 'std', 'count'],
        'actual': 'mean'
    }).round(1)
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        if day in high_volume_day_analysis.index:
            mean_error = high_volume_day_analysis.loc[day, ('error', 'mean')]
            std_error = high_volume_day_analysis.loc[day, ('error', 'std')]
            count = high_volume_day_analysis.loc[day, ('error', 'count')]
            avg_actual = high_volume_day_analysis.loc[day, ('actual', 'mean')]
            
            print(f"   {day}: {mean_error:.1f}% ± {std_error:.1f}% ({count} tests, avg {avg_actual:.0f} boxes)")
    
    # Business impact analysis
    print(f"\n💼 BUSINESS IMPACT ANALYSIS:")
    
    # Calculate total volume and errors
    total_actual = df['actual'].sum()
    total_forecast = df['forecast'].sum()
    total_error_boxes = abs(df['forecast'] - df['actual']).sum()
    
    print(f"   Total actual boxes: {total_actual:.0f}")
    print(f"   Total forecast boxes: {total_forecast:.0f}")
    print(f"   Total error: {total_error_boxes:.0f} boxes")
    print(f"   Overall accuracy: {(1 - total_error_boxes/total_actual)*100:.1f}%")
    
    # High-volume specific accuracy
    if not high_volume_days.empty:
        high_volume_actual = high_volume_days['actual'].sum()
        high_volume_error = abs(high_volume_days['forecast'] - high_volume_days['actual']).sum()
        high_volume_accuracy = (1 - high_volume_error/high_volume_actual)*100
        
        print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
        print(f"   High-volume error: {high_volume_error:.0f} boxes")
        print(f"   High-volume actual: {high_volume_actual:.0f} boxes")
    
    return df

def create_high_volume_recommendations(df):
    """Create specific recommendations for high-volume forecasting"""
    print(f"\n{'='*80}")
    print(f"HIGH-VOLUME FORECASTING RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Analyze high-volume days
    high_volume_days = df[df['actual'] >= 1000].copy()
    
    if high_volume_days.empty:
        print("❌ No high-volume days found for analysis")
        return
    
    print(f"\n🎯 KEY FINDINGS:")
    
    # Overall high-volume performance
    high_volume_accuracy = (1 - abs(high_volume_days['forecast'] - high_volume_days['actual']).sum() / high_volume_days['actual'].sum()) * 100
    print(f"   • High-volume accuracy: {high_volume_accuracy:.1f}%")
    
    # Best and worst performing days
    best_day = high_volume_days.loc[high_volume_days['error'].idxmin()]
    worst_day = high_volume_days.loc[high_volume_days['error'].idxmax()]
    
    print(f"   • Best high-volume day: {best_day['day']} ({best_day['error']:.1f}% error)")
    print(f"   • Worst high-volume day: {worst_day['day']} ({worst_day['error']:.1f}% error)")
    
    # Day-of-week patterns
    day_errors = high_volume_days.groupby('day')['error'].mean()
    best_day_of_week = day_errors.idxmin()
    worst_day_of_week = day_errors.idxmax()
    
    print(f"   • Best day of week: {best_day_of_week} ({day_errors[best_day_of_week]:.1f}% avg error)")
    print(f"   • Worst day of week: {worst_day_of_week} ({day_errors[worst_day_of_week]:.1f}% avg error)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if high_volume_accuracy >= 85:
        print(f"   ✅ High-volume forecasting is EXCELLENT ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ✅ System is ready for production use")
        print(f"   ✅ Focus on maintaining current performance")
    elif high_volume_accuracy >= 80:
        print(f"   ✅ High-volume forecasting is GOOD ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ✅ System is ready for production use")
        print(f"   ⚠️  Consider minor improvements for worst-performing days")
    elif high_volume_accuracy >= 75:
        print(f"   ⚠️  High-volume forecasting is ACCEPTABLE ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ⚠️  Consider improvements before production deployment")
        print(f"   ⚠️  Focus on improving {worst_day_of_week} forecasting")
    else:
        print(f"   ❌ High-volume forecasting needs IMPROVEMENT ({high_volume_accuracy:.1f}% accuracy)")
        print(f"   ❌ Do not deploy to production yet")
        print(f"   ❌ Focus on improving forecasting algorithms")
    
    # Specific recommendations
    print(f"\n🔧 SPECIFIC IMPROVEMENTS:")
    
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
    df = analyze_high_volume_performance()
    if df is not None:
        high_volume_accuracy = create_high_volume_recommendations(df)
        
        print(f"\n{'='*80}")
        print(f"FINAL ASSESSMENT")
        print(f"{'='*80}")
        
        if high_volume_accuracy >= 80:
            print(f"🎉 SYSTEM READY FOR PRODUCTION!")
            print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
            print(f"   This is excellent for demand forecasting!")
        else:
            print(f"⚠️  SYSTEM NEEDS IMPROVEMENT")
            print(f"   High-volume accuracy: {high_volume_accuracy:.1f}%")
            print(f"   Focus on high-volume forecasting before deployment")
