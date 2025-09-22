import pandas as pd
from pathlib import Path

def examine_excel_structure():
    """Examine the actual Excel file structure to understand the data layout"""
    
    # Find the most recent Excel file
    excel_files = list(Path('.').glob('Week *Loading Slip*.xlsx'))
    if not excel_files:
        print("No Excel files found!")
        return
    
    # Use the most recent file
    excel_file = sorted(excel_files)[-1]
    print(f"Examining: {excel_file}")
    print("=" * 60)
    
    # Read the Monday sheet
    try:
        monday_df = pd.read_excel(excel_file, sheet_name='Mon', header=None)
        print(f"Monday sheet dimensions: {monday_df.shape}")
        print()
        
        # Look for the "Our Compliments" or "DAILY TOTALS" section
        print("=== LOOKING FOR DAILY TOTALS SECTION ===")
        for idx, row in monday_df.iterrows():
            row_str = " ".join([str(cell) for cell in row.values if pd.notna(cell)])
            if any(keyword in row_str.lower() for keyword in ['our compliments', 'daily totals']):
                print(f"Row {idx}: {row_str}")
                
                # Show the next 20 rows to see the structure
                print(f"\nNext 20 rows after row {idx}:")
                for i in range(idx, min(idx + 20, len(monday_df))):
                    next_row = monday_df.iloc[i]
                    next_row_str = " ".join([str(cell) for cell in next_row.values if pd.notna(cell)])
                    if next_row_str.strip():
                        print(f"  Row {i}: {next_row_str}")
                break
        
        print("\n=== LOOKING FOR CUSTOMER NAMES ===")
        # Search for customer names in the entire sheet
        customer_keywords = ['walmart', 'loblaws', 'eiking', 'sobeys', 'metro']
        found_customers = []
        
        for idx, row in monday_df.iterrows():
            for col_idx, cell in enumerate(row):
                if pd.notna(cell) and isinstance(cell, str):
                    cell_lower = cell.lower()
                    for keyword in customer_keywords:
                        if keyword in cell_lower:
                            found_customers.append((idx, col_idx, cell))
                            print(f"Found '{cell}' at row {idx}, col {col_idx}")
        
        if not found_customers:
            print("No customer names found in the sheet")
        
        print("\n=== SAMPLE DATA AROUND CUSTOMER NAMES ===")
        for row_idx, col_idx, customer_name in found_customers[:3]:  # Show first 3
            print(f"\nAround '{customer_name}' (row {row_idx}, col {col_idx}):")
            # Show 5 rows before and after
            for i in range(max(0, row_idx - 5), min(len(monday_df), row_idx + 6)):
                row_data = monday_df.iloc[i]
                row_str = " | ".join([str(cell) for cell in row_data.values if pd.notna(cell)])
                marker = " <-- CUSTOMER" if i == row_idx else ""
                print(f"  Row {i}: {row_str}{marker}")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")

if __name__ == "__main__":
    examine_excel_structure()
