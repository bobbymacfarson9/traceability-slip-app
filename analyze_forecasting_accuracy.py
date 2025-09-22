import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history

def analyze_forecasting_accuracy():
    """Analyze current forecasting accuracy to identify improvement opportunities"""
    print("=== ANALYZING FORECASTING ACCURACY ISSUES ===")
    
    # Load historical data
    history_df = load_all_history(".")
    print(f"Loaded {len(history_df)} records from {history_df['file'].nunique()} files")
    
    # Test on multiple weeks to identify patterns
    test_weeks = [
        ("Week 24 Loading Slip 2025.xlsx", 24, 2025),
        ("Week 32 Loading Slip 2025.xlsx", 32, 2025)
    ]
    
    all_errors = []
    product_analysis = {}
    
    for week_file, week_num, year in test_weeks:
        print(f"\n{'='*60}")
        print(f"ANALYZING {week_file.upper()}")
        print(f"{'='*60}")
        
        test_file = Path(week_file)
        if not test_file.exists():
            print(f"File not found: {week_file}")
            continue
        
        for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
            print(f"\n--- {day.upper()} ---")
            
            # Get actual data
            actual_data = parse_daily_totals_universal(test_file, day)
            if actual_data.empty:
                print(f"No actual data for {day}")
                continue
            
            # Generate forecast
            forecast = forecast_weekday(
                history_df, 
                day, 
                window=8, 
                alpha=0.7,
                target_week_num=week_num,
                target_year=year,
                use_last_year=True,
                conservative_mode=True
            )
            
            # Create comparison
            comparison = forecast.merge(actual_data, on='product', how='outer')
            comparison = comparison.fillna(0)
            comparison = comparison.rename(columns={'boxes': 'actual_boxes'})
            
            # Calculate errors
            comparison['abs_error'] = abs(comparison['forecast_boxes'] - comparison['actual_boxes'])
            comparison['pct_error'] = np.where(
                comparison['actual_boxes'] > 0,
                comparison['abs_error'] / comparison['actual_boxes'] * 100,
                np.where(comparison['forecast_boxes'] > 0, 100, 0)
            )
            
            # Analyze errors
            total_forecast = comparison['forecast_boxes'].sum()
            total_actual = comparison['actual_boxes'].sum()
            overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
            
            print(f"Total Forecast: {total_forecast:.0f} boxes")
            print(f"Total Actual: {total_actual:.0f} boxes")
            print(f"Overall Error: {overall_error:.1f}%")
            
            # Analyze individual product errors
            high_error_products = comparison[comparison['pct_error'] > 50].copy()
            if not high_error_products.empty:
                print(f"\nHigh Error Products (>50% error):")
                for _, row in high_error_products.iterrows():
                    print(f"  {row['product']:<30} Forecast: {row['forecast_boxes']:>3} | Actual: {row['actual_boxes']:>3} | Error: {row['pct_error']:>6.1f}%")
                    
                    # Track product-level analysis
                    product = row['product']
                    if product not in product_analysis:
                        product_analysis[product] = {
                            'total_forecast': 0,
                            'total_actual': 0,
                            'error_count': 0,
                            'high_error_count': 0,
                            'days_seen': set()
                        }
                    
                    product_analysis[product]['total_forecast'] += row['forecast_boxes']
                    product_analysis[product]['total_actual'] += row['actual_boxes']
                    product_analysis[product]['error_count'] += 1
                    if row['pct_error'] > 50:
                        product_analysis[product]['high_error_count'] += 1
                    product_analysis[product]['days_seen'].add(day)
            
            # Track overall errors
            all_errors.append({
                'week': week_file,
                'day': day,
                'total_forecast': total_forecast,
                'total_actual': total_actual,
                'overall_error': overall_error,
                'num_products_forecast': len(forecast),
                'num_products_actual': len(actual_data),
                'high_error_count': len(high_error_products)
            })
    
    # Overall analysis
    print(f"\n{'='*60}")
    print(f"OVERALL FORECASTING ANALYSIS")
    print(f"{'='*60}")
    
    if all_errors:
        avg_error = sum([e['overall_error'] for e in all_errors]) / len(all_errors)
        print(f"Average Overall Error: {avg_error:.1f}%")
        
        # Identify problematic patterns
        high_error_days = [e for e in all_errors if e['overall_error'] > 50]
        if high_error_days:
            print(f"\nHigh Error Days (>50% error):")
            for error in high_error_days:
                print(f"  {error['week']} {error['day']}: {error['overall_error']:.1f}% error")
        
        # Analyze product-level issues
        print(f"\nProduct-Level Analysis:")
        problematic_products = []
        for product, data in product_analysis.items():
            if data['error_count'] > 0:
                avg_product_error = abs(data['total_forecast'] - data['total_actual']) / data['total_actual'] * 100 if data['total_actual'] > 0 else 100
                if avg_product_error > 50 or data['high_error_count'] > 0:
                    problematic_products.append({
                        'product': product,
                        'avg_error': avg_product_error,
                        'high_error_count': data['high_error_count'],
                        'total_forecast': data['total_forecast'],
                        'total_actual': data['total_actual'],
                        'days_seen': len(data['days_seen'])
                    })
        
        if problematic_products:
            print(f"\nMost Problematic Products:")
            problematic_products.sort(key=lambda x: x['avg_error'], reverse=True)
            for product in problematic_products[:10]:  # Top 10
                print(f"  {product['product']:<30} Avg Error: {product['avg_error']:>6.1f}% | High Errors: {product['high_error_count']} | Days: {product['days_seen']}")
    
    # Recommendations
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS FOR IMPROVEMENT")
    print(f"{'='*60}")
    
    print(f"1. 🎯 SEASONAL/HOLIDAY DETECTION:")
    print(f"   - Week 32 shows very low demand (likely holiday)")
    print(f"   - Need to detect and adjust for holiday weeks")
    print(f"   - Consider day-of-week patterns")
    
    print(f"\n2. 📊 PRODUCT-SPECIFIC IMPROVEMENTS:")
    print(f"   - Some products have consistently high errors")
    print(f"   - Need product-specific forecasting models")
    print(f"   - Consider demand volatility by product")
    
    print(f"\n3. 🔄 OUTLIER HANDLING:")
    print(f"   - Better detection of outlier weeks")
    print(f"   - Weighted averaging based on recency")
    print(f"   - Customer-specific demand patterns")
    
    print(f"\n4. 📈 ADVANCED FORECASTING:")
    print(f"   - Trend analysis for growing/declining products")
    print(f"   - Day-of-week seasonality")
    print(f"   - Customer-specific demand patterns")
    
    return all_errors, product_analysis

if __name__ == "__main__":
    analyze_forecasting_accuracy()
