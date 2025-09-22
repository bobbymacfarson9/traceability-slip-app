import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history

def create_clean_verification_excel():
    """Create a clean Excel file for product verification"""
    print("=== CREATING CLEAN VERIFICATION EXCEL ===")
    
    # Test on Week 24, 2025 Monday (we know this has good data)
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print(f"Testing file: {test_file}")
    
    # 1. Parse actual data using universal parser
    print("\n=== PARSING ACTUAL DATA ===")
    actual_data = parse_daily_totals_universal(test_file, "Mon")
    
    if actual_data.empty:
        print("No actual data found for Week 24, 2025 Monday")
        return
    
    print(f"Found {len(actual_data)} products in actual data:")
    for _, row in actual_data.iterrows():
        print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
    
    total_actual = actual_data['boxes'].sum()
    print(f"\nTotal actual boxes: {total_actual}")
    
    # 2. Build historical data and generate forecast
    print("\n=== GENERATING FORECAST ===")
    history_df = load_all_history(".")
    print(f"Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
    
    # Generate forecast
    forecast = forecast_weekday(
        history_df, 
        "Mon", 
        window=8, 
        alpha=0.7,
        target_week_num=24,
        target_year=2025,
        use_last_year=True,
        conservative_mode=True
    )
    
    print(f"Generated forecast for {len(forecast)} products:")
    for _, row in forecast.iterrows():
        print(f"  {row['product']:<30} {row['forecast_boxes']:>6} boxes")
    
    total_forecast = forecast['forecast_boxes'].sum()
    print(f"\nTotal forecast boxes: {total_forecast}")
    
    # 3. Create comprehensive comparison
    print("\n=== CREATING COMPREHENSIVE COMPARISON ===")
    
    # Merge forecast and actuals
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
    
    # Sort by absolute error (largest errors first)
    comparison = comparison.sort_values('abs_error', ascending=False)
    
    # 4. Create detailed Excel file
    print("\n=== CREATING EXCEL FILE ===")
    
    with pd.ExcelWriter('product_verification_week24_2025.xlsx', engine='openpyxl') as writer:
        # Sheet 1: Detailed Comparison
        comparison.to_excel(writer, sheet_name='Forecast_vs_Actual', index=False)
        
        # Sheet 2: Summary Statistics
        summary_data = {
            'Metric': [
                'Total Forecast Boxes',
                'Total Actual Boxes', 
                'Overall Error (%)',
                'Overall Accuracy (%)',
                'Number of Products Forecasted',
                'Number of Products Actual',
                'Products with Perfect Match',
                'Products with >50% Error',
                'Products with >100% Error'
            ],
            'Value': [
                total_forecast,
                total_actual,
                abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0,
                100 - (abs(total_forecast - total_actual) / total_actual * 100) if total_actual > 0 else 0,
                len(forecast),
                len(actual_data),
                len(comparison[comparison['abs_error'] == 0]),
                len(comparison[comparison['pct_error'] > 50]),
                len(comparison[comparison['pct_error'] > 100])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 3: Products by Customer (for verification)
        customer_analysis = []
        for _, row in comparison.iterrows():
            product = row['product']
            if 'Wal' in product or 'Walmart' in product:
                customer = 'Walmart'
            elif 'Lob' in product or 'Loblaws' in product:
                customer = 'Loblaws'
            elif 'Eyk' in product or 'ED' in product or 'Eyking' in product:
                customer = 'Eyking'
            elif 'OC' in product or 'Our Compliments' in product:
                customer = 'Our Compliments'
            else:
                customer = 'Other'
            
            customer_analysis.append({
                'Customer': customer,
                'Product': product,
                'Forecast': row['forecast_boxes'],
                'Actual': row['actual_boxes'],
                'Error': row['abs_error'],
                'Error_%': row['pct_error']
            })
        
        customer_df = pd.DataFrame(customer_analysis)
        customer_df = customer_df.sort_values(['Customer', 'Error'], ascending=[True, False])
        customer_df.to_excel(writer, sheet_name='By_Customer', index=False)
        
        # Sheet 4: Raw Actual Data (for manual verification)
        actual_data_clean = actual_data[['product', 'boxes']].copy()
        actual_data_clean = actual_data_clean.sort_values('product')
        actual_data_clean.to_excel(writer, sheet_name='Raw_Actual_Data', index=False)
        
        # Sheet 5: Raw Forecast Data
        forecast_clean = forecast[['product', 'forecast_boxes']].copy()
        forecast_clean = forecast_clean.rename(columns={'forecast_boxes': 'boxes'})
        forecast_clean = forecast_clean.sort_values('product')
        forecast_clean.to_excel(writer, sheet_name='Raw_Forecast_Data', index=False)
    
    print(f"✅ Excel file created: product_verification_week24_2025.xlsx")
    print(f"\n📊 SUMMARY:")
    print(f"   Total Forecast: {total_forecast:.0f} boxes")
    print(f"   Total Actual: {total_actual:.0f} boxes")
    overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
    print(f"   Overall Error: {overall_error:.1f}%")
    print(f"   Accuracy: {100 - overall_error:.1f}%")
    
    print(f"\n📋 EXCEL FILE CONTENTS:")
    print(f"   Sheet 1: Forecast_vs_Actual - Detailed comparison with errors")
    print(f"   Sheet 2: Summary - Key statistics and metrics")
    print(f"   Sheet 3: By_Customer - Products grouped by customer for verification")
    print(f"   Sheet 4: Raw_Actual_Data - Clean actual data for manual checking")
    print(f"   Sheet 5: Raw_Forecast_Data - Clean forecast data")
    
    return comparison

if __name__ == "__main__":
    create_clean_verification_excel()
