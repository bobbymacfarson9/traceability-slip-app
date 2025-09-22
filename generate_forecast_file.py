from egg_packing_predictor import load_all_history, forecast_weekday
import pandas as pd
from pathlib import Path

def generate_forecast_file(target_week, target_year):
    """Generate day-by-day forecasts for a specific week and save to CSV"""
    history = load_all_history()
    
    print(f"Generating forecasts for Week {target_week}, {target_year}")
    print("=" * 60)
    
    all_forecasts = []
    
    # Generate forecasts for each day (Mon-Fri)
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        print(f"\nForecasting {day}...")
        
        # Get improved forecast
        forecast = forecast_weekday(
            history, day, window=8, alpha=0.7,
            target_week_num=target_week, target_year=target_year,
            use_last_year=True, exclude_outliers=True, 
            use_trend=True, conservative_mode=True
        )
        
        if not forecast.empty:
            # Add day and week info
            forecast['day'] = day
            forecast['week'] = target_week
            forecast['year'] = target_year
            
            # Reorder columns
            forecast = forecast[['week', 'year', 'day', 'product', 'forecast_boxes']]
            
            all_forecasts.append(forecast)
            
            print(f"  {len(forecast)} products forecasted")
            print(f"  Total forecast: {forecast['forecast_boxes'].sum()} boxes")
        else:
            print(f"  No forecast data available")
    
    if all_forecasts:
        # Combine all forecasts
        combined_forecast = pd.concat(all_forecasts, ignore_index=True)
        
        # Save to CSV
        filename = f"forecast_week_{target_week}_{target_year}.csv"
        combined_forecast.to_csv(filename, index=False)
        
        print(f"\nForecast saved to: {filename}")
        print(f"Total products forecasted: {len(combined_forecast)}")
        print(f"Total boxes forecasted: {combined_forecast['forecast_boxes'].sum()}")
        
        # Show summary by day
        print("\nSUMMARY BY DAY:")
        print("-" * 40)
        summary = combined_forecast.groupby('day')['forecast_boxes'].agg(['count', 'sum']).reset_index()
        summary.columns = ['Day', 'Products', 'Total_Boxes']
        
        for _, row in summary.iterrows():
            print(f"{row['Day']:<8} {row['Products']:>3} products, {row['Total_Boxes']:>6} boxes")
        
        return filename
    else:
        print("No forecasts generated!")
        return None

def show_forecast_preview(filename):
    """Show a preview of the generated forecast file"""
    if filename and Path(filename).exists():
        df = pd.read_csv(filename)
        
        print(f"\nPREVIEW OF {filename}:")
        print("=" * 80)
        
        # Show first few rows
        print("First 20 rows:")
        print(df.head(20).to_string(index=False))
        
        print(f"\nTotal rows: {len(df)}")
        print(f"Days covered: {df['day'].unique()}")
        print(f"Products: {df['product'].nunique()}")

if __name__ == "__main__":
    # Generate forecast for next week (you can change this)
    target_week = 30  # Change this to the week you want to forecast
    target_year = 2025
    
    filename = generate_forecast_file(target_week, target_year)
    
    if filename:
        show_forecast_preview(filename)
        
        print(f"\nYou can now:")
        print(f"1. Open {filename} in Excel to review the forecasts")
        print(f"2. Compare with actual data when available")
        print(f"3. Verify the calculations are correct")
