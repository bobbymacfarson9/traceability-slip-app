import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal

def test_fixed_thursday():
    """Test the fixed Thursday parser"""
    print("=== TESTING FIXED THURSDAY PARSER ===")
    
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    try:
        result = parse_daily_totals_universal(test_file, "Thurs")
        
        if not result.empty:
            print(f"✅ Found {len(result)} products:")
            total_boxes = 0
            customers = set()
            
            for _, row in result.iterrows():
                print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
                total_boxes += row['boxes']
                
                # Identify customer
                product = row['product']
                if 'Wal' in product or 'Walmart' in product:
                    customers.add('Walmart')
                elif 'Lob' in product or 'Loblaws' in product:
                    customers.add('Loblaws')
                elif 'Eyk' in product or 'ED' in product or 'Eyking' in product:
                    customers.add('Eyking')
                elif 'OC' in product or 'Our Compliments' in product:
                    customers.add('Our Compliments')
                else:
                    customers.add('Other')
            
            print(f"\nTotal boxes: {total_boxes}")
            print(f"Customers found: {', '.join(sorted(customers))}")
            
            # Show products by customer
            print(f"\n--- Products by Customer ---")
            for customer in sorted(customers):
                customer_products = []
                for _, row in result.iterrows():
                    product = row['product']
                    if ((customer == 'Walmart' and ('Wal' in product or 'Walmart' in product)) or
                        (customer == 'Loblaws' and ('Lob' in product or 'Loblaws' in product)) or
                        (customer == 'Eyking' and ('Eyk' in product or 'ED' in product or 'Eyking' in product)) or
                        (customer == 'Our Compliments' and ('OC' in product or 'Our Compliments' in product)) or
                        (customer == 'Other' and not any(x in product for x in ['Wal', 'Lob', 'Eyk', 'ED', 'OC']))):
                        customer_products.append(f"{product} ({row['boxes']} boxes)")
                
                if customer_products:
                    print(f"  {customer}: {', '.join(customer_products)}")
        else:
            print(f"❌ No products found for Thursday")
            
    except Exception as e:
        print(f"Error testing Thursday: {e}")

if __name__ == "__main__":
    test_fixed_thursday()
