from egg_packing_predictor import load_all_history
import pandas as pd

def analyze_monday_data():
    history = load_all_history()
    
    print('=== RAW MONDAY DATA FOR WEEK 24, 2025 ===')
    monday_data = history[
        (history['day'] == 'Mon') & 
        (history['week_num'] == 24) & 
        (history['year'] == 2025)
    ][['product', 'boxes']].sort_values('product')
    
    print('All Monday products:')
    for _, row in monday_data.iterrows():
        product = row['product']
        boxes = row['boxes']
        print(f'{product:<30} {boxes:>6}')
    
    print(f'\nTotal products: {len(monday_data)}')
    print(f'Total boxes: {monday_data["boxes"].sum()}')
    print(f'Products with boxes > 0: {len(monday_data[monday_data["boxes"] > 0])}')
    
    print('\n=== PRODUCTS WITH ACTUAL DEMAND ===')
    demand_products = monday_data[monday_data['boxes'] > 0]
    for _, row in demand_products.iterrows():
        print(f'{row["product"]:<30} {row["boxes"]:>6} boxes')
    
    print(f'\nTotal demand: {demand_products["boxes"].sum()} boxes')
    
    # Check if we're missing major customers
    print('\n=== CHECKING FOR MISSING CUSTOMERS ===')
    all_products = monday_data['product'].unique()
    
    missing_customers = []
    expected_customers = ['Loblaws', 'Eiking', 'Walmart', 'Sobeys', 'Metro']
    
    for customer in expected_customers:
        found = any(customer.lower() in str(product).lower() for product in all_products)
        if not found:
            missing_customers.append(customer)
            print(f'Missing: {customer}')
        else:
            print(f'Found: {customer}')
    
    if missing_customers:
        print(f'\nMissing customers: {missing_customers}')
    else:
        print('\nAll expected customers found')

if __name__ == "__main__":
    analyze_monday_data()
