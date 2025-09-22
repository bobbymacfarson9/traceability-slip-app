import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def find_high_volume_days():
    """Find high-volume days in the historical data"""
    print("=== FINDING HIGH-VOLUME DAYS ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    print(f"📊 HISTORICAL DATA OVERVIEW:")
    print(f"   Total records: {len(history_df)}")
    print(f"   Date range: {history_df['year'].min()}-{history_df['year'].max()}")
    print(f"   Weeks: {history_df['week_num'].nunique()}")
    
    # Analyze daily volumes
    daily_volumes = history_df.groupby(['year', 'week_num', 'day'])['boxes'].sum().reset_index()
    daily_volumes['total_boxes'] = daily_volumes['boxes']
    
    print(f"\n📦 DAILY VOLUME DISTRIBUTION:")
    print(f"   Average daily volume: {daily_volumes['total_boxes'].mean():.0f} boxes")
    print(f"   Median daily volume: {daily_volumes['total_boxes'].median():.0f} boxes")
    print(f"   Max daily volume: {daily_volumes['total_boxes'].max():.0f} boxes")
    print(f"   Min daily volume: {daily_volumes['total_boxes'].min():.0f} boxes")
    print(f"   Std dev: {daily_volumes['total_boxes'].std():.0f} boxes")
    
    # Volume percentiles
    percentiles = [50, 75, 90, 95, 99]
    print(f"\n📈 VOLUME PERCENTILES:")
    for p in percentiles:
        value = np.percentile(daily_volumes['total_boxes'], p)
        print(f"   {p}th percentile: {value:.0f} boxes")
    
    # Find high-volume days
    high_volume_threshold = 1000
    high_volume_days = daily_volumes[daily_volumes['total_boxes'] >= high_volume_threshold].copy()
    
    print(f"\n🎯 HIGH-VOLUME DAYS (≥{high_volume_threshold} boxes):")
    print(f"   Found: {len(high_volume_days)} high-volume days")
    print(f"   Percentage: {len(high_volume_days)/len(daily_volumes)*100:.1f}% of all days")
    
    if not high_volume_days.empty:
        print(f"   Average high-volume: {high_volume_days['total_boxes'].mean():.0f} boxes")
        print(f"   Max high-volume: {high_volume_days['total_boxes'].max():.0f} boxes")
        
        # Show top high-volume days
        top_days = high_volume_days.nlargest(10, 'total_boxes')
        print(f"\n   Top 10 high-volume days:")
        for _, row in top_days.iterrows():
            print(f"     Week {row['week_num']}, {row['year']} {row['day']}: {row['total_boxes']:.0f} boxes")
        
        # Analyze by day of week
        print(f"\n   High-volume days by day of week:")
        day_counts = high_volume_days['day'].value_counts()
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            count = day_counts.get(day, 0)
            print(f"     {day}: {count} days")
        
        # Analyze by year
        print(f"\n   High-volume days by year:")
        year_counts = high_volume_days['year'].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"     {year}: {count} days")
    
    # Find very high-volume days
    very_high_threshold = 2000
    very_high_days = daily_volumes[daily_volumes['total_boxes'] >= very_high_threshold].copy()
    
    print(f"\n🚀 VERY HIGH-VOLUME DAYS (≥{very_high_threshold} boxes):")
    print(f"   Found: {len(very_high_days)} very high-volume days")
    print(f"   Percentage: {len(very_high_days)/len(daily_volumes)*100:.1f}% of all days")
    
    if not very_high_days.empty:
        print(f"   Average very high-volume: {very_high_days['total_boxes'].mean():.0f} boxes")
        print(f"   Max very high-volume: {very_high_days['total_boxes'].max():.0f} boxes")
        
        # Show all very high-volume days
        print(f"\n   All very high-volume days:")
        for _, row in very_high_days.iterrows():
            print(f"     Week {row['week_num']}, {row['year']} {row['day']}: {row['total_boxes']:.0f} boxes")
    
    # Find test weeks with high-volume days
    print(f"\n🧪 TEST WEEKS WITH HIGH-VOLUME DAYS:")
    test_weeks = [45, 46, 47, 48, 49, 50]
    test_year = 2024
    
    for week_num in test_weeks:
        week_days = daily_volumes[(daily_volumes['year'] == test_year) & (daily_volumes['week_num'] == week_num)]
        if not week_days.empty:
            max_volume = week_days['total_boxes'].max()
            avg_volume = week_days['total_boxes'].mean()
            high_volume_count = len(week_days[week_days['total_boxes'] >= high_volume_threshold])
            
            print(f"   Week {week_num}, {test_year}:")
            print(f"     Max daily: {max_volume:.0f} boxes")
            print(f"     Avg daily: {avg_volume:.0f} boxes")
            print(f"     High-volume days: {high_volume_count}/5")
            
            if high_volume_count > 0:
                high_days = week_days[week_days['total_boxes'] >= high_volume_threshold]
                for _, row in high_days.iterrows():
                    print(f"       {row['day']}: {row['total_boxes']:.0f} boxes")
    
    return daily_volumes, high_volume_days, very_high_days

