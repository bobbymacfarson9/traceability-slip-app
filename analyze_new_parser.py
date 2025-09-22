import pandas as pd

def analyze_new_parser():
    # Load the new parsed data
    new_data = pd.read_csv('test_parsed/all_parsed_totals_tally_carts.csv')
    
    print('=== NEW PARSER RESULTS ===')
    print(f'Total rows: {len(new_data)}')
    print(f'Files processed: {new_data["file"].nunique()}')
    print(f'Days: {sorted(new_data["day"].unique())}')
    print(f'Sections: {sorted(new_data["section"].unique())}')
    
    print('\n=== MONDAY DAILY_TOTALS SAMPLE ===')
    monday_totals = new_data[(new_data['day'] == 'Mon') & (new_data['section'] == 'DAILY_TOTALS')]
    print(f'Monday DAILY_TOTALS rows: {len(monday_totals)}')
    
    # Show first 10 Monday products with quantities
    monday_with_qty = monday_totals[monday_totals['qty'].notna() & (monday_totals['qty'] > 0)]
    print('\nFirst 10 Monday products with quantities:')
    for _, row in monday_with_qty.head(10).iterrows():
        print(f'  {row["product"]:<25} {row["qty"]:>6}')
    
    print(f'\nTotal Monday DAILY_TOTALS quantity: {monday_totals["qty"].sum():.0f}')
    
    print('\n=== CHECKING FOR CUSTOMER NAMES ===')
    all_products = new_data['product'].unique()
    customer_keywords = ['wal', 'lob', 'eyk', 'sobeys', 'metro']
    
    for keyword in customer_keywords:
        matches = [p for p in all_products if keyword.lower() in str(p).lower()]
        if matches:
            print(f'{keyword.upper()}: {len(matches)} products found')
            print(f'  Examples: {matches[:3]}')
        else:
            print(f'{keyword.upper()}: Not found')
    
    print('\n=== COMPARING WITH OLD SYSTEM ===')
    # Load old system data
    from egg_packing_predictor import load_all_history
    old_data = load_all_history()
    
    print(f'Old system total rows: {len(old_data)}')
    print(f'Old system unique products: {old_data["product"].nunique()}')
    print(f'Old system total boxes: {old_data["boxes"].sum():.0f}')
    
    # Compare Monday data specifically
    old_monday = old_data[old_data['day'] == 'Mon']
    new_monday = new_data[(new_data['day'] == 'Mon') & (new_data['section'] == 'DAILY_TOTALS')]
    
    print(f'\nMonday comparison:')
    print(f'  Old system: {len(old_monday)} records, {old_monday["boxes"].sum():.0f} total boxes')
    print(f'  New parser: {len(new_monday)} records, {new_monday["qty"].sum():.0f} total quantity')
    
    print(f'\nImprovement: {len(new_monday) / len(old_monday) if len(old_monday) > 0 else "N/A":.1f}x more records')

if __name__ == "__main__":
    analyze_new_parser()
