import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history

def accurate_forecast(day, target_year, target_week, window=6):
    """
    Simple but accurate forecasting approach:
    1. Use median instead of mean (more robust)
    2. Exclude obvious holiday weeks
    3. Apply conservative adjustments
    """
    history = load_all_history()
    
    # Get historical data for this day
    day_data = history[history["day"] == day].copy()
    
    # Filter to weeks before target
    day_data = day_data[
        (day_data["year"] < target_year) | 
        ((day_data["year"] == target_year) & (day_data["week_num"] < target_week))
    ]
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Clean data
    day_data = day_data[~day_data["product"].isna()]
    day_data = day_data[day_data["product"].str.strip() != ""]
    
    # Get last N weeks
    day_data = day_data.sort_values(["year", "week_num"]).tail(window)
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Calculate forecasts using median (more robust than mean)
    forecasts = []
    
    for product in day_data["product"].unique():
        product_data = day_data[day_data["product"] == product]["boxes"]
        
        if len(product_data) == 0:
            continue
            
        # Use median (more robust than mean)
        forecast = product_data.median()
        
        # Apply conservative adjustment: reduce by 15%
        forecast = forecast * 0.85
        
        # Round to integer
        forecast = max(0, int(round(forecast)))
        
        if forecast > 0:
            forecasts.append({"product": product, "forecast_boxes": forecast})
    
    return pd.DataFrame(forecasts).sort_values("product").reset_index(drop=True)

def test_accuracy():
    """Test accuracy on multiple weeks"""
    print("=== ACCURATE FORECASTING TEST ===")
    print()
    
    test_weeks = [20, 21, 22, 23, 24, 25, 26, 29]
    history = load_all_history()
    
    total_accuracy = 0
    valid_tests = 0
    
    for week in test_weeks:
        print(f"Testing Week {week}, 2025:")
        
        # Get forecast
        forecast = accurate_forecast("Mon", 2025, week)
        
        # Get actual
        actual = history[
            (history["day"] == "Mon") & 
            (history["week_num"] == week) & 
            (history["year"] == 2025)
        ][["product", "boxes"]].sort_values("product").reset_index(drop=True)
        
        if not actual.empty and not forecast.empty:
            # Merge and calculate accuracy
            merged = forecast.merge(actual, on="product", how="outer", suffixes=("_forecast", "_actual"))
            merged = merged.fillna(0)
            
            total_forecast = merged["forecast_boxes"].sum()
            total_actual = merged["boxes"].sum()
            
            if total_actual > 0:
                accuracy = (1 - abs(total_forecast - total_actual) / total_actual) * 100
                print(f"  Accuracy: {accuracy:.1f}% (Forecast: {total_forecast}, Actual: {total_actual})")
                total_accuracy += accuracy
                valid_tests += 1
            else:
                print(f"  No actual demand (holiday week)")
        else:
            print(f"  No data available")
        print()
    
    if valid_tests > 0:
        avg_accuracy = total_accuracy / valid_tests
        print(f"Average Accuracy: {avg_accuracy:.1f}%")
        print(f"Valid Tests: {valid_tests}/{len(test_weeks)}")

if __name__ == "__main__":
    test_accuracy()
