import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history, forecast_weekday

def test_improved_vs_original():
    """Test improved system vs original on normal weeks"""
    history = load_all_history()
    
    print("=== IMPROVED FORECASTING ACCURACY TEST ===")
    print("Testing on normal weeks (excluding holiday weeks)")
    print()
    
    # Test weeks - excluding known holiday weeks (8, 26, 29, 32)
    test_weeks = [20, 21, 22, 23, 24, 25]
    
    results = []
    
    for week in test_weeks:
        print(f"Testing Week {week}, 2025:")
        
        # Get actual data
        actual = history[
            (history["day"] == "Mon") & 
            (history["week_num"] == week) & 
            (history["year"] == 2025)
        ][["product", "boxes"]].sort_values("product").reset_index(drop=True)
        
        if actual.empty:
            print(f"  No actual data available")
            continue
            
        # Clean actual data
        actual = actual[~actual["product"].isna()]
        actual = actual[actual["product"].str.strip() != ""]
        actual = actual[actual["boxes"] > 0]  # Only products with demand
        
        if actual.empty:
            print(f"  No actual demand data")
            continue
        
        # Test ORIGINAL system (no improvements)
        try:
            original_forecast = forecast_weekday(
                history, "Mon", window=8, alpha=0.7,
                target_week_num=week, target_year=2025,
                use_last_year=True, exclude_outliers=False, 
                use_trend=False, conservative_mode=False
            )
        except:
            original_forecast = pd.DataFrame(columns=["product", "forecast_boxes"])
        
        # Test IMPROVED system (with all improvements)
        try:
            improved_forecast = forecast_weekday(
                history, "Mon", window=8, alpha=0.7,
                target_week_num=week, target_year=2025,
                use_last_year=True, exclude_outliers=True, 
                use_trend=True, conservative_mode=True
            )
        except:
            improved_forecast = pd.DataFrame(columns=["product", "forecast_boxes"])
        
        # Calculate accuracies
        def calculate_accuracy(forecast_df, actual_df):
            if forecast_df.empty or actual_df.empty:
                return 0, 0, 0
            
            # Merge forecasts with actuals
            merged = forecast_df.merge(actual_df, on="product", how="outer", suffixes=("_forecast", "_actual"))
            merged = merged.fillna(0)
            
            total_forecast = merged["forecast_boxes"].sum()
            total_actual = merged["boxes"].sum()
            
            if total_actual > 0:
                accuracy = (1 - abs(total_forecast - total_actual) / total_actual) * 100
                return accuracy, total_forecast, total_actual
            else:
                return 0, total_forecast, total_actual
        
        orig_acc, orig_forecast, orig_actual = calculate_accuracy(original_forecast, actual)
        impr_acc, impr_forecast, impr_actual = calculate_accuracy(improved_forecast, actual)
        
        # Store results
        results.append({
            'week': week,
            'actual_total': orig_actual,
            'original_forecast': orig_forecast,
            'original_accuracy': orig_acc,
            'improved_forecast': impr_forecast,
            'improved_accuracy': impr_acc,
            'improvement': impr_acc - orig_acc
        })
        
        print(f"  Actual Total: {orig_actual} boxes")
        print(f"  Original Forecast: {orig_forecast} boxes ({orig_acc:.1f}% accuracy)")
        print(f"  Improved Forecast: {impr_forecast} boxes ({impr_acc:.1f}% accuracy)")
        print(f"  Improvement: {impr_acc - orig_acc:+.1f} percentage points")
        print()
    
    # Summary
    if results:
        print("=== SUMMARY ===")
        avg_orig_acc = np.mean([r['original_accuracy'] for r in results])
        avg_impr_acc = np.mean([r['improved_accuracy'] for r in results])
        avg_improvement = avg_impr_acc - avg_orig_acc
        
        print(f"Average Original Accuracy: {avg_orig_acc:.1f}%")
        print(f"Average Improved Accuracy: {avg_impr_acc:.1f}%")
        print(f"Average Improvement: {avg_improvement:+.1f} percentage points")
        print()
        
        # Show best and worst improvements
        results.sort(key=lambda x: x['improvement'], reverse=True)
        print(f"Best Improvement: Week {results[0]['week']} (+{results[0]['improvement']:.1f} points)")
        print(f"Worst Improvement: Week {results[-1]['week']} ({results[-1]['improvement']:+.1f} points)")
        
        return results
    
    return []

