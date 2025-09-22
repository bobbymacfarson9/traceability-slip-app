import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history
from smart_bias_forecaster import HybridForecaster

def analyze_problematic_products():
    """Analyze why specific products are problematic and find solutions"""
    print("=== ANALYZING PROBLEMATIC PRODUCTS ===")
    
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
    
    # Focus on the most problematic products
    problematic_products = ['ED 18 LG', 'ED 18 XL', 'Wal GV Lg', 'Lob Lg', 'OC 30 Lrg']
    
    print(f"Analyzing {len(problematic_products)} most problematic products:")
    for product in problematic_products:
        print(f"  - {product}")
    
    # Analyze each problematic product
    for product in problematic_products:
        print(f"\n{'='*80}")
        print(f"ANALYZING: {product}")
        print(f"{'='*80}")
        
        # Get historical data for this product
        product_history = history_df[history_df['product'] == product].copy()
        
        if product_history.empty:
            print(f"❌ No historical data found for {product}")
            continue
        
        print(f"📊 Historical data: {len(product_history)} records")
        
        # Analyze by day of week
        print(f"\n📅 Historical demand by day of week:")
        day_analysis = product_history.groupby('day').agg({
            'boxes': ['count', 'mean', 'std', 'min', 'max']
        }).round(1)
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            if day in day_analysis.index:
                row = day_analysis.loc[day]
                count = row[('boxes', 'count')]
                mean = row[('boxes', 'mean')]
                std = row[('boxes', 'std')]
                min_val = row[('boxes', 'min')]
                max_val = row[('boxes', 'max')]
                
                print(f"  {day}: {count} records, avg: {mean:.1f}, std: {std:.1f}, range: {min_val}-{max_val}")
        
        # Analyze demand patterns
        print(f"\n📈 Demand pattern analysis:")
        
        # Check for trends over time
        product_history_sorted = product_history.sort_values(['year', 'week_num'])
        recent_weeks = product_history_sorted.tail(10)
        older_weeks = product_history_sorted.head(10)
        
        if len(recent_weeks) > 0 and len(older_weeks) > 0:
            recent_avg = recent_weeks['boxes'].mean()
            older_avg = older_weeks['boxes'].mean()
            trend = recent_avg - older_avg
            
            print(f"  Recent 10 weeks avg: {recent_avg:.1f} boxes")
            print(f"  Older 10 weeks avg: {older_avg:.1f} boxes")
            print(f"  Trend: {trend:+.1f} boxes ({'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable'})")
        
        # Check for volatility
        volatility = product_history['boxes'].std() / product_history['boxes'].mean() if product_history['boxes'].mean() > 0 else 0
        print(f"  Volatility (CV): {volatility:.2f} ({'high' if volatility > 0.5 else 'medium' if volatility > 0.3 else 'low'})")
        
        # Check for zero demand weeks
        zero_weeks = (product_history['boxes'] == 0).sum()
        print(f"  Zero demand weeks: {zero_weeks} ({zero_weeks/len(product_history)*100:.1f}%)")
        
        # Analyze forecasting errors for this product
        print(f"\n🔍 Forecasting error analysis:")
        
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
                
                # Find this product in actual data
                actual_row = actual_data[actual_data['product'] == product]
                if actual_row.empty:
                    continue
                
                actual_boxes = actual_row['boxes'].iloc[0]
                
                # Get forecast
                forecast_data = method.forecast_weekday(history_df, day, year, week_num)
                forecast_row = forecast_data[forecast_data['product'] == product]
                
                if forecast_row.empty:
                    forecast_boxes = 0
                else:
                    forecast_boxes = forecast_row['forecast_boxes'].iloc[0]
                
                error = forecast_boxes - actual_boxes
                error_pct = (error / actual_boxes * 100) if actual_boxes > 0 else 0
                
                error_data.append({
                    'week_file': week_file,
                    'day': day,
                    'actual': actual_boxes,
                    'forecast': forecast_boxes,
                    'error': error,
                    'error_pct': error_pct
                })
        
        if error_data:
            error_df = pd.DataFrame(error_data)
            
            print(f"  Test errors: {len(error_df)} predictions")
            print(f"  Average error: {error_df['error'].mean():+.1f} boxes")
            print(f"  Average error %: {error_df['error_pct'].mean():+.1f}%")
            print(f"  Error std: {error_df['error'].std():.1f} boxes")
            
            # Analyze errors by day
            print(f"  Errors by day:")
            day_errors = error_df.groupby('day')['error'].mean()
            for day, error in day_errors.items():
                print(f"    {day}: {error:+.1f} boxes average")
            
            # Show worst errors
            print(f"  Worst errors:")
            worst_errors = error_df.nlargest(3, 'error_pct')
            for _, row in worst_errors.iterrows():
                print(f"    {row['week_file']} {row['day']}: Actual {row['actual']}, Forecast {row['forecast']}, Error {row['error']:+.0f} ({row['error_pct']:+.1f}%)")
        
        # Identify root causes
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        # Check if product has irregular demand patterns
        if volatility > 0.5:
            print(f"  ❌ High volatility - demand is very inconsistent")
        
        if zero_weeks > len(product_history) * 0.2:
            print(f"  ❌ Many zero demand weeks - product may be seasonal or irregular")
        
        # Check if product has day-specific patterns
        day_means = product_history.groupby('day')['boxes'].mean()
        day_std = day_means.std()
        if day_std > day_means.mean() * 0.3:
            print(f"  ❌ Strong day-of-week patterns - demand varies significantly by day")
        
        # Check if product has trend issues
        if abs(trend) > product_history['boxes'].mean() * 0.2:
            print(f"  ❌ Strong trend - demand is changing over time")
        
        # Provide specific recommendations
        print(f"\n💡 SPECIFIC RECOMMENDATIONS FOR {product}:")
        
        if volatility > 0.5:
            print(f"  - Use longer historical window (8-10 weeks instead of 6)")
            print(f"  - Apply volatility-based adjustments")
        
        if zero_weeks > len(product_history) * 0.2:
            print(f"  - Detect and handle zero-demand weeks as outliers")
            print(f"  - Use median instead of mean for more robust forecasting")
        
        if day_std > day_means.mean() * 0.3:
            print(f"  - Implement day-specific forecasting models")
            print(f"  - Use day-of-week adjustments")
        
        if abs(trend) > product_history['boxes'].mean() * 0.2:
            print(f"  - Apply trend adjustments")
            print(f"  - Use weighted averages favoring recent weeks")
        
        # Check if product is missing from forecasts
        missing_count = 0
        for week_info in test_weeks:
            week_num = week_info['week_num']
            year = week_info['year']
            
            for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
                forecast_data = method.forecast_weekday(history_df, day, year, week_num)
                if forecast_data[forecast_data['product'] == product].empty:
                    missing_count += 1
        
        if missing_count > 0:
            print(f"  - Product missing from {missing_count} forecasts - check historical data availability")
    
    return problematic_products

def create_targeted_solutions():
    """Create targeted solutions for problematic products"""
    print(f"\n{'='*80}")
    print(f"TARGETED SOLUTIONS FOR PROBLEMATIC PRODUCTS")
    print(f"{'='*80}")
    
    # Analyze the problematic products
    problematic_products = analyze_problematic_products()
    
    print(f"\n🔧 IMPLEMENTATION STRATEGY:")
    print(f"1. Product-specific adjustments for high-volatility products")
    print(f"2. Day-specific models for products with strong day patterns")
    print(f"3. Trend adjustments for products with changing demand")
    print(f"4. Outlier detection for products with many zero weeks")
    print(f"5. Extended historical windows for volatile products")
    
    print(f"\n📋 SPECIFIC ACTIONS:")
    print(f"- ED 18 LG: Implement volatility-based adjustments and longer historical window")
    print(f"- ED 18 XL: Apply trend adjustments and day-specific models")
    print(f"- Wal GV Lg: Use median-based forecasting and outlier detection")
    print(f"- Lob Lg: Implement day-specific adjustments")
    print(f"- OC 30 Lrg: Apply trend adjustments and volatility handling")
    
    return problematic_products

if __name__ == "__main__":
    create_targeted_solutions()
