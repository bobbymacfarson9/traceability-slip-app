import pandas as pd
import numpy as np
from pathlib import Path

def examine_daily_totals_structure():
    """Examine the exact structure of the Daily Totals section"""
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== EXAMINING DAILY TOTALS STRUCTURE ===")
    print(f"File: {test_file}")
    
    # Read the Monday sheet
    df = pd.read_excel(test_file, sheet_name="Mon", header=None)
    
    # Find the Daily Totals section
    daily_totals_start = None
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        if "DAILY TOTALS" in row_str.upper():
            daily_totals_start = idx
            break
    
    if daily_totals_start is None:
        print("No DAILY TOTALS found")
        return
    
    print(f"Found DAILY TOTALS at row {daily_totals_start}")
    
    # Show the structure around Daily Totals
    print(f"\n=== DAILY TOTALS SECTION STRUCTURE ===")
    for i in range(daily_totals_start, min(daily_totals_start + 20, len(df))):
        row = df.iloc[i]
        row_str = " | ".join(f"{j}:{str(cell)}" for j, cell in enumerate(row.values) if pd.notna(cell))
        marker = " <-- DAILY TOTALS" if i == daily_totals_start else ""
        print(f"Row {i}: {row_str}{marker}")
        
        # Stop at Small Tally or Carts
        if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper():
            break
    
    # Let's also look at the original parser results to compare
    print(f"\n=== COMPARING WITH ORIGINAL PARSER ===")
    from fixed_daily_totals_parser import parse_daily_totals_only
    original_result = parse_daily_totals_only(test_file, "Mon")
    
    print(f"Original parser found {len(original_result)} products:")
    for _, row in original_result.iterrows():
        print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
    print(f"Original total: {original_result['boxes'].sum()}")
    
    # Let's manually examine what the correct totals should be
    print(f"\n=== MANUAL EXAMINATION OF ROW 69 ===")
    row_69 = df.iloc[69]
    print(f"Row 69 values: {list(row_69.values)}")
    
    # Let's look at the pattern more carefully
    print(f"\n=== ANALYZING DATA PATTERN ===")
    for i in range(69, 79):  # Rows 69-78
        row = df.iloc[i]
        row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
        print(f"Row {i}: {row_values}")

if __name__ == "__main__":
    examine_daily_totals_structure()
