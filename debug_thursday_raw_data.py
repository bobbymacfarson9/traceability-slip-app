import pandas as pd
import numpy as np
from pathlib import Path

def debug_thursday_raw_data():
    """Debug Thursday raw data to see what's actually in the Excel vs what parser finds"""
    print("=== DEBUGGING THURSDAY RAW DATA ===")
    
    # Test both weeks
    for week_file, week_name in [("Week 24 Loading Slip 2025.xlsx", "Week 24"), ("Week 32 Loading Slip 2025.xlsx", "Week 32")]:
        print(f"\n{'='*60}")
        print(f"DEBUGGING {week_name.upper()} THURSDAY")
        print(f"{'='*60}")
        
        test_file = Path(week_file)
        if not test_file.exists():
            print(f"Test file {test_file} not found")
            continue
        
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
                    print(f"Found 'DAILY TOTALS' at row {idx}")
                    break
            
            if daily_totals_start is None:
                print(f"❌ No 'DAILY TOTALS' found in {week_name}")
                continue
            
            # Find the end
            for idx in range(daily_totals_start, len(df)):
                row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper():
                    daily_totals_end = idx - 1
                    print(f"Found end marker at row {idx}")
                    break
            
            if daily_totals_end is None:
                daily_totals_end = len(df) - 1
                print(f"No end marker found, using end of sheet: row {daily_totals_end}")
            
            print(f"Daily Totals section: rows {daily_totals_start} to {daily_totals_end}")
            
            # Find header row
            header_row = None
            for idx in range(daily_totals_start, daily_totals_end + 1):
                row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
                if "Our Compliments" in row_str or "Walmart" in row_str or "Loblaws" in row_str or "Eyking" in row_str:
                    header_row = idx
                    print(f"Found header row at {idx}")
                    break
            
            if header_row is None:
                print(f"❌ No header row found in {week_name}")
                continue
            
            # Show header row in detail
            print(f"\n--- Header Row Details (Row {header_row}) ---")
            header_row_data = df.iloc[header_row]
            for col_idx, cell in enumerate(header_row_data):
                if pd.notna(cell) and str(cell).strip():
                    print(f"  Column {col_idx}: '{cell}'")
            
            # Show ALL data rows with detailed analysis
            print(f"\n--- ALL Data Rows with Manual Analysis ---")
            manual_products = []
            
            for idx in range(header_row + 1, daily_totals_end + 1):
                row = df.iloc[idx]
                row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
                
                if not any(v.strip() for v in row_values):
                    continue
                
                print(f"\nRow {idx}:")
                for col_idx, val in enumerate(row_values):
                    if val.strip():
                        print(f"  Col {col_idx}: '{val}'")
                
                # Manual analysis of what should be extracted
                print(f"  Manual analysis:")
                _manual_analyze_row(row_values, idx, manual_products)
            
            # Summary of what should be found
            print(f"\n--- Manual Analysis Summary ---")
            print(f"Products that should be found: {len(manual_products)}")
            for product_info in manual_products:
                print(f"  {product_info}")
            
            # Now test what the parser actually finds
            print(f"\n--- Parser Results ---")
            from egg_packing_predictor_universal import parse_daily_totals_universal
            parser_result = parse_daily_totals_universal(test_file, "Thurs")
            if not parser_result.empty:
                print(f"Parser found {len(parser_result)} products:")
                for _, row in parser_result.iterrows():
                    print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
            else:
                print("Parser found no products")
                
        except Exception as e:
            print(f"Error processing {week_name}: {e}")

def _manual_analyze_row(row_values, idx, manual_products):
    """Manually analyze what should be extracted from a row"""
    
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                manual_products.append(f"Our Compliments: {row_values[2]} = {qty} boxes")
                print(f"    Our Compliments: {row_values[2]} = {qty} boxes")
            else:
                print(f"    Our Compliments: {row_values[2]} = {qty} boxes (ZERO - should be skipped)")
        except ValueError:
            print(f"    Our Compliments: Invalid quantity '{row_values[1]}'")
    else:
        print(f"    Our Compliments: No data")
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                manual_products.append(f"Walmart: {row_values[5]} = {qty} boxes")
                print(f"    Walmart: {row_values[5]} = {qty} boxes")
            else:
                print(f"    Walmart: {row_values[5]} = {qty} boxes (ZERO - should be skipped)")
        except ValueError:
            print(f"    Walmart: Invalid quantity '{row_values[4]}'")
    else:
        print(f"    Walmart: No data")
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                manual_products.append(f"Loblaws: {row_values[8]} = {qty} boxes")
                print(f"    Loblaws: {row_values[8]} = {qty} boxes")
            else:
                print(f"    Loblaws: {row_values[8]} = {qty} boxes (ZERO - should be skipped)")
        except ValueError:
            print(f"    Loblaws: Invalid quantity '{row_values[7]}'")
    else:
        print(f"    Loblaws: No data")
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                manual_products.append(f"Eyking: {row_values[11]} = {qty} boxes")
                print(f"    Eyking: {row_values[11]} = {qty} boxes")
            else:
                print(f"    Eyking: {row_values[11]} = {qty} boxes (ZERO - should be skipped)")
        except ValueError:
            print(f"    Eyking: Invalid quantity '{row_values[10]}'")
    else:
        print(f"    Eyking: No data")

if __name__ == "__main__":
    debug_thursday_raw_data()
