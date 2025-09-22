import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history
from balanced_forecaster import BalancedForecaster

def test_balanced_accuracy():
    """Test the balanced forecaster on the same weeks we backtested"""
    print("=== TESTING BALANCED FORECASTER ACCURACY ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Create balanced forecaster
    balanced_forecaster = BalancedForecaster(history_df)
    
    # Test on the same weeks we backtested
    test_weeks = [
        ("Week 24 Loading Slip 2025.xlsx", 24, 2025, "Normal Week"),
        ("Week 32 Loading Slip 2025.xlsx", 32, 2025, "Holiday Week with Outliers"),
        ("Week 29 Loading Slip 2025.xlsx", 29, 2025, "Week with Outliers"),
        ("Week 12 Loading Slip 2025.xlsx", 12, 2025, "Normal Week"),
        ("Week 36 Loading Slip 2025.xlsx", 36, 2025, "Normal Week"),
        ("Week 22 Loading Slip 2025.xlsx", 22, 2025, "Holiday Week")
    ]
    
    results = []
    
    for week_file, week_num, year, week_type in test_weeks:
        print(f"\n{'='*60}")
        print(f"TESTING {week_file.upper()} - {week_type}")
        print(f"{'='*60}")
        
        test_file = Path(week_file)
        if not test_file.exists():
            print(f"File not found: {week_file}")
            continue
        
        week_results = {
            'week_file': week_file,
            'week_type': week_type,
            'original_errors': [],
            'balanced_errors': [],
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
            
            # Balanced forecast
            balanced_forecast = balanced_forecaster.forecast_weekday(day, year, week_num)
            balanced_total = balanced_forecast['forecast_boxes'].sum()
            balanced_error = abs(balanced_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Balanced Forecast: {balanced_total} boxes ({len(balanced_forecast)} products) - Error: {balanced_error:.1f}%")
            
            # Calculate improvement
            improvement = original_error - balanced_error
            improvement_pct = (improvement / original_error * 100) if original_error > 0 else 0
            
            print(f"Improvement: {improvement:.1f} percentage points ({improvement_pct:.1f}% better)")
            
            # Store results
            week_results['original_errors'].append(original_error)
            week_results['balanced_errors'].append(balanced_error)
            week_results['daily_comparison'].append({
                'day': day,
                'actual': total_actual,
                'original_forecast': original_total,
                'original_error': original_error,
                'balanced_forecast': balanced_total,
                'balanced_error': balanced_error,
                'improvement': improvement,
                'improvement_pct': improvement_pct
            })
        
        # Calculate weekly averages
        if week_results['original_errors']:
            avg_original_error = sum(week_results['original_errors']) / len(week_results['original_errors'])
            avg_balanced_error = sum(week_results['balanced_errors']) / len(week_results['balanced_errors'])
            avg_improvement = avg_original_error - avg_balanced_error
            
            print(f"\n📊 WEEKLY SUMMARY:")
            print(f"   Average Original Error: {avg_original_error:.1f}%")
            print(f"   Average Balanced Error: {avg_balanced_error:.1f}%")
            print(f"   Average Improvement: {avg_improvement:.1f} percentage points")
            
            week_results['avg_original_error'] = avg_original_error
            week_results['avg_balanced_error'] = avg_balanced_error
            week_results['avg_improvement'] = avg_improvement
        
        results.append(week_results)
    
    # Overall comparison
    print(f"\n{'='*70}")
    print(f"BALANCED FORECASTER RESULTS")
    print(f"{'='*70}")
    
    all_original_errors = []
    all_balanced_errors = []
    
    for result in results:
        all_original_errors.extend(result['original_errors'])
        all_balanced_errors.extend(result['balanced_errors'])
    
    if all_original_errors and all_balanced_errors:
        overall_original_error = sum(all_original_errors) / len(all_original_errors)
        overall_balanced_error = sum(all_balanced_errors) / len(all_balanced_errors)
        overall_improvement = overall_original_error - overall_balanced_error
        
        print(f"Overall Average Original Error: {overall_original_error:.1f}%")
        print(f"Overall Average Balanced Error: {overall_balanced_error:.1f}%")
        print(f"Overall Average Improvement: {overall_improvement:.1f} percentage points")
        
        # Calculate improvement percentage
        improvement_pct = (overall_improvement / overall_original_error * 100) if overall_original_error > 0 else 0
        print(f"Overall Improvement: {improvement_pct:.1f}% better")
        
        # Analyze by week type
        normal_weeks = [r for r in results if 'Normal' in r['week_type']]
        holiday_weeks = [r for r in results if 'Holiday' in r['week_type']]
        outlier_weeks = [r for r in results if 'Outlier' in r['week_type']]
        
        print(f"\n📊 BREAKDOWN BY WEEK TYPE:")
        print(f"   Normal weeks: {len(normal_weeks)}")
        print(f"   Holiday weeks: {len(holiday_weeks)}")
        print(f"   Outlier weeks: {len(outlier_weeks)}")
        
        if normal_weeks:
            normal_original = sum([e for r in normal_weeks for e in r['original_errors']]) / len([e for r in normal_weeks for e in r['original_errors']])
            normal_balanced = sum([e for r in normal_weeks for e in r['balanced_errors']]) / len([e for r in normal_weeks for e in r['balanced_errors']])
            print(f"   Normal weeks - Original: {normal_original:.1f}%, Balanced: {normal_balanced:.1f}%, Improvement: {normal_original - normal_balanced:.1f}pp")
        
        if holiday_weeks:
            holiday_original = sum([e for r in holiday_weeks for e in r['original_errors']]) / len([e for r in holiday_weeks for e in r['original_errors']])
            holiday_balanced = sum([e for r in holiday_weeks for e in r['balanced_errors']]) / len([e for r in holiday_weeks for e in r['balanced_errors']])
            print(f"   Holiday weeks - Original: {holiday_original:.1f}%, Balanced: {holiday_balanced:.1f}%, Improvement: {holiday_original - holiday_balanced:.1f}pp")
        
        if outlier_weeks:
            outlier_original = sum([e for r in outlier_weeks for e in r['original_errors']]) / len([e for r in outlier_weeks for e in r['original_errors']])
            outlier_balanced = sum([e for r in outlier_weeks for e in r['balanced_errors']]) / len([e for r in outlier_weeks for e in r['balanced_errors']])
            print(f"   Outlier weeks - Original: {outlier_original:.1f}%, Balanced: {outlier_balanced:.1f}%, Improvement: {outlier_original - outlier_balanced:.1f}pp")
        
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
    
    return results

if __name__ == "__main__":
    test_balanced_accuracy()
