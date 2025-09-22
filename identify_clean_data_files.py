import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal, load_all_history

def identify_clean_data_files():
    """Identify files with complete, correct data for testing"""
    print("=== IDENTIFYING CLEAN DATA FILES FOR TESTING ===")
    
    # Load historical data
    history_df = load_all_history(".")
    
    # Get all available weeks
    available_weeks = history_df.groupby(['year', 'week_num']).size().reset_index()
    available_weeks = available_weeks[available_weeks[0] >= 5]  # At least 5 records per week
    
    print(f"Found {len(available_weeks)} weeks with sufficient data")
    
    # Analyze each week for data quality
    week_analysis = []
    
    for _, week_info in available_weeks.iterrows():
        year = week_info['year']
        week_num = week_info['week_num']
        
        # Find the corresponding file
        week_files = list(Path(".").glob(f"Week {week_num} Loading Slip {year}.xlsx"))
        if not week_files:
            continue
        
        week_file = week_files[0]
        
        # Analyze data quality for this week
        daily_totals = []
        total_boxes = 0
        total_products = 0
        missing_days = []
        
        for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
            try:
                day_data = parse_daily_totals_universal(week_file, day)
                if day_data.empty:
                    missing_days.append(day)
                else:
                    day_total = day_data['boxes'].sum()
                    daily_totals.append(day_total)
                    total_boxes += day_total
                    total_products += len(day_data)
            except Exception as e:
                missing_days.append(day)
        
        # Calculate quality metrics
        avg_daily_total = np.mean(daily_totals) if daily_totals else 0
        daily_std = np.std(daily_totals) if len(daily_totals) > 1 else 0
        cv = daily_std / avg_daily_total if avg_daily_total > 0 else 0
        
        # Quality score (higher is better)
        quality_score = 0
        
        # Check for missing days (penalty)
        if not missing_days:
            quality_score += 50  # All days present
        else:
            quality_score += 50 - (len(missing_days) * 10)  # Penalty for missing days
        
        # Check for reasonable daily totals (not too low, not too high)
        if avg_daily_total > 100:  # Reasonable minimum
            quality_score += 20
        if avg_daily_total < 1000:  # Reasonable maximum
            quality_score += 20
        
        # Check for consistency (low coefficient of variation)
        if cv < 0.5:  # Consistent daily totals
            quality_score += 20
        elif cv < 1.0:  # Moderately consistent
            quality_score += 10
        
        # Check for reasonable product count
        if total_products > 50:  # Good product diversity
            quality_score += 10
        
        week_analysis.append({
            'week_file': week_file.name,
            'week_num': week_num,
            'year': year,
            'total_boxes': total_boxes,
            'total_products': total_products,
            'avg_daily_total': avg_daily_total,
            'daily_std': daily_std,
            'cv': cv,
            'missing_days': missing_days,
            'quality_score': quality_score,
            'is_clean': quality_score >= 80  # Threshold for "clean" data
        })
    
    # Sort by quality score
    week_analysis.sort(key=lambda x: x['quality_score'], reverse=True)
    
    print(f"\n📊 DATA QUALITY ANALYSIS:")
    print(f"{'Week':<25} {'Quality':<8} {'Total Boxes':<12} {'Avg Daily':<10} {'CV':<8} {'Missing Days'}")
    print(f"{'-'*80}")
    
    clean_weeks = []
    for week in week_analysis:
        missing_str = ', '.join(week['missing_days']) if week['missing_days'] else 'None'
        print(f"{week['week_file']:<25} {week['quality_score']:<8} {week['total_boxes']:<12} {week['avg_daily_total']:<10.0f} {week['cv']:<8.2f} {missing_str}")
        
        if week['is_clean']:
            clean_weeks.append(week)
    
    print(f"\n✅ CLEAN DATA FILES IDENTIFIED:")
    print(f"Found {len(clean_weeks)} weeks with quality score >= 80")
    
    # Select top 6 clean weeks for testing
    test_weeks = clean_weeks[:6]
    
    print(f"\n🎯 SELECTED TEST WEEKS:")
    for i, week in enumerate(test_weeks, 1):
        print(f"{i}. {week['week_file']} (Quality: {week['quality_score']}, Total: {week['total_boxes']} boxes)")
    
    return test_weeks

if __name__ == "__main__":
    identify_clean_data_files()
