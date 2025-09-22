import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, forecast_weekday, load_all_history

def create_full_week_verification():
    """Create a comprehensive Excel file with all days (Mon-Fri) for verification"""
    print("=== CREATING FULL WEEK VERIFICATION EXCEL ===")
    
    # Test on Week 24, 2025 - all days
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print(f"Testing file: {test_file}")
    
    # Build historical data
    print("\n=== BUILDING HISTORICAL DATASET ===")
    history_df = load_all_history(".")
    print(f"Built historical dataset: {len(history_df)} records from {history_df['file'].nunique()} files")
    
    # Process each day
    all_comparisons = []
    daily_summaries = []
    
    for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
        print(f"\n=== PROCESSING {day.upper()} ===")
        
        # 1. Parse actual data
        actual_data = parse_daily_totals_universal(test_file, day)
        
        if actual_data.empty:
            print(f"No actual data found for {day}")
            continue
        
        print(f"Found {len(actual_data)} products in actual data:")
        for _, row in actual_data.iterrows():
            print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
        
        total_actual = actual_data['boxes'].sum()
        print(f"Total actual boxes: {total_actual}")
        
        # 2. Generate forecast
        forecast = forecast_weekday(
            history_df, 
            day, 
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
        print(f"Total forecast boxes: {total_forecast}")
        
        # 3. Create comparison
        comparison = forecast.merge(actual_data, on='product', how='outer')
        comparison = comparison.fillna(0)
        comparison = comparison.rename(columns={'boxes': 'actual_boxes'})
        comparison['day'] = day
        
        # Calculate errors
        comparison['abs_error'] = abs(comparison['forecast_boxes'] - comparison['actual_boxes'])
        comparison['pct_error'] = np.where(
            comparison['actual_boxes'] > 0,
            comparison['abs_error'] / comparison['actual_boxes'] * 100,
            np.where(comparison['forecast_boxes'] > 0, 100, 0)
        )
        
        # Calculate overall accuracy for this day
        overall_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 0
        accuracy = 100 - overall_error
        
        print(f"Day accuracy: {accuracy:.1f}%")
        
        # Store comparison
        all_comparisons.append(comparison)
        
        # Store daily summary
        daily_summaries.append({
            'Day': day,
            'Total_Forecast': total_forecast,
            'Total_Actual': total_actual,
            'Overall_Error_%': overall_error,
            'Accuracy_%': accuracy,
            'Products_Forecast': len(forecast),
            'Products_Actual': len(actual_data),
            'Perfect_Matches': len(comparison[comparison['abs_error'] == 0]),
            'High_Error_Products': len(comparison[comparison['pct_error'] > 50])
        })
    
    # 4. Create comprehensive Excel file
    print(f"\n=== CREATING COMPREHENSIVE EXCEL FILE ===")
    
    with pd.ExcelWriter('full_week_verification_week24_2025.xlsx', engine='openpyxl') as writer:
        # Sheet 1: Daily Summary
        summary_df = pd.DataFrame(daily_summaries)
        summary_df.to_excel(writer, sheet_name='Daily_Summary', index=False)
        
        # Sheet 2: All Days Combined Comparison
        if all_comparisons:
            combined_comparison = pd.concat(all_comparisons, ignore_index=True)
            combined_comparison = combined_comparison.sort_values(['day', 'abs_error'], ascending=[True, False])
            combined_comparison.to_excel(writer, sheet_name='All_Days_Comparison', index=False)
        
        # Individual day sheets
        for i, comparison in enumerate(all_comparisons):
            day = comparison['day'].iloc[0]
            comparison_clean = comparison.drop('day', axis=1)
            comparison_clean = comparison_clean.sort_values('abs_error', ascending=False)
            comparison_clean.to_excel(writer, sheet_name=f'{day}_Details', index=False)
        
        # Sheet: Products by Customer (all days)
        customer_analysis = []
        for comparison in all_comparisons:
            day = comparison['day'].iloc[0]
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
                    'Day': day,
                    'Customer': customer,
                    'Product': product,
                    'Forecast': row['forecast_boxes'],
                    'Actual': row['actual_boxes'],
                    'Error': row['abs_error'],
                    'Error_%': row['pct_error']
                })
        
        if customer_analysis:
            customer_df = pd.DataFrame(customer_analysis)
            customer_df = customer_df.sort_values(['Day', 'Customer', 'Error'], ascending=[True, True, False])
            customer_df.to_excel(writer, sheet_name='By_Customer_All_Days', index=False)
        
        # Sheet: Raw Actual Data (all days)
        all_actual_data = []
        for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
            actual_data = parse_daily_totals_universal(test_file, day)
            if not actual_data.empty:
                actual_data['day'] = day
                all_actual_data.append(actual_data[['day', 'product', 'boxes']])
        
        if all_actual_data:
            raw_actual_df = pd.concat(all_actual_data, ignore_index=True)
            raw_actual_df = raw_actual_df.sort_values(['day', 'product'])
            raw_actual_df.to_excel(writer, sheet_name='Raw_Actual_All_Days', index=False)
    
    print(f"✅ Comprehensive Excel file created: full_week_verification_week24_2025.xlsx")
    
    # Print overall summary
    print(f"\n📊 WEEKLY SUMMARY:")
    total_forecast_all = sum([s['Total_Forecast'] for s in daily_summaries])
    total_actual_all = sum([s['Total_Actual'] for s in daily_summaries])
    overall_weekly_error = abs(total_forecast_all - total_actual_all) / total_actual_all * 100 if total_actual_all > 0 else 0
    
    print(f"   Total Forecast (All Days): {total_forecast_all:.0f} boxes")
    print(f"   Total Actual (All Days): {total_actual_all:.0f} boxes")
    print(f"   Overall Weekly Error: {overall_weekly_error:.1f}%")
    print(f"   Overall Weekly Accuracy: {100 - overall_weekly_error:.1f}%")
    
    print(f"\n📋 DAILY BREAKDOWN:")
    for summary in daily_summaries:
        print(f"   {summary['Day']}: {summary['Accuracy_%']:.1f}% accuracy ({summary['Total_Forecast']:.0f} vs {summary['Total_Actual']:.0f} boxes)")
    
    print(f"\n📋 EXCEL FILE CONTENTS:")
    print(f"   Sheet 1: Daily_Summary - Accuracy summary for each day")
    print(f"   Sheet 2: All_Days_Comparison - Combined comparison of all days")
    print(f"   Sheet 3-7: Mon_Details, Tues_Details, etc. - Individual day details")
    print(f"   Sheet 8: By_Customer_All_Days - Products grouped by customer across all days")
    print(f"   Sheet 9: Raw_Actual_All_Days - Clean actual data for all days")
    
    return daily_summaries

if __name__ == "__main__":
    create_full_week_verification()
