import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import load_all_history

def analyze_historical_data():
    """Analyze the historical data to understand the dataset"""
    print("=== ANALYZING HISTORICAL DATA ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    print(f"Total records: {len(history_df)}")
    print(f"Unique files: {history_df['file'].nunique()}")
    print(f"Date range: {history_df['year'].min()}-{history_df['year'].max()}")
    print(f"Week range: {history_df['week_num'].min()}-{history_df['week_num'].max()}")
    
    # Analyze by year
    print(f"\nRecords by year:")
    year_counts = history_df['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {year}: {count} records")
    
    # Analyze by week
    print(f"\nRecords by week (2024):")
    week_2024 = history_df[history_df['year'] == 2024]
    week_counts = week_2024['week_num'].value_counts().sort_index()
    for week, count in week_counts.items():
        print(f"  Week {week}: {count} records")
    
    # Analyze by day
    print(f"\nRecords by day:")
    day_counts = history_df['day'].value_counts()
    for day, count in day_counts.items():
        print(f"  {day}: {count} records")
    
    # Check what data we have before Week 39, 2024
    print(f"\nData before Week 39, 2024:")
    before_week39 = history_df[
        (history_df['year'] < 2024) | 
        ((history_df['year'] == 2024) & (history_df['week_num'] < 39))
    ]
    print(f"  Total records: {len(before_week39)}")
    
    if len(before_week39) > 0:
        print(f"  Date range: {before_week39['year'].min()}-{before_week39['year'].max()}")
        print(f"  Week range: {before_week39['week_num'].min()}-{before_week39['week_num'].max()}")
        
        # Show sample of data
        print(f"  Sample records:")
        for _, row in before_week39.head(10).iterrows():
            print(f"    Week {row['week_num']}, {row['year']} {row['day']}: {row['product']} - {row['boxes']} boxes")
    
    # Check what data we have for 2024
    print(f"\n2024 data analysis:")
    data_2024 = history_df[history_df['year'] == 2024]
    print(f"  Total records: {len(data_2024)}")
    
    # Check for missing weeks in 2024
    weeks_2024 = set(data_2024['week_num'].unique())
    all_weeks_2024 = set(range(1, 53))
    missing_weeks = all_weeks_2024 - weeks_2024
    
    print(f"  Weeks with data: {sorted(weeks_2024)}")
    print(f"  Missing weeks: {sorted(missing_weeks)}")
    
    # Check product diversity
    print(f"\nProduct analysis:")
    print(f"  Total unique products: {history_df['product'].nunique()}")
    
    # Most common products
    product_counts = history_df['product'].value_counts()
    print(f"  Top 10 products:")
    for product, count in product_counts.head(10).items():
        print(f"    {product}: {count} records")
    
    # Check if we have enough data for forecasting
    print(f"\nForecasting data availability:")
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        day_data = history_df[history_df['day'] == day]
        before_week39_day = day_data[
            (day_data['year'] < 2024) | 
            ((day_data['year'] == 2024) & (day_data['week_num'] < 39))
        ]
        print(f"  {day}: {len(before_week39_day)} records before Week 39, 2024")

if __name__ == "__main__":
    analyze_historical_data()
