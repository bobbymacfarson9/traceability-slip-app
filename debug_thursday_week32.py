import pandas as pd
import numpy as np
from pathlib import Path

def debug_thursday_week32():
    """Debug Thursday parsing for Week 32 to see why it's missing customers"""
    print("=== DEBUGGING THURSDAY WEEK 32 PARSING ===")
    
    test_file = Path("Week 32 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    try:
        df = pd.read_excel(test_file, sheet_name="Thurs", header=None)
        print(f"Loaded Thurs sheet: {len(df)} rows, {len(df.columns)} columns")
        
        # Find the Daily Totals section
        daily_totals_start = None
        daily_totals_end = None
        
        for idx, row in df.iterrows():
            row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
            if "DAILY TOTALS" in row_str.upper():
                daily_totals_start = idx + 1
                break
        
        if daily_totals_start is None:
            print("❌ No 'DAILY TOTALS' found")
            return
        
        # Find the end
        for idx in range(daily_totals_start, len(df)):
            row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
            if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper():
                daily_totals_end = idx - 1
                break
        
        if daily_totals_end is None:
            daily_totals_end = len(df) - 1
        
        # Find header row
        header_row = None
        for idx in range(daily_totals_start, daily_totals_end + 1):
            row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
            if "Our Compliments" in row_str or "Walmart" in row_str or "Loblaws" in row_str or "Eyking" in row_str:
                header_row = idx
                break
        
        if header_row is None:
            print("❌ No header row found")
            return
        
        print(f"Header row: {header_row}")
        print(f"Data rows: {header_row + 1} to {daily_totals_end}")
        
        # Show header row in detail
        print(f"\n--- Header Row Details ---")
        header_row_data = df.iloc[header_row]
        for col_idx, cell in enumerate(header_row_data):
            if pd.notna(cell) and str(cell).strip():
                print(f"  Column {col_idx}: '{cell}'")
        
        # Show ALL data rows in detail
        print(f"\n--- ALL Data Rows Details ---")
        for idx in range(header_row + 1, daily_totals_end + 1):
            row = df.iloc[idx]
            row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
            
            if not any(v.strip() for v in row_values):
                continue
            
            print(f"\nRow {idx}:")
            for col_idx, val in enumerate(row_values):
                if val.strip():
                    print(f"  Col {col_idx}: '{val}'")
            
            # Test what the current parser would extract
            print(f"  Current parser would extract:")
            _test_thurs_parsing_week32(row_values, idx)
        
    except Exception as e:
        print(f"Error: {e}")

def _test_thurs_parsing_week32(row_values, idx):
    """Test Thursday parsing logic for Week 32"""
    
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                print(f"    Our Compliments: {row_values[2]} = {qty} boxes")
            else:
                print(f"    Our Compliments: {row_values[2]} = {qty} boxes (ZERO - skipped)")
        except ValueError:
            print(f"    Our Compliments: Invalid quantity '{row_values[1]}'")
    else:
        print(f"    Our Compliments: Missing data - Col 1: '{row_values[1] if len(row_values) > 1 else 'N/A'}', Col 2: '{row_values[2] if len(row_values) > 2 else 'N/A'}'")
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                print(f"    Walmart: {row_values[5]} = {qty} boxes")
            else:
                print(f"    Walmart: {row_values[5]} = {qty} boxes (ZERO - skipped)")
        except ValueError:
            print(f"    Walmart: Invalid quantity '{row_values[4]}'")
    else:
        print(f"    Walmart: Missing data - Col 4: '{row_values[4] if len(row_values) > 4 else 'N/A'}', Col 5: '{row_values[5] if len(row_values) > 5 else 'N/A'}'")
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                print(f"    Loblaws: {row_values[8]} = {qty} boxes")
            else:
                print(f"    Loblaws: {row_values[8]} = {qty} boxes (ZERO - skipped)")
        except ValueError:
            print(f"    Loblaws: Invalid quantity '{row_values[7]}'")
    else:
        print(f"    Loblaws: Missing data - Col 7: '{row_values[7] if len(row_values) > 7 else 'N/A'}', Col 8: '{row_values[8] if len(row_values) > 8 else 'N/A'}'")
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                print(f"    Eyking: {row_values[11]} = {qty} boxes")
            else:
                print(f"    Eyking: {row_values[11]} = {qty} boxes (ZERO - skipped)")
        except ValueError:
            print(f"    Eyking: Invalid quantity '{row_values[10]}'")
    else:
        print(f"    Eyking: Missing data - Col 10: '{row_values[10] if len(row_values) > 10 else 'N/A'}', Col 11: '{row_values[11] if len(row_values) > 11 else 'N/A'}'")

if __name__ == "__main__":
    debug_thursday_week32()
