import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history
from improved_forecaster import ImprovedForecaster

def compare_forecasting_methods():
    """Compare original vs improved forecasting methods"""
    print("=== COMPARING FORECASTING METHODS ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Create both forecasters
    improved_forecaster = ImprovedForecaster(history_df)
    
    # Test on multiple weeks
    test_weeks = [
        ("Week 24 Loading Slip 2025.xlsx", 24, 2025, "Normal Week"),
        ("Week 32 Loading Slip 2025.xlsx", 32, 2025, "Holiday Week")
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
            'improved_errors': [],
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
            
            # Improved forecast
            improved_forecast = improved_forecaster.forecast_weekday(day, year, week_num)
            improved_total = improved_forecast['forecast_boxes'].sum()
            improved_error = abs(improved_total - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Improved Forecast: {improved_total} boxes ({len(improved_forecast)} products) - Error: {improved_error:.1f}%")
            
            # Calculate improvement
            improvement = original_error - improved_error
            improvement_pct = (improvement / original_error * 100) if original_error > 0 else 0
            
            print(f"Improvement: {improvement:.1f} percentage points ({improvement_pct:.1f}% better)")
            
            # Store results
            week_results['original_errors'].append(original_error)
            week_results['improved_errors'].append(improved_error)
            week_results['daily_comparison'].append({
                'day': day,
                'actual': total_actual,
                'original_forecast': original_total,
                'original_error': original_error,
                'improved_forecast': improved_total,
                'improved_error': improved_error,
                'improvement': improvement,
                'improvement_pct': improvement_pct
            })
        
        # Calculate weekly averages
        if week_results['original_errors']:
            avg_original_error = sum(week_results['original_errors']) / len(week_results['original_errors'])
            avg_improved_error = sum(week_results['improved_errors']) / len(week_results['improved_errors'])
            avg_improvement = avg_original_error - avg_improved_error
            
            print(f"\n📊 WEEKLY SUMMARY:")
            print(f"   Average Original Error: {avg_original_error:.1f}%")
            print(f"   Average Improved Error: {avg_improved_error:.1f}%")
            print(f"   Average Improvement: {avg_improvement:.1f} percentage points")
            
            week_results['avg_original_error'] = avg_original_error
            week_results['avg_improved_error'] = avg_improved_error
            week_results['avg_improvement'] = avg_improvement
        
        results.append(week_results)
    
    # Overall comparison
    print(f"\n{'='*60}")
    print(f"OVERALL COMPARISON")
    print(f"{'='*60}")
    
    all_original_errors = []
    all_improved_errors = []
    
    for result in results:
        all_original_errors.extend(result['original_errors'])
        all_improved_errors.extend(result['improved_errors'])
    
    if all_original_errors and all_improved_errors:
        overall_original_error = sum(all_original_errors) / len(all_original_errors)
        overall_improved_error = sum(all_improved_errors) / len(all_improved_errors)
        overall_improvement = overall_original_error - overall_improved_error
        
        print(f"Overall Average Original Error: {overall_original_error:.1f}%")
        print(f"Overall Average Improved Error: {overall_improved_error:.1f}%")
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
    
    # Create detailed Excel comparison
    create_detailed_comparison_excel(results)
    
    return results

def create_detailed_comparison_excel(results):
    """Create detailed Excel comparison of forecasting methods"""
    print(f"\n=== CREATING DETAILED COMPARISON EXCEL ===")
    
    with pd.ExcelWriter('forecasting_methods_comparison.xlsx', engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for result in results:
            summary_data.append({
                'Week': result['week_file'],
                'Week_Type': result['week_type'],
                'Avg_Original_Error_%': result.get('avg_original_error', 0),
                'Avg_Improved_Error_%': result.get('avg_improved_error', 0),
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
                    'Improved_Forecast': day_result['improved_forecast'],
                    'Improved_Error_%': day_result['improved_error'],
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
                    'Improved_Forecast': day_result['improved_forecast'],
                    'Improved_Error_%': day_result['improved_error'],
                    'Improvement_pp': day_result['improvement'],
                    'Improvement_%': day_result['improvement_pct']
                })
            
            week_df = pd.DataFrame(daily_data)
            week_df.to_excel(writer, sheet_name=week_name, index=False)
    
    print(f"✅ Detailed comparison Excel created: forecasting_methods_comparison.xlsx")

if __name__ == "__main__":
    compare_forecasting_methods()
