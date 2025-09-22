# comprehensive_egg_parser.py
# Python 3.10+
# pip install pandas openpyxl

from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


def extract_week_year(filename):
    """Extract week number and year from filename"""
    match = re.search(r'Week\s+(\d+).*?(\d{4})', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def coerce_qty(cell):
    """Convert cell to numeric quantity"""
    try:
        if pd.isna(cell):
            return np.nan
        if isinstance(cell, str):
            s = cell.strip()
            if s == "":
                return np.nan
        return pd.to_numeric(cell, errors="coerce")
    except Exception:
        return np.nan


def parse_customer_section(df: pd.DataFrame, start_row: int, end_row: int, section_name: str, file_name: str, day: str) -> pd.DataFrame:
    """Parse a customer section and extract product/quantity data"""
    records = []
    
    for idx in range(start_row, min(end_row + 1, len(df))):
        row = df.iloc[idx]
        
        # Skip empty rows
        if row.isna().all():
            continue
            
        # Look for product/quantity patterns
        # Pattern 1: [qty, product] or [qty, qty, product]
        # Pattern 2: [product, qty] 
        # Pattern 3: [qty, product, qty] (pieces, boxes)
        
        row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
        non_empty = [v for v in row_values if v.strip()]
        
        if len(non_empty) < 2:
            continue
            
        # Try different column combinations
        product = None
        qty = None
        
        # Check if this looks like a product row (has numbers and text)
        has_numbers = any(coerce_qty(v) > 0 for v in row_values)
        has_text = any(v.strip() and not v.replace('.', '').replace('-', '').isdigit() for v in row_values)
        
        if not (has_numbers and has_text):
            continue
            
        # Extract product name (longest text that's not a number)
        text_candidates = []
        for v in row_values:
            if v.strip() and not v.replace('.', '').replace('-', '').isdigit():
                # Skip common non-product words
                if v.lower() not in ['pcs', 'case', 'cases', 'ea', 'each', 'pk', 'pack', 'pks', 'po#', 'box total']:
                    text_candidates.append(v.strip())
        
        if text_candidates:
            product = max(text_candidates, key=len)
        
        # Extract quantity (look for the largest reasonable number)
        qty_candidates = []
        for v in row_values:
            q = coerce_qty(v)
            if not pd.isna(q) and q > 0 and q < 10000:  # Reasonable range
                qty_candidates.append(q)
        
        if qty_candidates:
            # If multiple quantities, prefer the larger one (likely boxes vs pieces)
            qty = max(qty_candidates)
        
        if product and qty and qty > 0:
            records.append({
                "file": file_name,
                "day": day,
                "section": section_name,
                "product": product,
                "qty": float(qty)
            })
    
    return pd.DataFrame.from_records(records)


def parse_sheet_comprehensive(file_path: Path, sheet: str) -> pd.DataFrame:
    """Parse all sections of a sheet comprehensively"""
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    file_name = file_path.name
    week_num, year = extract_week_year(file_name)
    
    all_records = []
    
    # Find all customer sections
    customer_sections = []
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        
        # Look for numbered customer sections
        if re.search(r'^\d+\.', row_str.strip()):
            # This is a customer section header
            customer_sections.append((idx, row_str.strip()))
    
    # Parse each customer section
    for i, (start_idx, section_name) in enumerate(customer_sections):
        # Find end of this section (start of next section or end of data)
        end_idx = len(df) - 1
        if i + 1 < len(customer_sections):
            end_idx = customer_sections[i + 1][0] - 1
        
        # Parse this customer section
        section_df = parse_customer_section(df, start_idx, end_idx, section_name, file_name, sheet)
        if not section_df.empty:
            all_records.append(section_df)
    
    # Also parse the Daily Totals section (existing logic)
    daily_totals_start = None
    daily_totals_end = None
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        if "DAILY TOTALS" in row_str.upper():
            daily_totals_start = idx + 1
        elif daily_totals_start is not None and ("SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper()):
            daily_totals_end = idx - 1
            break
    
    if daily_totals_start is not None:
        if daily_totals_end is None:
            daily_totals_end = len(df) - 1
        
        daily_totals_df = parse_customer_section(df, daily_totals_start, daily_totals_end, "DAILY_TOTALS", file_name, sheet)
        if not daily_totals_df.empty:
            all_records.append(daily_totals_df)
    
    # Combine all records
    if all_records:
        result = pd.concat(all_records, ignore_index=True)
        result['week_num'] = week_num
        result['year'] = year
        return result
    else:
        return pd.DataFrame(columns=["file", "day", "section", "product", "qty", "week_num", "year"])


def parse_file_comprehensive(file_path: Path, days: List[str] = ["Mon", "Tues", "Wed", "Thurs", "Fri"]) -> pd.DataFrame:
    """Parse all sections of all sheets in a file"""
    frames = []
    
    for day in days:
        try:
            df = parse_sheet_comprehensive(file_path, day)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"Error parsing {file_path} sheet {day}: {e}")
    
    if frames:
        return pd.concat(frames, ignore_index=True)
    else:
        return pd.DataFrame(columns=["file", "day", "section", "product", "qty", "week_num", "year"])


def parse_folder_comprehensive(root: Path | str = ".", glob: str = "Week *Loading Slip*.xlsx") -> pd.DataFrame:
    """Parse all files in folder comprehensively"""
    files = sorted(Path(root).glob(glob))
    frames = []
    
    for f in files:
        print(f"Parsing {f.name}...")
        df = parse_file_comprehensive(f)
        if not df.empty:
            frames.append(df)
    
    if not frames:
        return pd.DataFrame(columns=["file", "day", "section", "product", "qty", "week_num", "year"])
    
    result = pd.concat(frames, ignore_index=True)
    return result.sort_values(['year', 'week_num', 'file', 'day']).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description="Comprehensive parser for all customer sections in loading slips")
    ap.add_argument("--root", default=".", help="Folder containing week files")
    ap.add_argument("--glob", default="Week *Loading Slip*.xlsx", help="Glob pattern for week files")
    ap.add_argument("--outdir", default="./comprehensive_parsed", help="Output directory for CSVs")
    ap.add_argument("--test-file", help="Test on a single file first")
    args = ap.parse_args()

    root = Path(args.root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.test_file:
        # Test on single file
        test_file = Path(args.test_file)
        if test_file.exists():
            print(f"Testing comprehensive parser on {test_file}")
            result = parse_file_comprehensive(test_file)
            print(f"Parsed {len(result)} records")
            print("\nSample results:")
            print(result.head(20).to_string(index=False))
            
            # Save test results
            test_output = outdir / f"{test_file.stem}_comprehensive_test.csv"
            result.to_csv(test_output, index=False)
            print(f"\nSaved test results to: {test_output}")
        else:
            print(f"Test file {test_file} not found")
    else:
        # Parse all files
        print("Parsing all files comprehensively...")
        all_data = parse_folder_comprehensive(root, args.glob)
        
        master_path = outdir / "all_comprehensive_parsed.csv"
        all_data.to_csv(master_path, index=False)
        
        print(f"\nWrote master CSV: {master_path}")
        print(f"Total rows parsed: {len(all_data)}")
        print(f"Files processed: {all_data['file'].nunique()}")
        print(f"Sections found: {sorted(all_data['section'].unique())}")
        
        if not all_data.empty:
            print("\nSample (first 20 rows):")
            print(all_data.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
