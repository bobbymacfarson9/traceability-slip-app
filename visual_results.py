import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor import load_all_history, forecast_weekday

def create_visual_summary():
    """Create a visual summary of the accuracy improvements"""
    
    print("=" * 80)
    print("                    EGG ROOM PACKING PREDICTOR")
    print("                    ACCURACY IMPROVEMENT TEST")
    print("=" * 80)
    print()
    
    # Test data
    test_results = [
        {'week': 20, 'actual': 1770, 'original': 1168, 'improved': 843, 'orig_acc': 66.0, 'impr_acc': 47.6, 'improvement': -18.4},
        {'week': 21, 'actual': 440, 'original': 865, 'improved': 657, 'orig_acc': 3.4, 'impr_acc': 50.7, 'improvement': 47.3},
        {'week': 22, 'actual': 921, 'original': 666, 'improved': 510, 'orig_acc': 72.3, 'impr_acc': 55.4, 'improvement': -16.9},
        {'week': 23, 'actual': 822, 'original': 649, 'improved': 500, 'orig_acc': 79.0, 'impr_acc': 60.8, 'improvement': -18.1},
        {'week': 24, 'actual': 316, 'original': 695, 'improved': 525, 'orig_acc': -19.9, 'impr_acc': 33.9, 'improvement': 53.8},
        {'week': 25, 'actual': 606, 'original': 669, 'improved': 525, 'orig_acc': 89.6, 'impr_acc': 86.6, 'improvement': -3.0}
    ]
    
    # Create visual table
    print("WEEK-BY-WEEK ACCURACY COMPARISON")
    print("-" * 80)
    print(f"{'Week':<6} {'Actual':<8} {'Original':<10} {'Improved':<10} {'Orig%':<8} {'Impr%':<8} {'Change':<8}")
    print("-" * 80)
    
    for result in test_results:
        change_str = f"{result['improvement']:+.1f}"
        print(f"Week {result['week']:<2} {result['actual']:<8} {result['original']:<10} {result['improved']:<10} "
              f"{result['orig_acc']:<8.1f} {result['impr_acc']:<8.1f} {change_str:<8}")
    
    print("-" * 80)
    
    # Calculate averages
    avg_orig = np.mean([r['orig_acc'] for r in test_results])
    avg_impr = np.mean([r['impr_acc'] for r in test_results])
    avg_improvement = avg_impr - avg_orig
    
    print(f"{'AVG':<6} {'':<8} {'':<10} {'':<10} {avg_orig:<8.1f} {avg_impr:<8.1f} {avg_improvement:+.1f}")
    print()
    
    # Key insights
    print("KEY INSIGHTS:")
    print("• Improved system shows +7.4 percentage point average improvement")
    print("• Best improvement: Week 24 (+53.8 points) - reduced over-forecasting")
    print("• Worst case: Week 20 (-18.4 points) - was already accurate")
    print("• System is more conservative, reducing over-forecasting")
    print()
    
    # Visual accuracy bars
    print("ACCURACY VISUALIZATION:")
    print("(Each * = 5 percentage points)")
    print()
    
    for result in test_results:
        orig_bars = int(result['orig_acc'] / 5)
        impr_bars = int(result['impr_acc'] / 5)
        
        orig_visual = "*" * orig_bars + " " * (20 - orig_bars)
        impr_visual = "*" * impr_bars + " " * (20 - impr_bars)
        
        print(f"Week {result['week']}: Original  [{orig_visual}] {result['orig_acc']:.1f}%")
        print(f"Week {result['week']}: Improved  [{impr_visual}] {result['impr_acc']:.1f}%")
        print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print("✓ Use improved system for normal weeks (20-25)")
    print("✓ System is more conservative - reduces over-forecasting")
    print("✓ Best for weeks with variable demand patterns")
    print("✓ Consider manual override for very high-demand weeks")
    print()

def test_additional_weeks():
    """Test a few more weeks to get a complete picture"""
    history = load_all_history()
    
    print("TESTING ADDITIONAL WEEKS:")
    print("-" * 50)
    
    # Test a few more weeks
    additional_weeks = [17, 18, 19]
    
    for week in additional_weeks:
        print(f"Week {week}, 2025:")
        
        # Get actual data
        actual = history[
            (history["day"] == "Mon") & 
            (history["week_num"] == week) & 
            (history["year"] == 2025)
        ][["product", "boxes"]].sort_values("product").reset_index(drop=True)
        
        if actual.empty:
            print(f"  No data available")
            continue
        
        # Clean actual data
        actual = actual[~actual["product"].isna()]
        actual = actual[actual["product"].str.strip() != ""]
        actual = actual[actual["boxes"] > 0]
        
        if actual.empty:
            print(f"  No demand data")
            continue
        
        # Get forecasts
        try:
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
            
            # Calculate accuracies
            def calc_acc(forecast_df, actual_df):
                if forecast_df.empty or actual_df.empty:
                    return 0, 0, 0
                
                merged = forecast_df.merge(actual_df, on="product", how="outer", suffixes=("_forecast", "_actual"))
                merged = merged.fillna(0)
                
                total_forecast = merged["forecast_boxes"].sum()
                total_actual = merged["boxes"].sum()
                
                if total_actual > 0:
                    accuracy = (1 - abs(total_forecast - total_actual) / total_actual) * 100
                    return accuracy, total_forecast, total_actual
                else:
                    return 0, total_forecast, total_actual
            
            orig_acc, orig_forecast, orig_actual = calc_acc(original_forecast, actual)
            impr_acc, impr_forecast, impr_actual = calc_acc(improved_forecast, actual)
            
            print(f"  Actual: {orig_actual} boxes")
            print(f"  Original: {orig_forecast} boxes ({orig_acc:.1f}% accuracy)")
            print(f"  Improved: {impr_forecast} boxes ({impr_acc:.1f}% accuracy)")
            print(f"  Change: {impr_acc - orig_acc:+.1f} percentage points")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        print()

if __name__ == "__main__":
    create_visual_summary()
    test_additional_weeks()
