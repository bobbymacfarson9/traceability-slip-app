import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history

def create_features(history, day, target_year, target_week):
    """Create features for machine learning approach"""
    # Get historical data
    day_data = history[history["day"] == day].copy()
    day_data = day_data[
        (day_data["year"] < target_year) | 
        ((day_data["year"] == target_year) & (day_data["week_num"] < target_week))
    ]
    
    if day_data.empty:
        return pd.DataFrame()
    
    # Create weekly totals
    weekly_totals = day_data.groupby(["year", "week_num"])["boxes"].sum().reset_index()
    weekly_totals = weekly_totals.sort_values(["year", "week_num"])
    
    # Create features
    features = []
    for i in range(len(weekly_totals)):
        if i < 3:  # Need at least 3 weeks of history
            continue
            
        # Target (current week)
        target = weekly_totals.iloc[i]["boxes"]
        
        # Features (last 3 weeks)
        last_3_weeks = weekly_totals.iloc[i-3:i]["boxes"].values
        
        # Additional features
        mean_3_weeks = np.mean(last_3_weeks)
        std_3_weeks = np.std(last_3_weeks) if len(last_3_weeks) > 1 else 0
        trend = last_3_weeks[-1] - last_3_weeks[0] if len(last_3_weeks) > 1 else 0
        
        features.append({
            "week_1": last_3_weeks[0],
            "week_2": last_3_weeks[1], 
            "week_3": last_3_weeks[2],
            "mean_3": mean_3_weeks,
            "std_3": std_3_weeks,
            "trend": trend,
            "target": target
        })
    
    return pd.DataFrame(features)

def smart_forecast(history, day, target_year, target_week):
    """Smart forecasting using pattern recognition"""
    # Get recent data
    day_data = history[history["day"] == day].copy()
    day_data = day_data[
        (day_data["year"] < target_year) | 
        ((day_data["year"] == target_year) & (day_data["week_num"] < target_week))
    ]
    
    if day_data.empty:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Get last 4 weeks of data
    day_data = day_data.sort_values(["year", "week_num"]).tail(4)
    
    if len(day_data) < 2:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Calculate weekly totals
    weekly_totals = day_data.groupby(["year", "week_num"])["boxes"].sum().reset_index()
    weekly_totals = weekly_totals.sort_values(["year", "week_num"])
    
    if len(weekly_totals) < 2:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    # Pattern recognition
    recent_totals = weekly_totals["boxes"].values
    
    # Method 1: Simple average
    simple_avg = np.mean(recent_totals)
    
    # Method 2: Weighted average (more recent = higher weight)
    weights = np.linspace(0.3, 1.0, len(recent_totals))
    weighted_avg = np.average(recent_totals, weights=weights)
    
    # Method 3: Trend projection
    if len(recent_totals) >= 2:
        trend = recent_totals[-1] - recent_totals[0]
        trend_projection = recent_totals[-1] + trend * 0.5
    else:
        trend_projection = simple_avg
    
    # Method 4: Median (robust)
    median_val = np.median(recent_totals)
    
    # Choose the most conservative estimate
    base_forecast = min(simple_avg, weighted_avg, trend_projection, median_val)
    
    # Apply safety margin (reduce by 15% to avoid over-forecasting)
    total_forecast = base_forecast * 0.85
    
    # Distribute forecast across products based on historical proportions
    # Get product proportions from recent weeks
    recent_products = day_data.groupby("product")["boxes"].sum()
    total_recent = recent_products.sum()
    
    if total_recent == 0:
        return pd.DataFrame(columns=["product", "forecast_boxes"])
    
    forecasts = []
    for product, recent_boxes in recent_products.items():
        if pd.isna(product) or str(product).strip() == "":
            continue
            
        # Calculate proportion
        proportion = recent_boxes / total_recent
        
        # Apply proportion to total forecast
        product_forecast = total_forecast * proportion
        
        # Round to integer
        product_forecast = max(0, int(round(product_forecast)))
        
        if product_forecast > 0:
            forecasts.append({"product": product, "forecast_boxes": product_forecast})
    
    return pd.DataFrame(forecasts).sort_values("product").reset_index(drop=True)

def test_ml_accuracy():
    """Test the ML-based forecasting accuracy"""
    history = load_all_history()
    
    print("=== ML-BASED FORECASTING ACCURACY TEST ===")
    print()
    
    # Test multiple weeks
    test_weeks = [20, 21, 22, 23, 24, 25, 26, 29]
    
    total_accuracy = 0
    valid_tests = 0
    
    for week in test_weeks:
        print(f"Testing Week {week}, 2025:")
        
        # Get forecast
        forecast = smart_forecast(history, "Mon", 2025, week)
        
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
    test_ml_accuracy()
