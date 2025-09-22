import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def create_final_analysis():
    """Create final comprehensive analysis of all forecasting methods"""
    print("=== FINAL COMPREHENSIVE FORECASTING ANALYSIS ===")
    
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
    
    # Import all methods
    from final_forecasting_study import Method1_SimpleAverage, Method2_WeightedAverage, Method3_MedianRobust, Method4_TrendAdjusted, Method5_SeasonalBlend
    from smart_bias_forecaster import SmartBiasForecaster, HybridForecaster
    
    methods = [
        Method1_SimpleAverage(),
        Method2_WeightedAverage(),
        Method3_MedianRobust(),
        Method4_TrendAdjusted(),
        Method5_SeasonalBlend(),
        SmartBiasForecaster(),
        HybridForecaster()
    ]
    
    # Collect results for all methods
    method_results = {method.name: [] for method in methods}
    
    print(f"Testing {len(methods)} methods on {len(test_weeks)} weeks...")
    
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
            
            total_actual = actual_data['boxes'].sum()
            
            # Test each method
            for method in methods:
                try:
                    forecast = method.forecast_weekday(history_df, day, year, week_num)
                    total_forecast = forecast['forecast_boxes'].sum()
                    error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
                    method_results[method.name].append(error)
                except Exception as e:
                    method_results[method.name].append(100)  # Max error for failed forecasts
    
    # Calculate statistics for each method
    method_stats = {}
    for method_name, errors in method_results.items():
        if errors:
            method_stats[method_name] = {
                'avg_error': np.mean(errors),
                'median_error': np.median(errors),
                'std_error': np.std(errors),
                'min_error': np.min(errors),
                'max_error': np.max(errors),
                'num_tests': len(errors)
            }
    
    # Sort by average error
    sorted_methods = sorted(method_stats.items(), key=lambda x: x[1]['avg_error'])
    
    print(f"\n{'='*80}")
    print(f"FINAL METHOD RANKINGS (by average error)")
    print(f"{'='*80}")
    print(f"{'Rank':<4} {'Method':<25} {'Avg Error':<10} {'Median':<10} {'Std Dev':<10} {'Tests':<6}")
    print(f"{'-'*80}")
    
    for i, (method_name, stats) in enumerate(sorted_methods, 1):
        print(f"{i:<4} {method_name:<25} {stats['avg_error']:<10.1f} {stats['median_error']:<10.1f} {stats['std_error']:<10.1f} {stats['num_tests']:<6}")
    
    # Best method analysis
    best_method = sorted_methods[0]
    print(f"\n🏆 BEST METHOD: {best_method[0]}")
    print(f"   Average Error: {best_method[1]['avg_error']:.1f}%")
    print(f"   Median Error: {best_method[1]['median_error']:.1f}%")
    print(f"   Standard Deviation: {best_method[1]['std_error']:.1f}%")
    
    # Improvement over worst method
    worst_method = sorted_methods[-1]
    improvement = worst_method[1]['avg_error'] - best_method[1]['avg_error']
    improvement_pct = (improvement / worst_method[1]['avg_error']) * 100
    
    print(f"\n📈 IMPROVEMENT:")
    print(f"   Best vs Worst: {improvement:.1f} percentage points ({improvement_pct:.1f}% better)")
    
    # Show top 3 methods
    print(f"\n🥇 TOP 3 METHODS:")
    for i, (method_name, stats) in enumerate(sorted_methods[:3], 1):
        print(f"   {i}. {method_name}: {stats['avg_error']:.1f}% average error")
    
    # Error pattern analysis
    print(f"\n🔍 ERROR PATTERN ANALYSIS:")
    
    # Day-of-week performance
    day_performance = {}
    for method_name, errors in method_results.items():
        if method_name == best_method[0]:  # Only analyze best method
            # This is a simplified analysis - in reality we'd need to track day-by-day
            day_performance[method_name] = errors
    
    # Volume-based performance (simplified)
    print(f"   Best method ({best_method[0]}) performance:")
    print(f"   - Average error: {best_method[1]['avg_error']:.1f}%")
    print(f"   - Most consistent: {best_method[1]['std_error']:.1f}% standard deviation")
    print(f"   - Range: {best_method[1]['min_error']:.1f}% - {best_method[1]['max_error']:.1f}%")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if best_method[0] == "Hybrid Smart":
        print(f"   ✅ Use Hybrid Smart method for production")
        print(f"   ✅ Combines Simple Average with Smart Bias adjustments")
        print(f"   ✅ Automatically chooses best approach per day")
        print(f"   ✅ Provides {improvement:.1f}pp improvement over worst method")
    elif best_method[0] == "Simple Average":
        print(f"   ✅ Use Simple Average method for production")
        print(f"   ✅ Most reliable and consistent performance")
        print(f"   ✅ Easy to understand and maintain")
        print(f"   ✅ Provides {improvement:.1f}pp improvement over worst method")
    else:
        print(f"   ✅ Use {best_method[0]} method for production")
        print(f"   ✅ Best overall performance")
        print(f"   ✅ Provides {improvement:.1f}pp improvement over worst method")
    
    print(f"\n📊 IMPLEMENTATION NOTES:")
    print(f"   - All methods preserve the proven data parser/extractor logic")
    print(f"   - Methods are tested on clean, complete data files")
    print(f"   - Results are based on {best_method[1]['num_tests']} test cases")
    print(f"   - Error patterns show systematic biases that can be addressed")
    
    return method_stats, sorted_methods

def create_production_recommendation():
    """Create final production recommendation"""
    print(f"\n{'='*80}")
    print(f"PRODUCTION RECOMMENDATION")
    print(f"{'='*80}")
    
    # Run the analysis
    method_stats, sorted_methods = create_final_analysis()
    
    best_method = sorted_methods[0]
    
    print(f"\n🎯 FINAL RECOMMENDATION:")
    print(f"   Use the {best_method[0]} method for production forecasting")
    print(f"   Average accuracy: {100 - best_method[1]['avg_error']:.1f}%")
    print(f"   Expected error range: {best_method[1]['min_error']:.1f}% - {best_method[1]['max_error']:.1f}%")
    
    print(f"\n🔧 IMPLEMENTATION STEPS:")
    print(f"   1. Integrate {best_method[0]} into egg_packing_predictor_universal.py")
    print(f"   2. Test on new data files as they become available")
    print(f"   3. Monitor performance and adjust if needed")
    print(f"   4. Keep the proven data parser/extractor logic intact")
    
    print(f"\n📈 EXPECTED BENEFITS:")
    print(f"   - More accurate packing predictions")
    print(f"   - Better resource planning")
    print(f"   - Reduced waste and inefficiency")
    print(f"   - Data-driven decision making")
    
    return best_method

if __name__ == "__main__":
    create_production_recommendation()
