import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history
from smart_bias_forecaster import HybridForecaster

def detailed_accuracy_breakdown():
    """Detailed breakdown of accuracy issues by product, day, and volume"""
    print("=== DETAILED ACCURACY BREAKDOWN ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Use Hybrid Smart method (our best performer)
    method = HybridForecaster()
    
    # Test weeks (same as our study)
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Collect detailed error data
    error_data = []
    
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
            
            # Get forecast
            forecast_data = method.forecast_weekday(history_df, day, year, week_num)
            
            # Calculate errors for each product
            for _, actual_row in actual_data.iterrows():
                product = actual_row['product']
                actual_boxes = actual_row['boxes']
                
                # Find corresponding forecast
                forecast_row = forecast_data[forecast_data['product'] == product]
                if not forecast_row.empty:
                    forecast_boxes = forecast_row['forecast_boxes'].iloc[0]
                else:
                    forecast_boxes = 0  # Product not forecasted
                
                # Calculate error metrics
                absolute_error = abs(forecast_boxes - actual_boxes)
                percentage_error = (absolute_error / actual_boxes * 100) if actual_boxes > 0 else 0
                bias = forecast_boxes - actual_boxes  # Positive = over-predict, Negative = under-predict
                bias_percentage = (bias / actual_boxes * 100) if actual_boxes > 0 else 0
                
                # Categorize by volume
                if actual_boxes <= 5:
                    volume_category = "Very Small (1-5)"
                elif actual_boxes <= 15:
                    volume_category = "Small (6-15)"
                elif actual_boxes <= 50:
                    volume_category = "Medium (16-50)"
                elif actual_boxes <= 100:
                    volume_category = "Large (51-100)"
                else:
                    volume_category = "Very Large (100+)"
                
                error_data.append({
                    'week_file': week_file,
                    'week_num': week_num,
                    'year': year,
                    'day': day,
                    'product': product,
                    'actual_boxes': actual_boxes,
                    'forecast_boxes': forecast_boxes,
                    'absolute_error': absolute_error,
                    'percentage_error': percentage_error,
                    'bias': bias,
                    'bias_percentage': bias_percentage,
                    'volume_category': volume_category,
                    'over_predicted': bias > 0,
                    'under_predicted': bias < 0,
                    'exact_match': bias == 0
                })
    
    # Convert to DataFrame
    error_df = pd.DataFrame(error_data)
    
    if error_df.empty:
        print("No error data collected!")
        return
    
    print(f"Collected {len(error_df)} product-level error records")
    
    # Overall accuracy breakdown
    print(f"\n📊 OVERALL ACCURACY BREAKDOWN:")
    total_actual = error_df['actual_boxes'].sum()
    total_forecast = error_df['forecast_boxes'].sum()
    total_error = abs(total_forecast - total_actual)
    overall_accuracy = (1 - total_error / total_actual) * 100 if total_actual > 0 else 0
    
    print(f"Total actual boxes: {total_actual:,}")
    print(f"Total forecast boxes: {total_forecast:,}")
    print(f"Total error: {total_error:,} boxes")
    print(f"Overall accuracy: {overall_accuracy:.1f}%")
    
    # Volume-based accuracy breakdown
    print(f"\n📦 ACCURACY BY VOLUME CATEGORY:")
    volume_analysis = error_df.groupby('volume_category').agg({
        'actual_boxes': ['sum', 'count', 'mean'],
        'forecast_boxes': 'sum',
        'absolute_error': 'sum',
        'percentage_error': 'mean',
        'bias': 'sum'
    }).round(1)
    
    print(f"{'Category':<20} {'Count':<6} {'Avg Actual':<10} {'Total Actual':<12} {'Total Error':<12} {'Avg Error %':<10} {'Bias':<10}")
    print(f"{'-'*90}")
    
    for category in ['Very Small (1-5)', 'Small (6-15)', 'Medium (16-50)', 'Large (51-100)', 'Very Large (100+)']:
        if category in volume_analysis.index:
            row = volume_analysis.loc[category]
            count = row[('actual_boxes', 'count')]
            avg_actual = row[('actual_boxes', 'mean')]
            total_actual = row[('actual_boxes', 'sum')]
            total_error = row[('absolute_error', 'sum')]
            avg_error_pct = row[('percentage_error', 'mean')]
            bias = row[('bias', 'sum')]
            
            print(f"{category:<20} {count:<6} {avg_actual:<10.1f} {total_actual:<12.0f} {total_error:<12.0f} {avg_error_pct:<10.1f} {bias:<+10.0f}")
    
    # Day-of-week accuracy breakdown
    print(f"\n📅 ACCURACY BY DAY OF WEEK:")
    day_analysis = error_df.groupby('day').agg({
        'actual_boxes': ['sum', 'count'],
        'forecast_boxes': 'sum',
        'absolute_error': 'sum',
        'percentage_error': 'mean',
        'bias': 'sum'
    }).round(1)
    
    print(f"{'Day':<8} {'Count':<6} {'Total Actual':<12} {'Total Error':<12} {'Avg Error %':<10} {'Bias':<10}")
    print(f"{'-'*70}")
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        if day in day_analysis.index:
            row = day_analysis.loc[day]
            count = row[('actual_boxes', 'count')]
            total_actual = row[('actual_boxes', 'sum')]
            total_error = row[('absolute_error', 'sum')]
            avg_error_pct = row[('percentage_error', 'mean')]
            bias = row[('bias', 'sum')]
            
            print(f"{day:<8} {count:<6} {total_actual:<12.0f} {total_error:<12.0f} {avg_error_pct:<10.1f} {bias:<+10.0f}")
    
    # Product-level accuracy breakdown (top problematic products)
    print(f"\n🥚 MOST PROBLEMATIC PRODUCTS:")
    product_analysis = error_df.groupby('product').agg({
        'actual_boxes': ['sum', 'count', 'mean'],
        'forecast_boxes': 'sum',
        'absolute_error': 'sum',
        'percentage_error': 'mean',
        'bias': 'sum'
    }).round(1)
    
    # Sort by total error
    product_analysis_sorted = product_analysis.sort_values(('absolute_error', 'sum'), ascending=False)
    
    print(f"{'Product':<25} {'Count':<6} {'Avg Actual':<10} {'Total Actual':<12} {'Total Error':<12} {'Avg Error %':<10} {'Bias':<10}")
    print(f"{'-'*95}")
    
    for product in product_analysis_sorted.index[:15]:  # Top 15 problematic products
        row = product_analysis_sorted.loc[product]
        count = row[('actual_boxes', 'count')]
        avg_actual = row[('actual_boxes', 'mean')]
        total_actual = row[('actual_boxes', 'sum')]
        total_error = row[('absolute_error', 'sum')]
        avg_error_pct = row[('percentage_error', 'mean')]
        bias = row[('bias', 'sum')]
        
        print(f"{product:<25} {count:<6} {avg_actual:<10.1f} {total_actual:<12.0f} {total_error:<12.0f} {avg_error_pct:<10.1f} {bias:<+10.0f}")
    
    # Error distribution analysis
    print(f"\n📈 ERROR DISTRIBUTION ANALYSIS:")
    
    # Small errors (easy to correct on day of)
    small_errors = error_df[error_df['absolute_error'] <= 5]
    medium_errors = error_df[(error_df['absolute_error'] > 5) & (error_df['absolute_error'] <= 20)]
    large_errors = error_df[error_df['absolute_error'] > 20]
    
    print(f"Small errors (≤5 boxes): {len(small_errors)} products ({len(small_errors)/len(error_df)*100:.1f}%)")
    print(f"Medium errors (6-20 boxes): {len(medium_errors)} products ({len(medium_errors)/len(error_df)*100:.1f}%)")
    print(f"Large errors (>20 boxes): {len(large_errors)} products ({len(large_errors)/len(error_df)*100:.1f}%)")
    
    # Show examples of large errors
    if len(large_errors) > 0:
        print(f"\n🚨 EXAMPLES OF LARGE ERRORS (>20 boxes):")
        large_errors_sorted = large_errors.sort_values('absolute_error', ascending=False)
        print(f"{'Week':<30} {'Day':<6} {'Product':<25} {'Actual':<8} {'Forecast':<8} {'Error':<8} {'% Error':<8}")
        print(f"{'-'*95}")
        
        for _, row in large_errors_sorted.head(10).iterrows():
            print(f"{row['week_file']:<30} {row['day']:<6} {row['product']:<25} {row['actual_boxes']:<8} {row['forecast_boxes']:<8} {row['absolute_error']:<8} {row['percentage_error']:<8.1f}")
    
    # Bias analysis
    print(f"\n⚖️ BIAS ANALYSIS:")
    over_predicted = error_df[error_df['over_predicted']]
    under_predicted = error_df[error_df['under_predicted']]
    exact_matches = error_df[error_df['exact_match']]
    
    print(f"Over-predicted: {len(over_predicted)} products ({len(over_predicted)/len(error_df)*100:.1f}%)")
    print(f"Under-predicted: {len(under_predicted)} products ({len(under_predicted)/len(error_df)*100:.1f}%)")
    print(f"Exact matches: {len(exact_matches)} products ({len(exact_matches)/len(error_df)*100:.1f}%)")
    
    total_bias = error_df['bias'].sum()
    print(f"Total bias: {total_bias:+.0f} boxes ({total_bias/error_df['actual_boxes'].sum()*100:+.1f}%)")
    
    # Practical impact analysis
    print(f"\n🎯 PRACTICAL IMPACT ANALYSIS:")
    
    # Calculate impact by volume
    very_small_impact = error_df[error_df['volume_category'] == 'Very Small (1-5)']['absolute_error'].sum()
    small_impact = error_df[error_df['volume_category'] == 'Small (6-15)']['absolute_error'].sum()
    medium_impact = error_df[error_df['volume_category'] == 'Medium (16-50)']['absolute_error'].sum()
    large_impact = error_df[error_df['volume_category'] == 'Large (51-100)']['absolute_error'].sum()
    very_large_impact = error_df[error_df['volume_category'] == 'Very Large (100+)']['absolute_error'].sum()
    
    total_impact = very_small_impact + small_impact + medium_impact + large_impact + very_large_impact
    
    print(f"Error impact by volume category:")
    print(f"  Very Small (1-5 boxes): {very_small_impact:.0f} boxes ({very_small_impact/total_impact*100:.1f}% of total error)")
    print(f"  Small (6-15 boxes): {small_impact:.0f} boxes ({small_impact/total_impact*100:.1f}% of total error)")
    print(f"  Medium (16-50 boxes): {medium_impact:.0f} boxes ({medium_impact/total_impact*100:.1f}% of total error)")
    print(f"  Large (51-100 boxes): {large_impact:.0f} boxes ({large_impact/total_impact*100:.1f}% of total error)")
    print(f"  Very Large (100+ boxes): {very_large_impact:.0f} boxes ({very_large_impact/total_impact*100:.1f}% of total error)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if very_small_impact + small_impact > total_impact * 0.5:
        print(f"  ✅ Most errors are in small volume products - easy to correct on day of")
        print(f"  ✅ System is working well for major products")
    else:
        print(f"  ⚠️ Significant errors in medium/large volume products - may need attention")
    
    if len(large_errors) < len(error_df) * 0.1:
        print(f"  ✅ Few large errors - system is generally reliable")
    else:
        print(f"  ⚠️ Many large errors - may need refinement")
    
    return error_df

if __name__ == "__main__":
    detailed_accuracy_breakdown()
