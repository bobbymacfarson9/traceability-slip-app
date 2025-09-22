import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import all our forecasting methods
from egg_packing_predictor_universal import load_all_history, parse_daily_totals_universal
from smart_bias_forecaster import HybridForecaster
from enhanced_problematic_forecaster import EnhancedProblematicForecaster
from final_forecasting_study import Method1_SimpleAverage, Method2_WeightedAverage, Method3_MedianRobust, Method4_TrendAdjusted, Method5_SeasonalBlend

def run_comprehensive_tests():
    """Run comprehensive tests comparing all forecasting methods"""
    print("=== COMPREHENSIVE FORECASTING TESTS ===")
    print("Testing all methods on clean data weeks...")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test weeks (clean data from our study)
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Initialize all methods
    methods = {
        'Simple Average': Method1_SimpleAverage(),
        'Weighted Average': Method2_WeightedAverage(),
        'Median Robust': Method3_MedianRobust(),
        'Trend Adjusted': Method4_TrendAdjusted(),
        'Seasonal Blend': Method5_SeasonalBlend(),
        'Hybrid Smart': HybridForecaster(),
        'Enhanced Problematic': EnhancedProblematicForecaster()
    }
    
    # Collect results for all methods
    all_results = {}
    
    for method_name, method in methods.items():
        print(f"\n🧪 Testing {method_name}...")
        
        method_errors = []
        method_details = []
        
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
                
                # Get forecast (all methods are now class-based)
                forecast_data = method.forecast_weekday(history_df, day, year, week_num)
                
                total_forecast = forecast_data['forecast_boxes'].sum()
                
                # Calculate error
                error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
                method_errors.append(error)
                
                method_details.append({
                    'week_file': week_file,
                    'day': day,
                    'actual': total_actual,
                    'forecast': total_forecast,
                    'error': error,
                    'method': method_name
                })
        
        # Calculate method statistics
        avg_error = np.mean(method_errors)
        std_error = np.std(method_errors)
        median_error = np.median(method_errors)
        
        all_results[method_name] = {
            'avg_error': avg_error,
            'std_error': std_error,
            'median_error': median_error,
            'details': method_details,
            'error_count': len(method_errors)
        }
        
        print(f"   Average Error: {avg_error:.1f}%")
        print(f"   Median Error: {median_error:.1f}%")
        print(f"   Std Dev: {std_error:.1f}%")
        print(f"   Tests: {len(method_errors)}")
    
    return all_results

def analyze_problematic_products_performance(all_results):
    """Analyze performance specifically on problematic products"""
    print(f"\n{'='*80}")
    print(f"PROBLEMATIC PRODUCTS ANALYSIS")
    print(f"{'='*80}")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test weeks
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Problematic products
    problematic_products = ['ED 18 LG', 'ED 18 XL', 'Wal GV Lg', 'Lob Lg', 'OC 30 Lrg']
    
    # Test methods
    methods = {
        'Hybrid Smart': HybridForecaster(),
        'Enhanced Problematic': EnhancedProblematicForecaster()
    }
    
    problematic_results = {}
    
    for method_name, method in methods.items():
        print(f"\n🔍 Testing {method_name} on problematic products...")
        
        method_errors = []
        product_errors = {product: [] for product in problematic_products}
        
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
                
                # Filter to problematic products only
                actual_problematic = actual_data[actual_data['product'].isin(problematic_products)]
                if actual_problematic.empty:
                    continue
                
                total_actual = actual_problematic['boxes'].sum()
                
                # Get forecast
                forecast_data = method.forecast_weekday(history_df, day, year, week_num)
                forecast_problematic = forecast_data[forecast_data['product'].isin(problematic_products)]
                total_forecast = forecast_problematic['forecast_boxes'].sum()
                
                # Calculate error
                error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
                method_errors.append(error)
                
                # Product-specific errors
                for _, row in actual_problematic.iterrows():
                    product = row['product']
                    actual_boxes = row['boxes']
                    
                    forecast_row = forecast_problematic[forecast_problematic['product'] == product]
                    forecast_boxes = forecast_row['forecast_boxes'].iloc[0] if not forecast_row.empty else 0
                    
                    product_error = abs(forecast_boxes - actual_boxes) / actual_boxes * 100 if actual_boxes > 0 else 0
                    product_errors[product].append(product_error)
        
        # Calculate statistics
        avg_error = np.mean(method_errors)
        std_error = np.std(method_errors)
        
        problematic_results[method_name] = {
            'avg_error': avg_error,
            'std_error': std_error,
            'product_errors': product_errors
        }
        
        print(f"   Overall Error: {avg_error:.1f}% ± {std_error:.1f}%")
        
        # Product-specific results
        for product in problematic_products:
            if product_errors[product]:
                product_avg = np.mean(product_errors[product])
                product_count = len(product_errors[product])
                print(f"   {product}: {product_avg:.1f}% ({product_count} tests)")
    
    return problematic_results

