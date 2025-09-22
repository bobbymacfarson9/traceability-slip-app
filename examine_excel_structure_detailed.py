import pandas as pd
import numpy as np
from pathlib import Path

def examine_excel_structure_detailed():
    """Examine the Excel structure to understand where ALL the data is"""
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== DETAILED EXCEL STRUCTURE EXAMINATION ===")
    print(f"File: {test_file}")
    
    # Read the Monday sheet
    df = pd.read_excel(test_file, sheet_name="Mon", header=None)
    print(f"\nMonday sheet has {len(df)} rows and {len(df.columns)} columns")
    
    # Look for ALL potential data sections
    print("\n=== SEARCHING FOR ALL DATA SECTIONS ===")
    
    # Search for various patterns that might indicate data sections
    patterns_to_find = [
        "DAILY TOTALS",
        "SMALL TALLY", 
        "CARTS",
        "Our Compliments",
        "WAL", "WALMART",
        "LOB", "LOBLAWS", 
        "EYK", "EYKING",
        "SOBEYS",
        "METRO",
        "SUPERSTORE",
        "FOODLAND",
        "GIANT TIGER"
    ]
    
    found_sections = {}
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        row_str_upper = row_str.upper()
        
        for pattern in patterns_to_find:
            if pattern.upper() in row_str_upper:
                if pattern not in found_sections:
                    found_sections[pattern] = []
                found_sections[pattern].append((idx, row_str))
    
    # Display found sections
    for pattern, occurrences in found_sections.items():
        print(f"\n--- {pattern} ---")
        for idx, row_str in occurrences:
            print(f"  Row {idx}: {row_str}")
    
    # Now let's look at the actual data structure around these sections
    print("\n=== EXAMINING DATA AROUND KEY SECTIONS ===")
    
    # Look around DAILY TOTALS
    if "DAILY TOTALS" in found_sections:
        daily_totals_row = found_sections["DAILY TOTALS"][0][0]
        print(f"\n--- DATA AROUND DAILY TOTALS (Row {daily_totals_row}) ---")
        start = max(0, daily_totals_row - 5)
        end = min(len(df), daily_totals_row + 20)
        
        for i in range(start, end):
            row = df.iloc[i]
            row_str = " | ".join(str(cell) for cell in row.values if pd.notna(cell))
            marker = " <-- DAILY TOTALS" if i == daily_totals_row else ""
            print(f"  Row {i}: {row_str}{marker}")
    
    # Look for numbered sections (like "1. Giant Tiger", "2. Sobeys", etc.)
    print(f"\n--- SEARCHING FOR NUMBERED SECTIONS ---")
    numbered_sections = []
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        # Look for patterns like "1.", "2.", "3.", etc.
        if re.match(r'^\d+\.', row_str.strip()):
            numbered_sections.append((idx, row_str))
            print(f"  Row {idx}: {row_str}")
    
    # Look for customer-specific data blocks
    print(f"\n--- SEARCHING FOR CUSTOMER DATA BLOCKS ---")
    customer_keywords = ["WAL", "LOB", "EYK", "SOBEYS", "METRO", "SUPERSTORE", "FOODLAND", "GIANT TIGER"]
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        row_str_upper = row_str.upper()
        
        for keyword in customer_keywords:
            if keyword in row_str_upper and len(row_str.strip()) > 3:
                print(f"  Row {idx}: {row_str}")
                # Show a few rows after this to see the data structure
                for j in range(1, 6):
                    if idx + j < len(df):
                        next_row = df.iloc[idx + j]
                        next_row_str = " | ".join(str(cell) for cell in next_row.values if pd.notna(cell))
                        if next_row_str.strip():
                            print(f"    +{j}: {next_row_str}")
                break
    
    # Let's also check what the current parser is actually finding
    print(f"\n--- WHAT CURRENT PARSER FINDS ---")
    from fixed_daily_totals_parser import parse_daily_totals_only
    result = parse_daily_totals_only(test_file, "Mon")
    print(f"Current parser finds {len(result)} products:")
    for _, row in result.iterrows():
        print(f"  {row['product']}: {row['boxes']} boxes")

import re

if __name__ == "__main__":
    examine_excel_structure_detailed()
