from egg_packing_predictor import load_all_history, forecast_weekday
import pandas as pd

def show_week_details(week):
    history = load_all_history()
    
    print(f'=== DETAILED FORECAST vs ACTUAL: Week {week}, 2025 ===')
    print()

    # Get actual data
    actual = history[
        (history['day'] == 'Mon') & 
        (history['week_num'] == week) & 
        (history['year'] == 2025)
    ][['product', 'boxes']].sort_values('product').reset_index(drop=True)

    print('ACTUAL DATA:')
    print('-' * 50)
    for _, row in actual.iterrows():
        if row['boxes'] > 0:
            print(f'{row["product"]:<25} {row["boxes"]:>6} boxes')

    print()
    print(f'Total Actual: {actual["boxes"].sum()} boxes')
    print()

    # Get original forecast
    print('ORIGINAL SYSTEM FORECAST:')
    print('-' * 50)
    original_forecast = forecast_weekday(
        history, 'Mon', window=8, alpha=0.7,
        target_week_num=week, target_year=2025,
        use_last_year=True, exclude_outliers=False, 
        use_trend=False, conservative_mode=False
    )

    for _, row in original_forecast.iterrows():
        if row['forecast_boxes'] > 0:
            print(f'{row["product"]:<25} {row["forecast_boxes"]:>6} boxes')

    print()
    print(f'Total Original Forecast: {original_forecast["forecast_boxes"].sum()} boxes')
    print()

    # Get improved forecast
    print('IMPROVED SYSTEM FORECAST:')
    print('-' * 50)
    improved_forecast = forecast_weekday(
        history, 'Mon', window=8, alpha=0.7,
        target_week_num=week, target_year=2025,
        use_last_year=True, exclude_outliers=True, 
        use_trend=True, conservative_mode=True
    )

    for _, row in improved_forecast.iterrows():
        if row['forecast_boxes'] > 0:
            print(f'{row["product"]:<25} {row["forecast_boxes"]:>6} boxes')

    print()
    print(f'Total Improved Forecast: {improved_forecast["forecast_boxes"].sum()} boxes')
    print()

    # Calculate accuracies
    actual_total = actual['boxes'].sum()
    orig_total = original_forecast['forecast_boxes'].sum()
    impr_total = improved_forecast['forecast_boxes'].sum()

    orig_accuracy = (1 - abs(orig_total - actual_total) / actual_total) * 100
    impr_accuracy = (1 - abs(impr_total - actual_total) / actual_total) * 100

    print('ACCURACY COMPARISON:')
    print('-' * 50)
    print(f'Actual Total:     {actual_total:>6} boxes')
    print(f'Original Forecast: {orig_total:>6} boxes ({orig_accuracy:>5.1f}% accuracy)')
    print(f'Improved Forecast: {impr_total:>6} boxes ({impr_accuracy:>5.1f}% accuracy)')
    print(f'Improvement:      {impr_accuracy - orig_accuracy:>+5.1f} percentage points')
    print()
    
    # Product-by-product comparison
    print('PRODUCT-BY-PRODUCT COMPARISON:')
    print('-' * 80)
    print(f'{"Product":<25} {"Actual":<8} {"Original":<10} {"Improved":<10} {"Orig Err%":<10} {"Impr Err%":<10}')
    print('-' * 80)
    
    # Get all products
    all_products = set(actual['product'].unique())
    if not original_forecast.empty:
        all_products.update(original_forecast['product'].unique())
    if not improved_forecast.empty:
        all_products.update(improved_forecast['product'].unique())
    
    for product in sorted(all_products):
        actual_val = actual[actual['product'] == product]['boxes'].sum()
        orig_val = original_forecast[original_forecast['product'] == product]['forecast_boxes'].sum()
        impr_val = improved_forecast[improved_forecast['product'] == product]['forecast_boxes'].sum()
        
        if actual_val > 0:
            orig_error = abs(orig_val - actual_val) / actual_val * 100
            impr_error = abs(impr_val - actual_val) / actual_val * 100
            print(f'{product:<25} {actual_val:<8} {orig_val:<10} {impr_val:<10} {orig_error:<10.1f} {impr_error:<10.1f}')

if __name__ == "__main__":
    # Show Week 24 (best improvement)
    show_week_details(24)
    
    print("\n" + "="*80 + "\n")
    
    # Show Week 21 (also had good improvement)
    show_week_details(21)