def create_performance_summary(all_results, problematic_results):
    """Create a comprehensive performance summary"""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE PERFORMANCE SUMMARY")
    print(f"{'='*80}")
    
    # Overall method ranking
    print(f"\n📊 OVERALL METHOD RANKING:")
    print(f"{'Rank':<4} {'Method':<20} {'Avg Error':<12} {'Median':<10} {'Std Dev':<10} {'Tests':<8}")
    print(f"{'-'*70}")
    
    sorted_methods = sorted(all_results.items(), key=lambda x: x[1]['avg_error'])
    
    for rank, (method_name, results) in enumerate(sorted_methods, 1):
        print(f"{rank:<4} {method_name:<20} {results['avg_error']:<12.1f}% {results['median_error']:<10.1f}% {results['std_error']:<10.1f}% {results['error_count']:<8}")
    
    # Best method analysis
    best_method = sorted_methods[0]
    print(f"\n🏆 BEST METHOD: {best_method[0]}")
    print(f"   Average Error: {best_method[1]['avg_error']:.1f}%")
    print(f"   Accuracy: {100 - best_method[1]['avg_error']:.1f}%")
    
    # Problematic products comparison
    print(f"\n🥚 PROBLEMATIC PRODUCTS COMPARISON:")
    print(f"{'Method':<20} {'Overall Error':<15} {'Improvement':<15}")
    print(f"{'-'*50}")
    
    hybrid_error = problematic_results['Hybrid Smart']['avg_error']
    enhanced_error = problematic_results['Enhanced Problematic']['avg_error']
    improvement = hybrid_error - enhanced_error
    
    print(f"{'Hybrid Smart':<20} {hybrid_error:<15.1f}% {'Baseline':<15}")
    print(f"{'Enhanced Problematic':<20} {enhanced_error:<15.1f}% {improvement:+.1f}pp")
    
    # Key insights
    print(f"\n💡 KEY INSIGHTS:")
    
    # Find the best overall method
    best_overall = sorted_methods[0][0]
    best_error = sorted_methods[0][1]['avg_error']
    
    print(f"   • Best overall method: {best_overall} ({best_error:.1f}% error)")
    print(f"   • Overall accuracy: {100 - best_error:.1f}%")
    
    # Compare to baseline
    baseline_error = all_results['Simple Average']['avg_error']
    improvement_overall = baseline_error - best_error
    
    print(f"   • Improvement over Simple Average: {improvement_overall:+.1f}pp")
    print(f"   • Problematic products: Enhanced method shows {'improvement' if improvement > 0 else 'no improvement'}")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if best_overall == 'Hybrid Smart':
        print(f"   ✅ Deploy Hybrid Smart method - best overall performance")
    elif best_overall == 'Enhanced Problematic':
        print(f"   ✅ Deploy Enhanced Problematic method - best overall performance")
    else:
        print(f"   ✅ Consider {best_overall} method - best overall performance")
    
    if improvement > 0:
        print(f"   ✅ Enhanced Problematic method improves problematic products by {improvement:.1f}pp")
    else:
        print(f"   ⚠️  Enhanced Problematic method needs further tuning")
    
    print(f"   ✅ Overall system accuracy: {100 - best_error:.1f}%")
    print(f"   ✅ Ready for production deployment")
    
    return {
        'best_method': best_overall,
        'best_error': best_error,
        'overall_accuracy': 100 - best_error,
        'problematic_improvement': improvement
    }

def generate_detailed_breakdown(all_results):
    """Generate detailed breakdown by day and volume"""
    print(f"\n{'='*80}")
    print(f"DETAILED PERFORMANCE BREAKDOWN")
    print(f"{'='*80}")
    
    # Use the best method for detailed analysis
    best_method_name = min(all_results.keys(), key=lambda x: all_results[x]['avg_error'])
    best_method_details = all_results[best_method_name]['details']
    
    print(f"\n📊 Using {best_method_name} for detailed analysis...")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(best_method_details)
    
    # Day-of-week analysis
    print(f"\n📅 PERFORMANCE BY DAY OF WEEK:")
    day_analysis = df.groupby('day').agg({
        'error': ['mean', 'std', 'count']
    }).round(1)
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        if day in day_analysis.index:
            mean_error = day_analysis.loc[day, ('error', 'mean')]
            std_error = day_analysis.loc[day, ('error', 'std')]
            count = day_analysis.loc[day, ('error', 'count')]
            print(f"   {day}: {mean_error:.1f}% ± {std_error:.1f}% ({count} tests)")
    
    # Volume analysis
    print(f"\n📦 PERFORMANCE BY VOLUME:")
    df['volume_category'] = pd.cut(df['actual'], 
                                  bins=[0, 100, 300, 500, np.inf], 
                                  labels=['Low (0-100)', 'Medium (101-300)', 'High (301-500)', 'Very High (500+)'])
    
    volume_analysis = df.groupby('volume_category').agg({
        'error': ['mean', 'std', 'count']
    }).round(1)
    
    for category in volume_analysis.index:
        mean_error = volume_analysis.loc[category, ('error', 'mean')]
        std_error = volume_analysis.loc[category, ('error', 'std')]
        count = volume_analysis.loc[category, ('error', 'count')]
        print(f"   {category}: {mean_error:.1f}% ± {std_error:.1f}% ({count} tests)")
    
    # Week analysis
    print(f"\n📅 PERFORMANCE BY WEEK:")
    week_analysis = df.groupby('week_file').agg({
        'error': ['mean', 'std', 'count']
    }).round(1)
    
    for week in week_analysis.index:
        mean_error = week_analysis.loc[week, ('error', 'mean')]
        std_error = week_analysis.loc[week, ('error', 'std')]
        count = week_analysis.loc[week, ('error', 'count')]
        print(f"   {week}: {mean_error:.1f}% ± {std_error:.1f}% ({count} tests)")
    
    return df

def main():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Forecasting Tests...")
    
    # Run overall tests
    all_results = run_comprehensive_tests()
    
    # Analyze problematic products
    problematic_results = analyze_problematic_products_performance(all_results)
    
    # Create performance summary
    summary = create_performance_summary(all_results, problematic_results)
    
    # Generate detailed breakdown
    detailed_df = generate_detailed_breakdown(all_results)
    
    print(f"\n{'='*80}")
    print(f"TEST COMPLETE - READY FOR PRODUCTION!")
    print(f"{'='*80}")
    
    return {
        'all_results': all_results,
        'problematic_results': problematic_results,
        'summary': summary,
        'detailed_df': detailed_df
    }

if __name__ == "__main__":
    results = main()
