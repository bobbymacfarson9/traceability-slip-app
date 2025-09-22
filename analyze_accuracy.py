import pandas as pd
from pathlib import Path
from egg_packing_predictor import load_all_history

# Load all data
history = load_all_history()

print('=== DATA ANALYSIS FOR ACCURACY IMPROVEMENTS ===')
print()

# Check data availability
print('Available weeks in 2025:')
weeks_2025 = sorted(history[history['year'] == 2025]['week_num'].unique())
print(weeks_2025)
print()

# Analyze demand patterns by day
print('=== DEMAND PATTERNS BY DAY ===')
for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
    day_data = history[(history['day'] == day) & (history['year'] == 2025)]
    if not day_data.empty:
        total_boxes = day_data.groupby(['week_num', 'file'])['boxes'].sum().reset_index()
        avg_boxes = total_boxes['boxes'].mean()
        print(f'{day}: {len(total_boxes)} weeks, avg {avg_boxes:.1f} boxes/week')
        print(f'  Range: {total_boxes["boxes"].min()}-{total_boxes["boxes"].max()} boxes')
        print(f'  Zero weeks: {(total_boxes["boxes"] == 0).sum()}')
    print()

# Check for zero-demand weeks
print('=== ZERO DEMAND WEEKS ANALYSIS ===')
for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
    day_data = history[(history['day'] == day) & (history['year'] == 2025)]
    if not day_data.empty:
        weekly_totals = day_data.groupby(['week_num', 'file'])['boxes'].sum().reset_index()
        zero_weeks = weekly_totals[weekly_totals['boxes'] == 0]['week_num'].unique()
        if len(zero_weeks) > 0:
            print(f'{day}: Zero demand weeks: {sorted(zero_weeks)}')

# Analyze product-level patterns
print('\n=== PRODUCT-LEVEL ANALYSIS ===')
for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
    day_data = history[(history['day'] == day) & (history['year'] == 2025)]
    if not day_data.empty:
        product_stats = day_data.groupby('product')['boxes'].agg(['mean', 'std', 'count']).reset_index()
        product_stats = product_stats[product_stats['count'] >= 3]  # Only products with 3+ data points
        product_stats['cv'] = product_stats['std'] / product_stats['mean']  # Coefficient of variation
        
        print(f'\n{day} - Product Variability (CV = std/mean):')
        for _, row in product_stats.sort_values('cv', ascending=False).head(5).iterrows():
            if row['mean'] > 0:
                print(f'  {row["product"]}: avg={row["mean"]:.1f}, CV={row["cv"]:.2f}')
