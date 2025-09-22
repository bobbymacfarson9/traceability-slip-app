import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history
from enhanced_forecaster_with_outliers import EnhancedForecasterWithOutliers

def final_accuracy_comparison():
    """Compare all three forecasting methods: Original, Improved, and Enhanced with Outlier Detection"""
    print("=== FINAL ACCURACY COMPARISON: ALL THREE METHODS ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Create enhanced forecaster
    enhanced_forecaster = EnhancedForecasterWithOutliers(history_df)
    
    # Test on multiple weeks
    test_weeks = [
        ("Week 24 Loading Slip 2025.xlsx", 24, 2025, "Normal Week"),
        ("Week 32 Loading Slip 2025.xlsx", 32, 2025, "Holiday Week with Outliers")
    ]
    
    results = []
    
    for week_file, week_num, year, week_type in test_weeks:
        print(f"\n{'='*70}")
        print(f"TESTING {week_file.upper()} - {week_type}")
        print(f"{'='*70}")
        
        test_file = Path(week_file)
        if not test_file.exists():
            print(f"File not found: {week_file}")
            continue
        
        week_results = {
            'week_file': week_file,
            'week_type': week_type,
            'original_errors': [],
            'improved_errors': [],
            'enhanced_errors': [],
            'daily_comparison': []
        }
        
        for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
            print(f"\n--- {day.upper()} ---")
            
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                print(f"No actual data for {day}")
                continue
            
            total_actual = actual_data['boxes'].sum()
            print(f"Actual: {total_actual} boxes ({len(actual_data)} products)")
            
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
            
            # Enhanced forecast (with outlier detection)
            enhanced_forecast = enhanced_forecaster.forecast_weekday(day, year, week_num)
            enhanced_total = enhanced_forecast['forecast_boxes'].sum()
            enhanced_error = abs(enhanced_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Enhanced Forecast: {enhanced_total} boxes ({len(enhanced_forecast)} products) - Error: {enhanced_error:.1f}%")
            
            # Calculate improvements
            improvement_vs_original = original_error - enhanced_error
            improvement_pct = (improvement_vs_original / original_error * 100) if original_error > 0 else 0
            
            print(f"Improvement vs Original: {improvement_vs_original:.1f} percentage points ({improvement_pct:.1f}% better)")
            
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
                'improvement': improvement_vs_original,
                'improvement_pct': improvement_pct
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
            
            week_results['avg_original_error'] = avg_original_error
            week_results['avg_enhanced_error'] = avg_enhanced_error
            week_results['avg_improvement'] = avg_improvement
        
        results.append(week_results)
    
    # Overall comparison
    print(f"\n{'='*70}")
    print(f"OVERALL COMPARISON")
    print(f"{'='*70}")
    
    all_original_errors = []
    all_enhanced_errors = []
    
    for result in results:
        all_original_errors.extend(result['original_errors'])
        all_enhanced_errors.extend(result['enhanced_errors'])
    
    if all_original_errors and all_enhanced_errors:
        overall_original_error = sum(all_original_errors) / len(all_original_errors)
        overall_enhanced_error = sum(all_enhanced_errors) / len(all_enhanced_errors)
        overall_improvement = overall_original_error - overall_enhanced_error
        
        print(f"Overall Average Original Error: {overall_original_error:.1f}%")
        print(f"Overall Average Enhanced Error: {overall_enhanced_error:.1f}%")
        print(f"Overall Average Improvement: {overall_improvement:.1f} percentage points")
        
        # Calculate improvement percentage
        improvement_pct = (overall_improvement / overall_original_error * 100) if overall_original_error > 0 else 0
        print(f"Overall Improvement: {improvement_pct:.1f}% better")
        
        # Show best improvements
        print(f"\n🎯 BEST IMPROVEMENTS:")
        all_improvements = []
        for result in results:
            for day_result in result['daily_comparison']:
                all_improvements.append({
                    'week': result['week_file'],
                    'day': day_result['day'],
                    'improvement': day_result['improvement'],
                    'improvement_pct': day_result['improvement_pct']
                })
        
        all_improvements.sort(key=lambda x: x['improvement'], reverse=True)
        for improvement in all_improvements[:5]:  # Top 5
            print(f"   {improvement['week']} {improvement['day']}: {improvement['improvement']:.1f}pp improvement ({improvement['improvement_pct']:.1f}% better)")
    
    # Create final comparison Excel
    create_final_comparison_excel(results)
    
    return results

def create_final_comparison_excel(results):
    """Create final comparison Excel with all three methods"""
    print(f"\n=== CREATING FINAL COMPARISON EXCEL ===")
    
    with pd.ExcelWriter('final_forecasting_comparison.xlsx', engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for result in results:
            summary_data.append({
                'Week': result['week_file'],
                'Week_Type': result['week_type'],
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
                    'Week': result['week_file'],
                    'Week_Type': result['week_type'],
                    'Day': day_result['day'],
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
            week_name = result['week_file'].replace('.xlsx', '').replace(' ', '_')
            daily_data = []
            for day_result in result['daily_comparison']:
                daily_data.append({
                    'Day': day_result['day'],
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
    
    print(f"✅ Final comparison Excel created: final_forecasting_comparison.xlsx")

if __name__ == "__main__":
    final_accuracy_comparison()
