# final_correct_parser.py
# This parser correctly reads ALL columns in the Daily Totals section

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

def parse_daily_totals_final(file_path: Path, sheet: str) -> pd.DataFrame:
    """Parse ALL columns in the Daily Totals section correctly"""
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
    
    # Find the header row that shows the column structure
    header_row = None
    for idx in range(daily_totals_start, daily_totals_end + 1):
        row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
        if "Our Compliments" in row_str or "Walmart" in row_str or "Loblaws" in row_str or "Eyking" in row_str:
            header_row = idx
            print(f"Found header row at {idx}: {row_str}")
            break
    
    if header_row is None:
        print("No header row found in Daily Totals section")
        return pd.DataFrame(columns=["file", "day", "product", "boxes", "week_num", "year"])
    
    # Parse data rows (skip the header row)
    for idx in range(header_row + 1, daily_totals_end + 1):
        row = df.iloc[idx]
        row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
        
        # Skip empty rows
        if not any(v.strip() for v in row_values):
            continue
        
        # Parse the row systematically
        # The pattern is: [empty, qty1, product1, qty2, product2, empty, qty3, product3, empty, qty4, product4]
        
        i = 0
        while i < len(row_values):
            val = row_values[i].strip()
            
            # Skip empty cells
            if not val:
                i += 1
                continue
            
            # Check if this is a quantity (number)
            try:
                qty = float(val)
                if qty > 0:  # Only positive quantities
                    # Look for product name in the next cell
                    if i + 1 < len(row_values):
                        product = row_values[i + 1].strip()
                        if (product and 
                            not product.isdigit() and 
                            product.lower() not in ['pcs', 'case', 'cases', 'ea', 'each', 'pk', 'pack', 'pks', 'box total', 'our compliments'] and
                            not any(customer in product.lower() for customer in ['sobeys', 'walmart', 'loblaws', 'eyking', 'metro', 'superstore', 'foodland'])):
                            
                            records.append({
                                "file": file_name,
                                "day": sheet,
                                "product": product,
                                "boxes": int(qty),
                                "week_num": week_num,
                                "year": year
                            })
                            
                            print(f"  Row {idx}: {product} = {qty} boxes")
                            i += 2  # Skip both quantity and product
                        else:
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
            except ValueError:
                # Not a number, skip
                i += 1
    
    return pd.DataFrame.from_records(records)

def test_final_parser():
    """Test the final parser on Week 24, 2025 Monday"""
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== TESTING FINAL CORRECT PARSER ===")
    print(f"Testing file: {test_file}")
    
    result = parse_daily_totals_final(test_file, "Mon")
    
    print(f"\nParsed {len(result)} products from Daily Totals section:")
    for _, row in result.iterrows():
        print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
    
    print(f"\nTotal boxes: {result['boxes'].sum()}")
    
    # Compare with original parser
    print(f"\n=== COMPARISON WITH ORIGINAL PARSER ===")
    from fixed_daily_totals_parser import parse_daily_totals_only
    original_result = parse_daily_totals_only(test_file, "Mon")
    
    print(f"Original parser: {len(original_result)} products, {original_result['boxes'].sum()} total boxes")
    print(f"Final parser: {len(result)} products, {result['boxes'].sum()} total boxes")
    
    return result

if __name__ == "__main__":
    test_final_parser()
