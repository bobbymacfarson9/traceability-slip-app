# universal_daily_totals_parser.py
# This parser handles the different column structures across all days

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

def parse_daily_totals_universal(file_path: Path, sheet: str) -> pd.DataFrame:
    """Parse Daily Totals section handling different column structures per day"""
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
        if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper() or "SPECIALTY" in row_str.upper():
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
        
        # Handle different day structures
        if sheet == "Mon":
            # Monday: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)
            _parse_mon_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Tues":
            # Tuesday: Our Compliments (B,C), Walmart (D,E), Loblaws (H,I), Eyking (K,L)
            _parse_tues_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Wed":
            # Wednesday: Our Compliments (B,C), Walmart (D,E), Loblaws (G,H), Eyking (J,K)
            _parse_wed_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Thurs":
            # Thursday: Our Compliments (A,B), Walmart/Loblaws/Eyking embedded in product names
            _parse_thurs_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Fri":
            # Friday: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)
            _parse_fri_structure(row_values, idx, records, file_name, sheet, week_num, year)
    
    return pd.DataFrame.from_records(records)

def _parse_mon_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Monday structure: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[2], qty))
                print(f"  Row {idx}: {row_values[2]} = {qty} boxes (Our Compliments)")
        except ValueError:
            pass
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[5], qty))
                print(f"  Row {idx}: {row_values[5]} = {qty} boxes (Walmart)")
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[8], qty))
                print(f"  Row {idx}: {row_values[8]} = {qty} boxes (Loblaws)")
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[11], qty))
                print(f"  Row {idx}: {row_values[11]} = {qty} boxes (Eyking)")
        except ValueError:
            pass

def _parse_tues_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Tuesday structure: Our Compliments (B,C), Walmart (D,E), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[2], qty))
                print(f"  Row {idx}: {row_values[2]} = {qty} boxes (Our Compliments)")
        except ValueError:
            pass
    
    # Walmart: Column D (quantity), Column E (product)
    if len(row_values) > 4 and row_values[3].strip() and row_values[4].strip():
        try:
            qty = float(row_values[3])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[4], qty))
                print(f"  Row {idx}: {row_values[4]} = {qty} boxes (Walmart)")
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[8], qty))
                print(f"  Row {idx}: {row_values[8]} = {qty} boxes (Loblaws)")
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[11], qty))
                print(f"  Row {idx}: {row_values[11]} = {qty} boxes (Eyking)")
        except ValueError:
            pass

def _parse_wed_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Wednesday structure: Our Compliments (B,C), Walmart (D,E), Loblaws (G,H), Eyking (J,K)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[2], qty))
                print(f"  Row {idx}: {row_values[2]} = {qty} boxes (Our Compliments)")
        except ValueError:
            pass
    
    # Walmart: Column D (quantity), Column E (product)
    if len(row_values) > 4 and row_values[3].strip() and row_values[4].strip():
        try:
            qty = float(row_values[3])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[4], qty))
                print(f"  Row {idx}: {row_values[4]} = {qty} boxes (Walmart)")
        except ValueError:
            pass
    
    # Loblaws: Column G (product), Column H (quantity)
    if len(row_values) > 8 and row_values[6].strip() and row_values[7].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[6], qty))
                print(f"  Row {idx}: {row_values[6]} = {qty} boxes (Loblaws)")
        except ValueError:
            pass
    
    # Eyking: Column J (quantity), Column K (product)
    if len(row_values) > 11 and row_values[9].strip() and row_values[10].strip():
        try:
            qty = float(row_values[9])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[10], qty))
                print(f"  Row {idx}: {row_values[10]} = {qty} boxes (Eyking)")
        except ValueError:
            pass

def _parse_thurs_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Thursday structure: Our Compliments (A,B), Walmart/Loblaws/Eyking embedded in product names"""
    # Our Compliments: Column A (quantity), Column B (product)
    if len(row_values) > 1 and row_values[0].strip() and row_values[1].strip():
        try:
            qty = float(row_values[0])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[1], qty))
                print(f"  Row {idx}: {row_values[1]} = {qty} boxes (Our Compliments)")
        except ValueError:
            pass
    
    # Walmart/Loblaws/Eyking: Quantities embedded in product names (e.g., "23 Wal GV Xlrg")
    for i, val in enumerate(row_values):
        if val.strip() and not val.isdigit():
            # Look for pattern: "number product_name"
            match = re.match(r'^(\d+)\s+(.+)$', val.strip())
            if match:
                qty = int(match.group(1))
                product = match.group(2)
                if qty > 0:
                    records.append(_create_record(file_name, sheet, week_num, year, product, qty))
                    print(f"  Row {idx}: {product} = {qty} boxes (Embedded)")

def _parse_fri_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Friday structure: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[2], qty))
                print(f"  Row {idx}: {row_values[2]} = {qty} boxes (Our Compliments)")
        except ValueError:
            pass
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[5], qty))
                print(f"  Row {idx}: {row_values[5]} = {qty} boxes (Walmart)")
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[8], qty))
                print(f"  Row {idx}: {row_values[8]} = {qty} boxes (Loblaws)")
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                records.append(_create_record(file_name, sheet, week_num, year, row_values[11], qty))
                print(f"  Row {idx}: {row_values[11]} = {qty} boxes (Eyking)")
        except ValueError:
            pass

def _create_record(file_name, sheet, week_num, year, product, qty):
    """Create a standardized record"""
    return {
        "file": file_name,
        "day": sheet,
        "product": product,
        "boxes": int(qty),
        "week_num": week_num,
        "year": year
    }

def test_universal_parser():
    """Test the universal parser on all days of Week 24, 2025"""
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    print("=== TESTING UNIVERSAL DAILY TOTALS PARSER ===")
    print(f"Testing file: {test_file}")
    
    all_results = []
    
    for day in ["Mon", "Tues", "Wed", "Thurs", "Fri"]:
        print(f"\n--- {day} ---")
        result = parse_daily_totals_universal(test_file, day)
        all_results.append(result)
        
        print(f"Parsed {len(result)} products from {day}:")
        for _, row in result.iterrows():
            print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
        
        if not result.empty:
            print(f"Total boxes for {day}: {result['boxes'].sum()}")
        else:
            print(f"Total boxes for {day}: 0")
    
    # Combine all results
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        print(f"\n=== COMBINED RESULTS ===")
        print(f"Total products across all days: {len(combined)}")
        print(f"Total boxes across all days: {combined['boxes'].sum()}")
        
        # Show unique products
        unique_products = combined['product'].unique()
        print(f"Unique products: {len(unique_products)}")
        for product in sorted(unique_products):
            total_qty = combined[combined['product'] == product]['boxes'].sum()
            print(f"  {product:<30} {total_qty:>6} total boxes")
    
    return all_results

if __name__ == "__main__":
    test_universal_parser()
