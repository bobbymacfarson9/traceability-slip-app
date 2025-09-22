import pandas as pd
import numpy as np
from pathlib import Path

def debug_wednesday_thursday():
    """Debug Wednesday and Thursday parsing issues"""
    print("=== DEBUGGING WEDNESDAY AND THURSDAY PARSING ===")
    
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    for day in ["Wed", "Thurs"]:
        print(f"\n{'='*50}")
        print(f"DEBUGGING {day.upper()}")
        print(f"{'='*50}")
        
        try:
            df = pd.read_excel(test_file, sheet_name=day, header=None)
            print(f"Loaded {day} sheet: {len(df)} rows, {len(df.columns)} columns")
            
            # Find the Daily Totals section
            daily_totals_start = None
            daily_totals_end = None
            
            print(f"\n--- Looking for DAILY TOTALS section ---")
            for idx, row in df.iterrows():
                row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
                
                # Look for "DAILY TOTALS" marker
                if "DAILY TOTALS" in row_str.upper():
                    daily_totals_start = idx + 1
                    print(f"Found 'DAILY TOTALS' at row {idx}")
                    print(f"Row content: {row_str}")
                    break
            
            if daily_totals_start is None:
                print(f"❌ No 'DAILY TOTALS' found in {day}")
                continue
            
            # Find the end of Daily Totals section
            for idx in range(daily_totals_start, len(df)):
                row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper() or "SPECIALTY" in row_str.upper():
                    daily_totals_end = idx - 1
                    print(f"Found end marker at row {idx}: {row_str}")
                    break
            
            if daily_totals_end is None:
                daily_totals_end = len(df) - 1
                print(f"No end marker found, using end of sheet: row {daily_totals_end}")
            
            print(f"Daily Totals section: rows {daily_totals_start} to {daily_totals_end}")
            
            # Find the header row that shows the column structure
            header_row = None
            print(f"\n--- Looking for header row ---")
            for idx in range(daily_totals_start, daily_totals_end + 1):
                row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if "Our Compliments" in row_str or "Walmart" in row_str or "Loblaws" in row_str or "Eyking" in row_str:
                    header_row = idx
                    print(f"Found header row at {idx}: {row_str}")
                    break
            
            if header_row is None:
                print(f"❌ No header row found in {day}")
                continue
            
            # Show the header row in detail
            print(f"\n--- Header row details (row {header_row}) ---")
            header_row_data = df.iloc[header_row]
            for col_idx, cell in enumerate(header_row_data):
                if pd.notna(cell) and str(cell).strip():
                    print(f"  Column {col_idx}: '{cell}'")
            
            # Show data rows
            print(f"\n--- Data rows (rows {header_row + 1} to {daily_totals_end}) ---")
            for idx in range(header_row + 1, min(header_row + 10, daily_totals_end + 1)):  # Show first 10 rows
                row = df.iloc[idx]
                row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
                
                # Skip empty rows
                if not any(v.strip() for v in row_values):
                    continue
                
                print(f"\nRow {idx}:")
                for col_idx, val in enumerate(row_values):
                    if val.strip():
                        print(f"  Col {col_idx}: '{val}'")
                
                # Test current parsing logic
                print(f"  Testing current parsing logic:")
                if day == "Wed":
                    _test_wed_parsing(row_values, idx)
                elif day == "Thurs":
                    _test_thurs_parsing(row_values, idx)
            
            # Show what the current parser would extract
            print(f"\n--- What current parser extracts ---")
            from egg_packing_predictor_universal import parse_daily_totals_universal
            result = parse_daily_totals_universal(test_file, day)
            if not result.empty:
                print(f"Found {len(result)} products:")
                for _, row in result.iterrows():
                    print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
            else:
                print("No products found by current parser")
                
        except Exception as e:
            print(f"Error processing {day}: {e}")

def _test_wed_parsing(row_values, idx):
    """Test Wednesday parsing logic"""
    print(f"    Wednesday parsing test:")
    
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                print(f"      Our Compliments: {row_values[2]} = {qty} boxes")
        except ValueError:
            print(f"      Our Compliments: Invalid quantity '{row_values[1]}'")
    
    # Walmart: Column D (quantity), Column E (product)
    if len(row_values) > 4 and row_values[3].strip() and row_values[4].strip():
        try:
            qty = float(row_values[3])
            if qty > 0:
                print(f"      Walmart: {row_values[4]} = {qty} boxes")
        except ValueError:
            print(f"      Walmart: Invalid quantity '{row_values[3]}'")
    
    # Loblaws: Column G (product), Column H (quantity)
    if len(row_values) > 8 and row_values[6].strip() and row_values[7].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                print(f"      Loblaws: {row_values[6]} = {qty} boxes")
        except ValueError:
            print(f"      Loblaws: Invalid quantity '{row_values[7]}'")
    
    # Eyking: Column J (quantity), Column K (product)
    if len(row_values) > 11 and row_values[9].strip() and row_values[10].strip():
        try:
            qty = float(row_values[9])
            if qty > 0:
                print(f"      Eyking: {row_values[10]} = {qty} boxes")
        except ValueError:
            print(f"      Eyking: Invalid quantity '{row_values[9]}'")
    else:
        print(f"      Eyking: Not enough columns or empty values")
        if len(row_values) > 9:
            print(f"        Col 9: '{row_values[9]}'")
        if len(row_values) > 10:
            print(f"        Col 10: '{row_values[10]}'")

def _test_thurs_parsing(row_values, idx):
    """Test Thursday parsing logic"""
    print(f"    Thursday parsing test:")
    
    # Our Compliments: Column A (quantity), Column B (product)
    if len(row_values) > 1 and row_values[0].strip() and row_values[1].strip():
        try:
            qty = float(row_values[0])
            if qty > 0:
                print(f"      Our Compliments: {row_values[1]} = {qty} boxes")
        except ValueError:
            print(f"      Our Compliments: Invalid quantity '{row_values[0]}'")
    
    # Look for embedded quantities in other columns
    for i, val in enumerate(row_values):
        if val.strip() and not val.isdigit():
            # Look for pattern: "number product_name"
            import re
            match = re.match(r'^(\d+)\s+(.+)$', val.strip())
            if match:
                qty = int(match.group(1))
                product = match.group(2)
                if qty > 0:
                    print(f"      Embedded (Col {i}): {product} = {qty} boxes")

if __name__ == "__main__":
    debug_wednesday_thursday()
