import pandas as pd
from pathlib import Path

def test_comprehensive_parsing():
    """Test parsing ALL sections of the Excel file to find missing customer data"""
    
    # Test on Week 24, 2025 Monday sheet
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== COMPREHENSIVE PARSING TEST ===")
    print(f"Testing file: {test_file}")
    
    # Read the Monday sheet
    df = pd.read_excel(test_file, sheet_name="Mon", header=None)
    print(f"Sheet dimensions: {df.shape}")
    
    # Look for all potential customer sections
    print("\n=== SEARCHING FOR CUSTOMER SECTIONS ===")
    
    # Search for customer names in the data
    customer_keywords = ['lob', 'eyk', 'sobeys', 'metro', 'walmart', 'wal', 'north sydney', 'sydney river']
    
    for keyword in customer_keywords:
        print(f"\nSearching for '{keyword}':")
        for idx, row in df.iterrows():
            row_str = " ".join(str(cell).lower() for cell in row.values if pd.notna(cell))
            if keyword.lower() in row_str:
                print(f"  Row {idx}: {row.values[:5]}")  # Show first 5 columns
    
    # Look for numbered sections (like "4. Sobeys - North Sydney")
    print(f"\n=== SEARCHING FOR NUMBERED SECTIONS ===")
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        if re.search(r'^\d+\.', row_str.strip()):
            print(f"  Row {idx}: {row.values[:5]}")
    
    # Show a broader view of the data structure
    print(f"\n=== DATA STRUCTURE OVERVIEW ===")
    print("First 20 rows:")
    for idx in range(min(20, len(df))):
        row = df.iloc[idx]
        non_empty = [str(cell) for cell in row.values if pd.notna(cell) and str(cell).strip()]
        if non_empty:
            print(f"  Row {idx}: {non_empty[:3]}")  # Show first 3 non-empty cells
    
    print(f"\nRows 60-80 (around Daily Totals):")
    for idx in range(60, min(80, len(df))):
        row = df.iloc[idx]
        non_empty = [str(cell) for cell in row.values if pd.notna(cell) and str(cell).strip()]
        if non_empty:
            print(f"  Row {idx}: {non_empty[:3]}")

if __name__ == "__main__":
    import re
    test_comprehensive_parsing()
