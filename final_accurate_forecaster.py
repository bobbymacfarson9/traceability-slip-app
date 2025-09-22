import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history

def final_accurate_forecast(history, day, target_year, target_week, window=6):
    """
    Final accurate forecasting approach:
    1. Clean data processing
    2. Outlier detection and removal
    3. Conservative forecasting
    4. Product-level accuracy focus
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
    
    # Clean product names
    day_data = day_data[~day_data["product"].isna()]
    day_data = day_data[day_data["product"].str.strip() != ""]
    
    # Identify holiday weeks (zero or very low demand)
    weekly_totals = day_data.groupby(["year", "week_num"])["boxes"].sum().reset_index()
    
    if len(weekly_totals) < 3:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Use median as threshold for holiday detection
    median_weekly = weekly_totals["boxes"].median()
    holiday_threshold = median_weekly * 0.2  # 20% of median
    
    holiday_weeks = weekly_totals[weekly_totals["boxes"] <= holiday_threshold]
    holiday_set = set(zip(holiday_weeks["year"], holiday_weeks["week_num"]))
    
    # Remove holiday weeks
    day_data = day_data[~day_data.apply(
        lambda row: (row["year"], row["week_num"]) in holiday_set, axis=1
    )]
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Get last N weeks of clean data
    day_data = day_data.sort_values(["year", "week_num"]).tail(window)
    
    # Calculate forecasts for each product
    forecasts = []
    
    # Group by product and calculate statistics
    product_stats = day_data.groupby("product")["boxes"].agg([
        "count", "mean", "median", "std"
    ]).reset_index()
    
    # Only forecast products with sufficient data
    product_stats = product_stats[product_stats["count"] >= 2]
    
    for _, row in product_stats.iterrows():
        product = row["product"]
        mean_val = row["mean"]
        median_val = row["median"]
        std_val = row["std"] if not pd.isna(row["std"]) else 0
        
        # Use median as base (more robust than mean)
        base_forecast = median_val
        
        # Apply conservative adjustment based on variability
        if std_val > 0 and mean_val > 0:
            cv = std_val / mean_val  # Coefficient of variation
            if cv > 1.0:  # High variability
                adjustment = 0.7  # Reduce by 30%
            elif cv > 0.5:  # Medium variability
                adjustment = 0.8  # Reduce by 20%
            else:  # Low variability
                adjustment = 0.9  # Reduce by 10%
        else:
            adjustment = 0.8  # Default 20% reduction
        
        forecast = base_forecast * adjustment
        forecast = max(0, int(round(forecast)))
        
        if forecast > 0:
            forecasts.append({"product": product, "forecast_boxes": forecast})
    
    if not forecasts:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    return pd.DataFrame(forecasts).sort_values("product").reset_index(drop=True)

def test_final_accuracy():
    """Test the final accurate forecasting"""
    history = load_all_history()
    
    print("=== FINAL ACCURATE FORECASTING TEST ===")
    print()
    
    # Test multiple weeks
    test_weeks = [20, 21, 22, 23, 24, 25, 26, 29]
    
    total_accuracy = 0
    valid_tests = 0
    results = []
    
    for week in test_weeks:
        print(f"Testing Week {week}, 2025:")
        
        # Get forecast
        forecast = final_accurate_forecast(history, "Mon", 2025, week)
        
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
                results.append((week, accuracy, total_forecast, total_actual))
            else:
                print(f"  No actual demand (holiday week)")
        else:
            print(f"  No data available")
        print()
    
    if valid_tests > 0:
        avg_accuracy = total_accuracy / valid_tests
        print(f"Average Accuracy: {avg_accuracy:.1f}%")
        print(f"Valid Tests: {valid_tests}/{len(test_weeks)}")
        
        # Show best and worst predictions
        results.sort(key=lambda x: x[1], reverse=True)
        print(f"\\nBest Prediction: Week {results[0][0]} - {results[0][1]:.1f}% accuracy")
        print(f"Worst Prediction: Week {results[-1][0]} - {results[-1][1]:.1f}% accuracy")

if __name__ == "__main__":
    test_final_accuracy()