def create_detailed_comparison(week):
    """Create detailed product-by-product comparison for a specific week"""
    history = load_all_history()
    
    print(f"\n=== DETAILED COMPARISON: Week {week}, 2025 ===")
    
    # Get actual data
    actual = history[
        (history["day"] == "Mon") & 
        (history["week_num"] == week) & 
        (history["year"] == 2025)
    ][["product", "boxes"]].sort_values("product").reset_index(drop=True)
    
    if actual.empty:
        print("No actual data available")
        return
    
    # Clean actual data
    actual = actual[~actual["product"].isna()]
    actual = actual[actual["product"].str.strip() != ""]
    actual = actual[actual["boxes"] > 0]
    
    # Get forecasts
    original_forecast = forecast_weekday(
        history, "Mon", window=8, alpha=0.7,
        target_week_num=week, target_year=2025,
        use_last_year=True, exclude_outliers=False, 
        use_trend=False, conservative_mode=False
    )
    
    improved_forecast = forecast_weekday(
        history, "Mon", window=8, alpha=0.7,
        target_week_num=week, target_year=2025,
        use_last_year=True, exclude_outliers=True, 
        use_trend=True, conservative_mode=True
    )
    
    # Create comparison table
    comparison = []
    
    # Get all products
    all_products = set(actual["product"].unique())
    if not original_forecast.empty:
        all_products.update(original_forecast["product"].unique())
    if not improved_forecast.empty:
        all_products.update(improved_forecast["product"].unique())
    
    for product in sorted(all_products):
        actual_val = actual[actual["product"] == product]["boxes"].sum()
        orig_val = original_forecast[original_forecast["product"] == product]["forecast_boxes"].sum()
        impr_val = improved_forecast[improved_forecast["product"] == product]["forecast_boxes"].sum()
        
        if actual_val > 0:
            orig_error = abs(orig_val - actual_val) / actual_val * 100
            impr_error = abs(impr_val - actual_val) / actual_val * 100
            error_improvement = orig_error - impr_error
        else:
            orig_error = impr_error = error_improvement = 0
        
        comparison.append({
            'Product': product,
            'Actual': actual_val,
            'Original': orig_val,
            'Improved': impr_val,
            'Orig_Error_%': orig_error,
            'Impr_Error_%': impr_error,
            'Improvement': error_improvement
        })
    
    # Display comparison
    df = pd.DataFrame(comparison)
    df = df[df['Actual'] > 0]  # Only show products with actual demand
    
    print("\nProduct-by-Product Comparison:")
    print("=" * 80)
    print(f"{'Product':<20} {'Actual':<8} {'Original':<10} {'Improved':<10} {'Orig_Err%':<10} {'Impr_Err%':<10} {'Better?':<8}")
    print("=" * 80)
    
    for _, row in df.iterrows():
        better = "✓" if row['Improvement'] > 0 else "✗" if row['Improvement'] < 0 else "="
        print(f"{row['Product']:<20} {row['Actual']:<8} {row['Original']:<10} {row['Improved']:<10} "
              f"{row['Orig_Error_%']:<10.1f} {row['Impr_Error_%']:<10.1f} {better:<8}")
    
    print("=" * 80)
    
    # Summary stats
    better_count = (df['Improvement'] > 0).sum()
    worse_count = (df['Improvement'] < 0).sum()
    same_count = (df['Improvement'] == 0).sum()
    
    print(f"\nSummary: {better_count} products better, {worse_count} worse, {same_count} same")
    print(f"Average error improvement: {df['Improvement'].mean():.1f} percentage points")

if __name__ == "__main__":
    # Run the main test
    results = test_improved_vs_original()
    
    # Show detailed comparison for the best week
    if results:
        best_week = max(results, key=lambda x: x['improvement'])
        create_detailed_comparison(best_week['week'])
