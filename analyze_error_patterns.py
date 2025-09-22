import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history
from final_forecasting_study import Method1_SimpleAverage, FinalForecastingStudy

def analyze_error_patterns():
    """Analyze error patterns to identify systematic biases"""
    print("=== ANALYZING ERROR PATTERNS FOR BIAS DETECTION ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Use the same test weeks as our study
    test_weeks = [
        {'week_file': 'Week 45 Loading Slip 2024.xlsx', 'week_num': 45, 'year': 2024},
        {'week_file': 'Week 46 Loading Slip 2024.xlsx', 'week_num': 46, 'year': 2024},
        {'week_file': 'Week 47 Loading Slip 2024.xlsx', 'week_num': 47, 'year': 2024},
        {'week_file': 'Week 48 Loading Slip 2024.xlsx', 'week_num': 48, 'year': 2024},
        {'week_file': 'Week 49 Loading Slip 2024.xlsx', 'week_num': 49, 'year': 2024},
        {'week_file': 'Week 50 Loading Slip 2024.xlsx', 'week_num': 50, 'year': 2024}
    ]
    
    # Use Simple Average method (our best performer)
    method = Method1_SimpleAverage()
    
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
    
    # Overall bias analysis
    print(f"\n📊 OVERALL BIAS ANALYSIS:")
    total_bias = error_df['bias'].sum()
    avg_bias = error_df['bias'].mean()
    avg_bias_percentage = error_df['bias_percentage'].mean()
    
    print(f"Total bias: {total_bias:+.1f} boxes")
    print(f"Average bias: {avg_bias:+.1f} boxes per product")
    print(f"Average bias percentage: {avg_bias_percentage:+.1f}%")
    
    over_predicted = error_df['over_predicted'].sum()
    under_predicted = error_df['under_predicted'].sum()
    exact_matches = error_df['exact_match'].sum()
    
    print(f"\nPrediction direction:")
    print(f"  Over-predicted: {over_predicted} products ({over_predicted/len(error_df)*100:.1f}%)")
    print(f"  Under-predicted: {under_predicted} products ({under_predicted/len(error_df)*100:.1f}%)")
    print(f"  Exact matches: {exact_matches} products ({exact_matches/len(error_df)*100:.1f}%)")
    
    # Day-of-week bias analysis
    print(f"\n📅 DAY-OF-WEEK BIAS ANALYSIS:")
    day_bias = error_df.groupby('day').agg({
        'bias': ['mean', 'sum', 'count'],
        'bias_percentage': 'mean',
        'over_predicted': 'sum',
        'under_predicted': 'sum'
    }).round(2)
    
    print(f"{'Day':<8} {'Avg Bias':<10} {'Total Bias':<12} {'Bias %':<8} {'Over':<6} {'Under':<6} {'Count':<6}")
    print(f"{'-'*60}")
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        if day in day_bias.index:
            row = day_bias.loc[day]
            avg_bias = row[('bias', 'mean')]
            total_bias = row[('bias', 'sum')]
            bias_pct = row[('bias_percentage', 'mean')]
            over = row[('over_predicted', 'sum')]
            under = row[('under_predicted', 'sum')]
            count = row[('bias', 'count')]
            
            print(f"{day:<8} {avg_bias:<+10.1f} {total_bias:<+12.1f} {bias_pct:<+8.1f} {over:<6} {under:<6} {count:<6}")
    
    # Product-level bias analysis
    print(f"\n🥚 PRODUCT-LEVEL BIAS ANALYSIS:")
    product_bias = error_df.groupby('product').agg({
        'bias': ['mean', 'sum', 'count'],
        'bias_percentage': 'mean',
        'over_predicted': 'sum',
        'under_predicted': 'sum',
        'actual_boxes': 'mean'
    }).round(2)
    
    # Sort by average bias
    product_bias_sorted = product_bias.sort_values(('bias', 'mean'), ascending=False)
    
    print(f"{'Product':<25} {'Avg Bias':<10} {'Bias %':<8} {'Over':<6} {'Under':<6} {'Count':<6} {'Avg Actual':<10}")
    print(f"{'-'*80}")
    
    for product in product_bias_sorted.index[:15]:  # Top 15 products
        row = product_bias_sorted.loc[product]
        avg_bias = row[('bias', 'mean')]
        bias_pct = row[('bias_percentage', 'mean')]
        over = row[('over_predicted', 'sum')]
        under = row[('under_predicted', 'sum')]
        count = row[('bias', 'count')]
        avg_actual = row[('actual_boxes', 'mean')]
        
        print(f"{product:<25} {avg_bias:<+10.1f} {bias_pct:<+8.1f} {over:<6} {under:<6} {count:<6} {avg_actual:<10.1f}")
    
    # Week-level bias analysis
    print(f"\n📅 WEEK-LEVEL BIAS ANALYSIS:")
    week_bias = error_df.groupby('week_file').agg({
        'bias': ['mean', 'sum'],
        'bias_percentage': 'mean',
        'over_predicted': 'sum',
        'under_predicted': 'sum'
    }).round(2)
    
    print(f"{'Week':<30} {'Avg Bias':<10} {'Total Bias':<12} {'Bias %':<8} {'Over':<6} {'Under':<6}")
    print(f"{'-'*75}")
    
    for week in week_bias.index:
        row = week_bias.loc[week]
        avg_bias = row[('bias', 'mean')]
        total_bias = row[('bias', 'sum')]
        bias_pct = row[('bias_percentage', 'mean')]
        over = row[('over_predicted', 'sum')]
        under = row[('under_predicted', 'sum')]
        
        print(f"{week:<30} {avg_bias:<+10.1f} {total_bias:<+12.1f} {bias_pct:<+8.1f} {over:<6} {under:<6}")
    
    # Identify systematic patterns
    print(f"\n🔍 SYSTEMATIC PATTERN ANALYSIS:")
    
    # Check for day-of-week patterns
    day_patterns = error_df.groupby('day')['bias'].mean()
    print(f"\nDay-of-week bias patterns:")
    for day, bias in day_patterns.items():
        direction = "over-predicts" if bias > 0 else "under-predicts" if bias < 0 else "neutral"
        print(f"  {day}: {bias:+.1f} boxes average ({direction})")
    
    # Check for product patterns
    product_patterns = error_df.groupby('product')['bias'].mean()
    consistent_over = product_patterns[product_patterns > 2].index.tolist()
    consistent_under = product_patterns[product_patterns < -2].index.tolist()
    
    if consistent_over:
        print(f"\nProducts consistently over-predicted (>2 boxes):")
        for product in consistent_over:
            avg_bias = product_patterns[product]
            print(f"  {product}: {avg_bias:+.1f} boxes average")
    
    if consistent_under:
        print(f"\nProducts consistently under-predicted (<-2 boxes):")
        for product in consistent_under:
            avg_bias = product_patterns[product]
            print(f"  {product}: {avg_bias:+.1f} boxes average")
    
    # Check for volume-based patterns
    print(f"\n📊 VOLUME-BASED BIAS PATTERNS:")
    error_df['volume_category'] = pd.cut(error_df['actual_boxes'], 
                                       bins=[0, 10, 50, 100, float('inf')], 
                                       labels=['Low (1-10)', 'Medium (11-50)', 'High (51-100)', 'Very High (100+)'])
    
    volume_bias = error_df.groupby('volume_category')['bias'].mean()
    for category, bias in volume_bias.items():
        direction = "over-predicts" if bias > 0 else "under-predicts" if bias < 0 else "neutral"
        print(f"  {category}: {bias:+.1f} boxes average ({direction})")
    
    return error_df, day_patterns, product_patterns, volume_bias

def create_bias_adjusted_forecaster(error_df, day_patterns, product_patterns):
    """Create a bias-adjusted forecasting method"""
    print(f"\n🔧 CREATING BIAS-ADJUSTED FORECASTER:")
    
    # Calculate adjustment factors
    day_adjustments = {}
    for day, bias in day_patterns.items():
        # If we consistently over-predict, reduce forecast by bias amount
        day_adjustments[day] = -bias
    
    product_adjustments = {}
    for product, bias in product_patterns.items():
        # Only adjust for products with consistent bias > 1 box
        if abs(bias) > 1:
            product_adjustments[product] = -bias
    
    print(f"Day adjustments:")
    for day, adj in day_adjustments.items():
        if abs(adj) > 0.5:
            print(f"  {day}: {adj:+.1f} boxes")
    
    print(f"\nProduct adjustments (for bias > 1 box):")
    for product, adj in product_adjustments.items():
        print(f"  {product}: {adj:+.1f} boxes")
    
    return day_adjustments, product_adjustments

def test_bias_adjusted_forecaster():
    """Test the bias-adjusted forecaster"""
    print(f"\n🧪 TESTING BIAS-ADJUSTED FORECASTER:")
    
    # Run the analysis
    error_df, day_patterns, product_patterns, volume_bias = analyze_error_patterns()
    
    # Create adjustments
    day_adjustments, product_adjustments = create_bias_adjusted_forecaster(error_df, day_patterns, product_patterns)
    
    # Test on a sample week
    from final_forecasting_study import Method1_SimpleAverage
    from egg_packing_predictor_universal import load_all_history, parse_daily_totals_universal
    
    history_df = load_all_history(".")
    method = Method1_SimpleAverage()
    
    # Test on Week 51, 2024 (not in our training set)
    test_file = Path("Week 51 Loading Slip 2024.xlsx")
    if test_file.exists():
        print(f"\nTesting on Week 51, 2024:")
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                continue
            
            # Get base forecast
            base_forecast = method.forecast_weekday(history_df, day, 2024, 51)
            
            # Apply bias adjustments
            adjusted_forecast = base_forecast.copy()
            
            # Apply day adjustment
            if day in day_adjustments:
                day_adj = day_adjustments[day]
                if abs(day_adj) > 0.5:
                    adjusted_forecast['forecast_boxes'] = adjusted_forecast['forecast_boxes'] + day_adj
                    adjusted_forecast['forecast_boxes'] = adjusted_forecast['forecast_boxes'].clip(lower=0)
            
            # Apply product adjustments
            for product, adj in product_adjustments.items():
                mask = adjusted_forecast['product'] == product
                if mask.any():
                    adjusted_forecast.loc[mask, 'forecast_boxes'] += adj
                    adjusted_forecast.loc[mask, 'forecast_boxes'] = adjusted_forecast.loc[mask, 'forecast_boxes'].clip(lower=0)
            
            # Calculate errors
            total_actual = actual_data['boxes'].sum()
            total_base = base_forecast['forecast_boxes'].sum()
            total_adjusted = adjusted_forecast['forecast_boxes'].sum()
            
            base_error = abs(total_base - total_actual) / total_actual * 100 if total_actual > 0 else 0
            adjusted_error = abs(total_adjusted - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            improvement = base_error - adjusted_error
            
            print(f"  {day}: Base {total_base:.0f} ({base_error:.1f}% error) → Adjusted {total_adjusted:.0f} ({adjusted_error:.1f}% error) → {improvement:+.1f}pp improvement")

if __name__ == "__main__":
    test_bias_adjusted_forecaster()
