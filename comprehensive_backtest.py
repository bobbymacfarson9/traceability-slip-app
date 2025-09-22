import pandas as pd
import numpy as np
from pathlib import Path
import random
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history
from enhanced_forecaster_with_outliers import EnhancedForecasterWithOutliers

def comprehensive_backtest():
    """Comprehensive backtest on multiple random weeks to evaluate the enhanced forecaster"""
    print("=== COMPREHENSIVE BACKTEST: ENHANCED FORECASTER ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Get all available weeks
    available_weeks = history_df.groupby(['year', 'week_num']).size().reset_index()
    available_weeks = available_weeks[available_weeks[0] >= 5]  # At least 5 records per week
    
    print(f"Found {len(available_weeks)} weeks with sufficient data")
    
    # Create enhanced forecaster
    enhanced_forecaster = EnhancedForecasterWithOutliers(history_df)
    
    # Test on multiple random weeks (excluding the ones we already tested)
    excluded_weeks = [(2025, 24), (2025, 32)]  # Already tested these
    test_weeks = available_weeks[
        ~available_weeks.apply(lambda row: (row['year'], row['week_num']) in excluded_weeks, axis=1)
    ].sample(n=min(5, len(available_weeks)), random_state=42)
    
    print(f"Testing on {len(test_weeks)} random weeks:")
    for _, row in test_weeks.iterrows():
        print(f"  Week {row['week_num']}, {row['year']}")
    
    results = []
    
    for _, week_info in test_weeks.iterrows():
        year = week_info['year']
        week_num = week_info['week_num']
        
        # Find the corresponding file
        week_files = list(Path(".").glob(f"Week {week_num} Loading Slip {year}.xlsx"))
        if not week_files:
            print(f"File not found for Week {week_num}, {year}")
            continue
        
        week_file = week_files[0]
        
        print(f"\n{'='*60}")
        print(f"TESTING WEEK {week_num}, {year}")
        print(f"File: {week_file.name}")
        print(f"{'='*60}")
        
        week_results = {
            'week_file': week_file.name,
            'week_num': week_num,
            'year': year,
            'original_errors': [],
            'enhanced_errors': [],
            'daily_comparison': [],
            'outlier_days_detected': [],
            'legitimate_holiday': False
        }
        
        # Check if this is a legitimate holiday
        if (year, week_num) in enhanced_forecaster.legitimate_holidays:
            week_results['legitimate_holiday'] = True
            print(f"📅 This is a legitimate holiday week")
        
        for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
            print(f"\n--- {day.upper()} ---")
            
            # Get actual data
            actual_data = parse_daily_totals_universal(week_file, day)
            if actual_data.empty:
                print(f"No actual data for {day}")
                continue
            
            total_actual = actual_data['boxes'].sum()
            print(f"Actual: {total_actual} boxes ({len(actual_data)} products)")
            
            # Check if this day is detected as an outlier
            is_outlier = (year, week_num, day) in enhanced_forecaster.outlier_days
            if is_outlier:
                week_results['outlier_days_detected'].append(day)
                print(f"🚫 This day is detected as an outlier")
            
            # Original forecast
            original_forecast = forecast_weekday(
                history_df, 
                day, 
                window=8, 
                alpha=0.7,
                target_week_num=week_num,
                target_year=year,
                use_last_year=True,
                conservative_mode=True
            )
            
            original_total = original_forecast['forecast_boxes'].sum()
            original_error = abs(original_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Original Forecast: {original_total} boxes ({len(original_forecast)} products) - Error: {original_error:.1f}%")
            
            # Enhanced forecast
            enhanced_forecast = enhanced_forecaster.forecast_weekday(day, year, week_num)
            enhanced_total = enhanced_forecast['forecast_boxes'].sum()
            enhanced_error = abs(enhanced_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Enhanced Forecast: {enhanced_total} boxes ({len(enhanced_forecast)} products) - Error: {enhanced_error:.1f}%")
            
            # Calculate improvement
            improvement = original_error - enhanced_error
            improvement_pct = (improvement / original_error * 100) if original_error > 0 else 0
            
            print(f"Improvement: {improvement:.1f} percentage points ({improvement_pct:.1f}% better)")
            
            # Store results
            week_results['original_errors'].append(original_error)
            week_results['enhanced_errors'].append(enhanced_error)
            week_results['daily_comparison'].append({
                'day': day,
                'actual': total_actual,
                'original_forecast': original_total,
                'original_error': original_error,
                'enhanced_forecast': enhanced_total,
                'enhanced_error': enhanced_error,
                'improvement': improvement,
                'improvement_pct': improvement_pct,
                'is_outlier': is_outlier
            })
        
        # Calculate weekly averages
        if week_results['original_errors']:
            avg_original_error = sum(week_results['original_errors']) / len(week_results['original_errors'])
            avg_enhanced_error = sum(week_results['enhanced_errors']) / len(week_results['enhanced_errors'])
            avg_improvement = avg_original_error - avg_enhanced_error
            
            print(f"\n📊 WEEKLY SUMMARY:")
            print(f"   Average Original Error: {avg_original_error:.1f}%")
            print(f"   Average Enhanced Error: {avg_enhanced_error:.1f}%")
            print(f"   Average Improvement: {avg_improvement:.1f} percentage points")
            if week_results['outlier_days_detected']:
                print(f"   Outlier Days Detected: {', '.join(week_results['outlier_days_detected'])}")
            
            week_results['avg_original_error'] = avg_original_error
            week_results['avg_enhanced_error'] = avg_enhanced_error
            week_results['avg_improvement'] = avg_improvement
        
        results.append(week_results)
    
    # Overall analysis
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE BACKTEST RESULTS")
    print(f"{'='*70}")
    
    all_original_errors = []
    all_enhanced_errors = []
    outlier_weeks = []
    holiday_weeks = []
    
    for result in results:
        all_original_errors.extend(result['original_errors'])
        all_enhanced_errors.extend(result['enhanced_errors'])
        
        if result['outlier_days_detected']:
            outlier_weeks.append(result)
        if result['legitimate_holiday']:
            holiday_weeks.append(result)
    
    if all_original_errors and all_enhanced_errors:
        overall_original_error = sum(all_original_errors) / len(all_original_errors)
        overall_enhanced_error = sum(all_enhanced_errors) / len(all_enhanced_errors)
        overall_improvement = overall_original_error - overall_enhanced_error
        
        print(f"Overall Average Original Error: {overall_original_error:.1f}%")
        print(f"Overall Average Enhanced Error: {overall_enhanced_error:.1f}%")
        print(f"Overall Average Improvement: {overall_improvement:.1f} percentage points")
        
        improvement_pct = (overall_improvement / overall_original_error * 100) if overall_original_error > 0 else 0
        print(f"Overall Improvement: {improvement_pct:.1f}% better")
        
        print(f"\n📊 BREAKDOWN BY WEEK TYPE:")
        print(f"   Total weeks tested: {len(results)}")
        print(f"   Weeks with outlier days: {len(outlier_weeks)}")
        print(f"   Legitimate holiday weeks: {len(holiday_weeks)}")
        print(f"   Normal weeks: {len(results) - len(outlier_weeks) - len(holiday_weeks)}")
        
        # Analyze by week type
        if outlier_weeks:
            print(f"\n🚫 OUTLIER WEEKS ANALYSIS:")
            outlier_original_errors = []
            outlier_enhanced_errors = []
            for week in outlier_weeks:
                outlier_original_errors.extend(week['original_errors'])
                outlier_enhanced_errors.extend(week['enhanced_errors'])
            
            if outlier_original_errors:
                avg_outlier_original = sum(outlier_original_errors) / len(outlier_original_errors)
                avg_outlier_enhanced = sum(outlier_enhanced_errors) / len(outlier_enhanced_errors)
                print(f"   Average Original Error: {avg_outlier_original:.1f}%")
                print(f"   Average Enhanced Error: {avg_outlier_enhanced:.1f}%")
                print(f"   Improvement: {avg_outlier_original - avg_outlier_enhanced:.1f}pp")
        
        if holiday_weeks:
            print(f"\n📅 HOLIDAY WEEKS ANALYSIS:")
            holiday_original_errors = []
            holiday_enhanced_errors = []
            for week in holiday_weeks:
                holiday_original_errors.extend(week['original_errors'])
                holiday_enhanced_errors.extend(week['enhanced_errors'])
            
            if holiday_original_errors:
                avg_holiday_original = sum(holiday_original_errors) / len(holiday_original_errors)
                avg_holiday_enhanced = sum(holiday_enhanced_errors) / len(holiday_enhanced_errors)
                print(f"   Average Original Error: {avg_holiday_original:.1f}%")
                print(f"   Average Enhanced Error: {avg_holiday_enhanced:.1f}%")
                print(f"   Improvement: {avg_holiday_original - avg_holiday_enhanced:.1f}pp")
        
        # Show best and worst improvements
        print(f"\n🎯 BEST IMPROVEMENTS:")
        all_improvements = []
        for result in results:
            for day_result in result['daily_comparison']:
                all_improvements.append({
                    'week': f"Week {result['week_num']}, {result['year']}",
                    'day': day_result['day'],
                    'improvement': day_result['improvement'],
                    'improvement_pct': day_result['improvement_pct'],
                    'is_outlier': day_result['is_outlier']
                })
        
        all_improvements.sort(key=lambda x: x['improvement'], reverse=True)
        for improvement in all_improvements[:5]:  # Top 5
            outlier_flag = " (OUTLIER)" if improvement['is_outlier'] else ""
            print(f"   {improvement['week']} {improvement['day']}: {improvement['improvement']:.1f}pp improvement ({improvement['improvement_pct']:.1f}% better){outlier_flag}")
        
        print(f"\n⚠️  WORST IMPROVEMENTS:")
        for improvement in all_improvements[-5:]:  # Bottom 5
            outlier_flag = " (OUTLIER)" if improvement['is_outlier'] else ""
            print(f"   {improvement['week']} {improvement['day']}: {improvement['improvement']:.1f}pp improvement ({improvement['improvement_pct']:.1f}% better){outlier_flag}")
    
    # Create comprehensive backtest Excel
    create_backtest_excel(results)
    
    return results

def create_backtest_excel(results):
    """Create comprehensive backtest Excel"""
    print(f"\n=== CREATING COMPREHENSIVE BACKTEST EXCEL ===")
    
    with pd.ExcelWriter('comprehensive_backtest_results.xlsx', engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for result in results:
            summary_data.append({
                'Week': f"Week {result['week_num']}, {result['year']}",
                'Week_File': result['week_file'],
                'Is_Holiday': result['legitimate_holiday'],
                'Outlier_Days': ', '.join(result['outlier_days_detected']) if result['outlier_days_detected'] else 'None',
                'Avg_Original_Error_%': result.get('avg_original_error', 0),
                'Avg_Enhanced_Error_%': result.get('avg_enhanced_error', 0),
                'Avg_Improvement_pp': result.get('avg_improvement', 0)
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed daily comparison
        all_daily_data = []
        for result in results:
            for day_result in result['daily_comparison']:
                all_daily_data.append({
                    'Week': f"Week {result['week_num']}, {result['year']}",
                    'Week_File': result['week_file'],
                    'Is_Holiday': result['legitimate_holiday'],
                    'Day': day_result['day'],
                    'Is_Outlier': day_result['is_outlier'],
                    'Actual_Boxes': day_result['actual'],
                    'Original_Forecast': day_result['original_forecast'],
                    'Original_Error_%': day_result['original_error'],
                    'Enhanced_Forecast': day_result['enhanced_forecast'],
                    'Enhanced_Error_%': day_result['enhanced_error'],
                    'Improvement_pp': day_result['improvement'],
                    'Improvement_%': day_result['improvement_pct']
                })
        
        daily_df = pd.DataFrame(all_daily_data)
        daily_df.to_excel(writer, sheet_name='Daily_Comparison', index=False)
        
        # Individual week sheets
        for result in results:
            week_name = f"Week_{result['week_num']}_{result['year']}"
            daily_data = []
            for day_result in result['daily_comparison']:
                daily_data.append({
                    'Day': day_result['day'],
                    'Is_Outlier': day_result['is_outlier'],
                    'Actual_Boxes': day_result['actual'],
                    'Original_Forecast': day_result['original_forecast'],
                    'Original_Error_%': day_result['original_error'],
                    'Enhanced_Forecast': day_result['enhanced_forecast'],
                    'Enhanced_Error_%': day_result['enhanced_error'],
                    'Improvement_pp': day_result['improvement'],
                    'Improvement_%': day_result['improvement_pct']
                })
            
            week_df = pd.DataFrame(daily_data)
            week_df.to_excel(writer, sheet_name=week_name, index=False)
    
    print(f"✅ Comprehensive backtest Excel created: comprehensive_backtest_results.xlsx")

if __name__ == "__main__":
    comprehensive_backtest()
