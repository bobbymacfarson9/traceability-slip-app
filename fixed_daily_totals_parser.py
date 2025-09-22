# fixed_daily_totals_parser.py
# This parser ONLY reads the "Daily Totals" section and extracts the correct product/box data

import pandas as pd
import numpy as np
import re
from pathlib import Path

def extract_week_year(filename):
    """Extract week number and year from filename"""
    match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def parse_daily_totals_only(file_path: Path, sheet: str) -> pd.DataFrame:
    """Parse ONLY the Daily Totals section and extract correct product/box data"""
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    file_name = file_path.name
    week_num, year = extract_week_year(file_name)
    
    records = []
    
    # Find the Daily Totals section
    daily_totals_start = None
    daily_totals_end = None
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        
        # Look for "DAILY TOTALS" marker
        if "DAILY TOTALS" in row_str.upper():
            daily_totals_start = idx + 1  # Start after the header
            print(f"Found DAILY TOTALS at row {idx}")
            break
    
    if daily_totals_start is None:
        print(f"No DAILY TOTALS found in {file_name} sheet {sheet}")
        return pd.DataFrame(columns=["file", "day", "product", "boxes", "week_num", "year"])
    
    # Find the end of Daily Totals section
    for idx in range(daily_totals_start, len(df)):
        row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
        if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper():
            daily_totals_end = idx - 1
            break
    
    if daily_totals_end is None:
        daily_totals_end = len(df) - 1
    
    print(f"Daily Totals section: rows {daily_totals_start} to {daily_totals_end}")
    
    # Parse the Daily Totals section
    for idx in range(daily_totals_start, daily_totals_end + 1):
        row = df.iloc[idx]
        row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
        
        # Skip empty rows
        if not any(v.strip() for v in row_values):
            continue
        
        # Look for product/quantity patterns in the Daily Totals
        # The pattern should be: [quantity, product_name] or [product_name, quantity]
        # We need to identify which column has the boxes (not pieces)
        
        # Try to find numeric quantities and product names
        quantities = []
        products = []
        
        for i, val in enumerate(row_values):
            val = val.strip()
            if not val:
                continue
                
            # Check if it's a number (quantity)
            try:
                qty = float(val)
                if qty > 0:  # Only positive quantities
                    quantities.append((i, qty))
            except ValueError:
                # Check if it's a product name (not a customer name or section header)
                if (val and 
                    not val.isdigit() and 
                    not re.match(r'^\d+\.', val) and  # Not a numbered section
                    val.lower() not in ['pcs', 'case', 'cases', 'ea', 'each', 'pk', 'pack', 'pks', 'box total', 'our compliments'] and
                    not any(customer in val.lower() for customer in ['sobeys', 'walmart', 'loblaws', 'eyking', 'metro', 'superstore', 'foodland'])):
                    products.append((i, val))
        
        # If we found both quantities and products, create records
        if quantities and products:
            # Use the largest quantity (likely boxes, not pieces)
            max_qty = max(quantities, key=lambda x: x[1])
            qty_value = max_qty[1]
            
            # Use the longest product name (most descriptive)
            max_product = max(products, key=lambda x: len(x[1]))
            product_name = max_product[1]
            
            records.append({
                "file": file_name,
                "day": sheet,
                "product": product_name,
                "boxes": int(qty_value),
                "week_num": week_num,
                "year": year
            })
            
            print(f"  Row {idx}: {product_name} = {qty_value} boxes")
    
    return pd.DataFrame.from_records(records)

def test_daily_totals_parsing():
    """Test the fixed Daily Totals parser on Week 24, 2025 Monday"""
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== TESTING FIXED DAILY TOTALS PARSER ===")
    print(f"Testing file: {test_file}")
    
    result = parse_daily_totals_only(test_file, "Mon")
    
    print(f"\nParsed {len(result)} products from Daily Totals section:")
    for _, row in result.iterrows():
        print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
    
    print(f"\nTotal boxes: {result['boxes'].sum()}")
    
    return result

if __name__ == "__main__":
    test_daily_totals_parsing()
