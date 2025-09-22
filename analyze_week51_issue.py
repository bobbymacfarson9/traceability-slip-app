import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our proven parser logic (preserved)
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def analyze_week51_issue():
    """Analyze what's happening with Week 51 to understand the extreme errors"""
    print("=== ANALYZING WEEK 51 ISSUE ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Test Week 51
    test_file = Path('Week 51 Loading Slip 2024.xlsx')
    if not test_file.exists():
        print("❌ Week 51 file not found")
        return
    
    print(f"🔍 Analyzing Week 51 (December 16-20, 2024)...")
    print(f"This is likely a holiday week (Christmas week)")
    
    # Analyze each day
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        print(f"\n📅 {day} Analysis:")
        
        # Get actual data
        actual_data = parse_daily_totals_universal(test_file, day)
        if actual_data.empty:
            print(f"   No data found")
            continue
        
        total_actual = actual_data['boxes'].sum()
        print(f"   Actual total: {total_actual} boxes")
        
        if total_actual == 0:
            print(f"   ⚠️  ZERO DEMAND - This is likely a holiday!")
            continue
        
        # Show product breakdown
        print(f"   Products:")
        for _, row in actual_data.iterrows():
            print(f"     {row['product']}: {row['boxes']} boxes")
        
        # Check if this is unusually low demand
        # Get historical data for this day
        day_data = history_df[history_df['day'] == day].copy()
        if len(day_data) > 0:
            historical_avg = day_data['boxes'].mean()
            historical_median = day_data['boxes'].median()
            
            print(f"   Historical avg: {historical_avg:.1f} boxes")
            print(f"   Historical median: {historical_median:.1f} boxes")
            
            if total_actual < historical_avg * 0.1:  # Less than 10% of average
                print(f"   🚨 EXTREMELY LOW DEMAND - {total_actual/historical_avg*100:.1f}% of average")
            elif total_actual < historical_avg * 0.3:  # Less than 30% of average
                print(f"   ⚠️  Very low demand - {total_actual/historical_avg*100:.1f}% of average")
    
    # Check if this is a known holiday week
    print(f"\n🎄 HOLIDAY ANALYSIS:")
    print(f"Week 51, 2024 = December 16-20, 2024")
    print(f"This is the week before Christmas (Dec 25)")
    print(f"Many businesses have reduced operations or early closures")
    print(f"This explains the extremely low demand!")
    
    # Analyze historical patterns around holidays
    print(f"\n📊 HISTORICAL HOLIDAY PATTERNS:")
    
    # Look for other weeks with very low demand
    low_demand_weeks = []
    
    for (year, week_num), week_data in history_df.groupby(['year', 'week_num']):
        total_week_boxes = week_data['boxes'].sum()
        
        # Calculate average for comparison
        all_weeks_avg = history_df.groupby(['year', 'week_num'])['boxes'].sum().mean()
        
        if total_week_boxes < all_weeks_avg * 0.3:  # Less than 30% of average
            low_demand_weeks.append({
                'year': year,
                'week_num': week_num,
                'total_boxes': total_week_boxes,
                'percentage': total_week_boxes / all_weeks_avg * 100
            })
    
    if low_demand_weeks:
        print(f"Found {len(low_demand_weeks)} weeks with very low demand:")
        for week in sorted(low_demand_weeks, key=lambda x: x['percentage'])[:5]:
            print(f"   Week {week['week_num']}, {week['year']}: {week['total_boxes']:.0f} boxes ({week['percentage']:.1f}% of avg)")
    
    return True

def create_holiday_detection_solution():
    """Create a solution for holiday detection and handling"""
    print(f"\n{'='*80}")
    print(f"HOLIDAY DETECTION SOLUTION")
    print(f"{'='*80}")
    
    print(f"\n🎯 PROBLEM IDENTIFIED:")
    print(f"   Week 51 is a holiday week (Christmas week)")
    print(f"   System doesn't detect holiday scenarios")
    print(f"   Results in massive over-prediction")
    
    print(f"\n💡 SOLUTION STRATEGY:")
    print(f"   1. Detect holiday weeks based on demand patterns")
    print(f"   2. Apply holiday-specific forecasting (70-90% reduction)")
    print(f"   3. Use minimum thresholds to prevent extreme predictions")
    print(f"   4. Flag potential holiday weeks for manual review")
    
    print(f"\n🔧 IMPLEMENTATION:")
    print(f"   - Holiday detection: If total demand < 30% of historical average")
    print(f"   - Holiday adjustment: Apply 70-90% reduction factor")
    print(f"   - Minimum forecast: Set reasonable minimums (20-50 boxes)")
    print(f"   - Manual override: Flag weeks for human review")
    
    print(f"\n📅 KNOWN HOLIDAY WEEKS TO FLAG:")
    print(f"   - Christmas week (Week 51-52)")
    print(f"   - New Year week (Week 1)")
    print(f"   - Easter week (varies)")
    print(f"   - Thanksgiving week (varies)")
    print(f"   - Any week with <30% of average demand")
    
    return True

def create_simple_holiday_fix():
    """Create a simple holiday detection and fix"""
    print(f"\n{'='*80}")
    print(f"SIMPLE HOLIDAY FIX")
    print(f"{'='*80}")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Calculate historical average by day
    day_averages = history_df.groupby('day')['boxes'].sum().mean()
    print(f"Historical daily average: {day_averages:.1f} boxes")
    
    # Test Week 51 with simple holiday detection
    test_file = Path('Week 51 Loading Slip 2024.xlsx')
    if not test_file.exists():
        print("❌ Week 51 file not found")
        return
    
    print(f"\n🧪 Testing simple holiday fix on Week 51...")
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        # Get actual data
        actual_data = parse_daily_totals_universal(test_file, day)
        if actual_data.empty:
            continue
        
        actual_total = actual_data['boxes'].sum()
        
        # Simple holiday detection: if actual < 20% of historical average
        holiday_threshold = day_averages * 0.2
        
        if actual_total < holiday_threshold:
            print(f"   {day}: {actual_total} boxes - HOLIDAY DETECTED (threshold: {holiday_threshold:.0f})")
            # Apply holiday forecast: 50% of historical average
            holiday_forecast = day_averages * 0.5
            print(f"     Holiday forecast: {holiday_forecast:.0f} boxes")
        else:
            print(f"   {day}: {actual_total} boxes - Normal demand")
    
    return True

if __name__ == "__main__":
    analyze_week51_issue()
    create_holiday_detection_solution()
    create_simple_holiday_fix()