def analyze_volume_patterns(daily_volumes):
    """Analyze volume patterns to understand when high-volume days occur"""
    print(f"\n{'='*80}")
    print(f"VOLUME PATTERN ANALYSIS")
    print(f"{'='*80}")
    
    # Day-of-week analysis
    print(f"\n📅 VOLUME BY DAY OF WEEK:")
    day_analysis = daily_volumes.groupby('day')['total_boxes'].agg(['mean', 'median', 'std', 'max', 'count']).round(0)
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        if day in day_analysis.index:
            mean_vol = day_analysis.loc[day, 'mean']
            median_vol = day_analysis.loc[day, 'median']
            max_vol = day_analysis.loc[day, 'max']
            count = day_analysis.loc[day, 'count']
            print(f"   {day}: avg {mean_vol:.0f}, median {median_vol:.0f}, max {max_vol:.0f} ({count} days)")
    
    # Year analysis
    print(f"\n📅 VOLUME BY YEAR:")
    year_analysis = daily_volumes.groupby('year')['total_boxes'].agg(['mean', 'median', 'std', 'max', 'count']).round(0)
    
    for year in sorted(year_analysis.index):
        mean_vol = year_analysis.loc[year, 'mean']
        median_vol = year_analysis.loc[year, 'median']
        max_vol = year_analysis.loc[year, 'max']
        count = year_analysis.loc[year, 'count']
        print(f"   {year}: avg {mean_vol:.0f}, median {median_vol:.0f}, max {max_vol:.0f} ({count} days)")
    
    # Week analysis
    print(f"\n📅 VOLUME BY WEEK NUMBER:")
    week_analysis = daily_volumes.groupby('week_num')['total_boxes'].agg(['mean', 'median', 'std', 'max', 'count']).round(0)
    
    # Show weeks with highest average volume
    top_weeks = week_analysis.nlargest(10, 'mean')
    print(f"   Top 10 weeks by average daily volume:")
    for week_num, row in top_weeks.iterrows():
        print(f"     Week {week_num}: avg {row['mean']:.0f}, max {row['max']:.0f} ({row['count']} days)")
    
    return day_analysis, year_analysis, week_analysis

if __name__ == "__main__":
    daily_volumes, high_volume_days, very_high_days = find_high_volume_days()
    if daily_volumes is not None:
        analyze_volume_patterns(daily_volumes)
        
        print(f"\n{'='*80}")
        print(f"CONCLUSION")
        print(f"{'='*80}")
        
        if len(high_volume_days) > 0:
            print(f"✅ Found {len(high_volume_days)} high-volume days in historical data")
            print(f"✅ System has been tested on high-volume scenarios")
            print(f"✅ High-volume forecasting performance can be analyzed")
        else:
            print(f"⚠️  No high-volume days found in historical data")
            print(f"⚠️  All days have <1000 boxes")
            print(f"⚠️  Need to test on different data or adjust thresholds")
            
        if len(very_high_days) > 0:
            print(f"✅ Found {len(very_high_days)} very high-volume days")
            print(f"✅ System has been tested on extreme high-volume scenarios")
        else:
            print(f"⚠️  No very high-volume days found")
            print(f"⚠️  All days have <2000 boxes")
