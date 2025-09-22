from egg_packing_predictor import load_all_history
import pandas as pd

def investigate_data():
    history = load_all_history()
    
    print('=== CHECKING ALL MONDAY DATA ===')
    monday_data = history[history['day'] == 'Mon']
    print(f'Total Monday records: {len(monday_data)}')
    
    print('\n=== MONDAY DATA BY WEEK ===')
    for week in sorted(monday_data['week_num'].unique()):
        week_data = monday_data[monday_data['week_num'] == week]
        total_boxes = week_data['boxes'].sum()
        print(f'Week {week}: {len(week_data)} records, {total_boxes} total boxes')
    
    print('\n=== CHECKING WEEK 24 SPECIFICALLY ===')
    week24_data = history[
        (history['week_num'] == 24) & 
        (history['year'] == 2025)
    ]
    print(f'Week 24 total records: {len(week24_data)}')
    print('Days in Week 24:', week24_data['day'].unique())
    
    for day in ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']:
        day_data = week24_data[week24_data['day'] == day]
        boxes_sum = day_data['boxes'].sum()
        print(f'{day}: {len(day_data)} records, {boxes_sum} boxes')
    
    print('\n=== SAMPLE MONDAY DATA (Week 24) ===')
    monday_week24 = week24_data[week24_data['day'] == 'Mon']
    if not monday_week24.empty:
        print('First 10 records:')
        for _, row in monday_week24.head(10).iterrows():
            print(f'  {row["product"]} -> {row["boxes"]} boxes')
    else:
        print('No Monday data found for Week 24')
    
    print('\n=== CHECKING FOR CUSTOMER NAMES ===')
    all_products = history['product'].unique()
    customer_keywords = ['loblaws', 'eiking', 'walmart', 'sobeys', 'metro']
    
    for keyword in customer_keywords:
        matches = [p for p in all_products if keyword.lower() in str(p).lower()]
        if matches:
            print(f'{keyword.upper()}: {matches[:3]}')  # Show first 3 matches
        else:
            print(f'{keyword.upper()}: Not found')

if __name__ == "__main__":
    investigate_data()
