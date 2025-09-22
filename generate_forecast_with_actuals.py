from egg_packing_predictor import load_all_history, forecast_weekday
import pandas as pd
from pathlib import Path

def generate_forecast_with_actuals(target_week, target_year):
    """Generate forecasts with actual data and differences for verification"""
    history = load_all_history()
    
    print(f"Generating forecasts with actuals for Week {target_week}, {target_year}")
    print("=" * 70)
    
    all_data = []
    
    # Generate forecasts for each day (Mon-Fri)
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        print(f"\nProcessing {day}...")
        
        # Get improved forecast
        forecast = forecast_weekday(
            history, day, window=8, alpha=0.7,
            target_week_num=target_week, target_year=target_year,
            use_last_year=True, exclude_outliers=True, 
            use_trend=True, conservative_mode=True
        )
        
        # Get actual data
        actual = history[
            (history['day'] == day) & 
            (history['week_num'] == target_week) & 
            (history['year'] == target_year)
        ][['product', 'boxes']].sort_values('product').reset_index(drop=True)
        
        if not forecast.empty:
            # Add day and week info to forecast
            forecast['day'] = day
            forecast['week'] = target_week
            forecast['year'] = target_year
            
            # Merge forecast with actual data
            merged = forecast.merge(actual, on='product', how='outer', suffixes=('_forecast', '_actual'))
            merged = merged.fillna(0)
            
            # Rename columns for clarity
            merged = merged.rename(columns={'boxes': 'actual_boxes'})
            
            # Calculate differences
            merged['difference'] = merged['forecast_boxes'] - merged['actual_boxes']
            merged['abs_difference'] = abs(merged['difference'])
            merged['percent_error'] = 0.0
            
            # Calculate percentage error (only for products with actual demand)
            for idx, row in merged.iterrows():
                if row['actual_boxes'] > 0:
                    merged.at[idx, 'percent_error'] = abs(row['difference']) / row['actual_boxes'] * 100
            
            # Reorder columns
            merged = merged[['week', 'year', 'day', 'product', 'forecast_boxes', 'actual_boxes', 'difference', 'abs_difference', 'percent_error']]
            
            all_data.append(merged)
            
            # Show summary for this day
            total_forecast = merged['forecast_boxes'].sum()
            total_actual = merged['actual_boxes'].sum()
            total_diff = total_forecast - total_actual
            
            print(f"  Forecast: {total_forecast:>6} boxes")
            print(f"  Actual:   {total_actual:>6} boxes")
            print(f"  Difference: {total_diff:>+6} boxes")
            
            if total_actual > 0:
                accuracy = (1 - abs(total_diff) / total_actual) * 100
                print(f"  Accuracy: {accuracy:>6.1f}%")
        else:
            print(f"  No forecast data available")
    
    if all_data:
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Save to CSV
        filename = f"forecast_vs_actual_week_{target_week}_{target_year}.csv"
        combined_data.to_csv(filename, index=False)
        
        print(f"\nData saved to: {filename}")
        print(f"Total rows: {len(combined_data)}")
        
        # Show overall summary
        print("\nOVERALL SUMMARY:")
        print("-" * 50)
        total_forecast = combined_data['forecast_boxes'].sum()
        total_actual = combined_data['actual_boxes'].sum()
        total_diff = total_forecast - total_actual
        
        print(f"Total Forecast: {total_forecast:>8} boxes")
        print(f"Total Actual:   {total_actual:>8} boxes")
        print(f"Total Difference: {total_diff:>+8} boxes")
        
        if total_actual > 0:
            overall_accuracy = (1 - abs(total_diff) / total_actual) * 100
            print(f"Overall Accuracy: {overall_accuracy:>6.1f}%")
        
        # Show summary by day
        print("\nSUMMARY BY DAY:")
        print("-" * 60)
        print(f"{'Day':<8} {'Forecast':<10} {'Actual':<10} {'Difference':<12} {'Accuracy':<10}")
        print("-" * 60)
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            day_data = combined_data[combined_data['day'] == day]
            if not day_data.empty:
                day_forecast = day_data['forecast_boxes'].sum()
                day_actual = day_data['actual_boxes'].sum()
                day_diff = day_forecast - day_actual
                
                if day_actual > 0:
                    day_accuracy = (1 - abs(day_diff) / day_actual) * 100
                    accuracy_str = f"{day_accuracy:.1f}%"
                else:
                    accuracy_str = "N/A"
                
                print(f"{day:<8} {day_forecast:<10} {day_actual:<10} {day_diff:+<12} {accuracy_str:<10}")
        
        return filename
    else:
        print("No data generated!")
        return None

def show_data_preview(filename):
    """Show a preview of the generated data file"""
    if filename and Path(filename).exists():
        df = pd.read_csv(filename)
        
        print(f"\nPREVIEW OF {filename}:")
        print("=" * 100)
        
        # Show first 20 rows
        print("First 20 rows:")
        print(df.head(20).to_string(index=False))
        
        print(f"\nFile contains:")
        print(f"- Total rows: {len(df)}")
        print(f"- Days: {df['day'].unique()}")
        print(f"- Products: {df['product'].nunique()}")
        print(f"- Columns: {list(df.columns)}")

if __name__ == "__main__":
    # Generate forecast with actuals for Week 24, 2025 (has actual data)
    target_week = 24
    target_year = 2025
    
    filename = generate_forecast_with_actuals(target_week, target_year)
    
    if filename:
        show_data_preview(filename)
        
        print(f"\nYou can now:")
        print(f"1. Open {filename} in Excel to review the data")
        print(f"2. Verify the calculations in the 'difference' and 'percent_error' columns")
        print(f"3. Check that forecast - actual = difference")
        print(f"4. Verify percent_error = abs(difference) / actual * 100")
