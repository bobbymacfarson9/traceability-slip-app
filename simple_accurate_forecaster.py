import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history

def simple_accurate_forecast(history, day, target_year, target_week, window=6):
    """
    Simple but accurate forecasting approach:
    1. Use only recent weeks (exclude holidays)
    2. Use median instead of mean (more robust)
    3. Apply conservative adjustments
    """
    # Get historical data for this day
    day_data = history[history["day"] == day].copy()
    
    # Filter to weeks before target
    day_data = day_data[
        (day_data["year"] < target_year) | 
        ((day_data["year"] == target_year) & (day_data["week_num"] < target_week))
    ]
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Identify holiday weeks (zero or very low demand)
    weekly_totals = day_data.groupby(["year", "week_num"])["boxes"].sum().reset_index()
    median_weekly = weekly_totals["boxes"].median()
    holiday_threshold = median_weekly * 0.1  # 10% of median
    
    holiday_weeks = weekly_totals[weekly_totals["boxes"] <= holiday_threshold]
    holiday_set = set(zip(holiday_weeks["year"], holiday_weeks["week_num"]))
    
    # Remove holiday weeks from data
    day_data = day_data[~day_data.apply(
        lambda row: (row["year"], row["week_num"]) in holiday_set, axis=1
    )]
    
    # Get last N weeks of clean data
    day_data = day_data.sort_values(["year", "week_num"]).tail(window)
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Calculate forecasts for each product
    forecasts = []
    for product in day_data["product"].unique():
        if pd.isna(product) or str(product).strip() == "":
            continue
            
        product_data = day_data[day_data["product"] == product]["boxes"]
        
        if len(product_data) == 0:
            continue
            
        # Use median (more robust than mean)
        forecast = product_data.median()
        
        # Apply conservative adjustment: reduce by 10% to avoid over-forecasting
        forecast = forecast * 0.9
        
        # Round to integer
        forecast = max(0, int(round(forecast)))
        
        if forecast > 0:
            forecasts.append({"product": product, "forecast_boxes": forecast})
    
    return pd.DataFrame(forecasts).sort_values("product").reset_index(drop=True)

def test_simple_accuracy():
    """Test the simple but accurate forecasting"""
    history = load_all_history()
    
    print("=== SIMPLE ACCURATE FORECASTING TEST ===")
    print()
    
    # Test multiple weeks
    test_weeks = [20, 21, 22, 23, 24, 25, 26, 29]
    
    total_accuracy = 0
    valid_tests = 0
    
    for week in test_weeks:
        print(f"Testing Week {week}, 2025:")
        
        # Get forecast
        forecast = simple_accurate_forecast(history, "Mon", 2025, week)
        
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
    test_simple_accuracy()
