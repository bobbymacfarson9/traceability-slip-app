#!/usr/bin/env python3
"""
Convert Loading Slip Excel files to clean CSV format.
This strips out all formatting and keeps just the raw data values.
"""

import pandas as pd
import glob
import os
from pathlib import Path

def convert_excel_to_csv():
    """Convert all Loading Slip Excel files to CSV format"""
    
    print("🔄 CONVERTING EXCEL FILES TO CSV")
    print("="*50)
    
    # Find all Loading Slip files
    loading_slip_files = glob.glob("*Loading Slip*.xlsx")
    
    if not loading_slip_files:
        print("❌ No Loading Slip files found!")
        return
    
    print(f"Found {len(loading_slip_files)} Loading Slip files")
    
    # Create CSV output directory
    csv_dir = Path("CSV_Data")
    csv_dir.mkdir(exist_ok=True)
    
    for file_path in loading_slip_files:
        print(f"\n📖 Converting: {file_path}")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            # Get base filename without extension
            base_name = Path(file_path).stem
            
            # Process each sheet
            for sheet_name in excel_file.sheet_names:
                print(f"  📋 Processing sheet: {sheet_name}")
                
                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                
                # Create CSV filename
                csv_filename = f"{base_name}_{sheet_name}.csv"
                csv_path = csv_dir / csv_filename
                
                # Save as CSV
                df.to_csv(csv_path, index=False, header=False)
                print(f"    ✅ Saved: {csv_filename}")
        
        except Exception as e:
            print(f"  ❌ Error converting {file_path}: {e}")
    
    print(f"\n✅ Conversion complete!")
    print(f"📁 CSV files saved in: {csv_dir}")
    print(f"📊 You can now analyze the CSV files for product types and data structure.")

def analyze_csv_structure():
    """Analyze the converted CSV files to understand the data structure"""
    
    csv_dir = Path("CSV_Data")
    if not csv_dir.exists():
        print("❌ No CSV files found. Run convert_excel_to_csv() first.")
        return
    
    csv_files = list(csv_dir.glob("*.csv"))
    
    print(f"\n🔍 ANALYZING CSV STRUCTURE")
    print("="*50)
    print(f"Found {len(csv_files)} CSV files")
    
    # Analyze a few files to understand structure
    for csv_file in csv_files[:3]:  # Look at first 3 files
        print(f"\n📊 Analyzing: {csv_file.name}")
        
        try:
            df = pd.read_csv(csv_file, header=None)
            print(f"  Shape: {df.shape}")
            print(f"  First 5 rows:")
            print(df.head().to_string())
            
            # Look for product data patterns
            print(f"  Data types in first 10 columns:")
            for i in range(min(10, len(df.columns))):
                non_null_count = df.iloc[:, i].notna().sum()
                print(f"    Column {i}: {non_null_count} non-null values")
        
        except Exception as e:
            print(f"  ❌ Error analyzing {csv_file}: {e}")

def extract_product_types_from_csv():
    """Extract all product types from CSV files"""
    
    csv_dir = Path("CSV_Data")
    if not csv_dir.exists():
        print("❌ No CSV files found. Run convert_excel_to_csv() first.")
        return
    
    csv_files = list(csv_dir.glob("*Mon*.csv"))  # Focus on Monday sheets first
    
    print(f"\n🎯 EXTRACTING PRODUCT TYPES FROM CSV")
    print("="*50)
    
    all_product_types = set()
    product_counts = {}
    
    for csv_file in csv_files:
        print(f"\n📖 Analyzing: {csv_file.name}")
        
        try:
            df = pd.read_csv(csv_file, header=None)
            
            # Look for product data in the sheet
            products_found = set()
            
            # Scan through all cells looking for product names
            for row_idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    cell_value = df.iloc[row_idx, col_idx]
                    
                    if pd.notna(cell_value) and isinstance(cell_value, str):
                        cell_str = str(cell_value).strip()
                        
                        # Look for product names (common patterns)
                        if (len(cell_str) > 2 and 
                            any(keyword in cell_str.lower() for keyword in 
                                ['oc', 'lob', 'nova', 'ed', 'eyk', 'wal', 'box', 'pack', 'xl', 'lg', 'med', 'br'])):
                            
                            products_found.add(cell_str)
                            all_product_types.add(cell_str)
                            
                            if cell_str in product_counts:
                                product_counts[cell_str] += 1
                            else:
                                product_counts[cell_str] = 1
            
            print(f"  ✅ Found {len(products_found)} products: {sorted(products_found)}")
        
        except Exception as e:
            print(f"  ❌ Error analyzing {csv_file}: {e}")
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS")
    print("="*50)
    print(f"Total unique product types: {len(all_product_types)}")
    
    if all_product_types:
        print(f"\n📈 Product Types (sorted by frequency):")
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        for product, count in sorted_products:
            print(f"  • {product} (found in {count} files)")
        
        # Generate configuration code
        print(f"\n⚙️ CONFIGURATION CODE")
        print("="*50)
        print("PRODUCT_SIZING = {")
        
        for product in sorted(all_product_types):
            # Auto-detect if it's likely a double-stack product
            product_lower = product.lower()
            is_double_stack = any(keyword in product_lower for keyword in 
                                ['nova', '30 pack', 'xlrg', 'lrg', '30'])
            
            if is_double_stack:
                print(f"    '{product}': 2,  # Double-stack product")
            else:
                print(f"    '{product}': 1,  # Regular product")
        
        print("    'default': 1  # Default for any product not listed above")
        print("}")
    
    return all_product_types

def main():
    """Main function"""
    print("🎯 Excel to CSV Converter for Pallet Optimizer")
    print("This will convert your Loading Slip files to clean CSV format.")
    
    # Step 1: Convert Excel to CSV
    convert_excel_to_csv()
    
    # Step 2: Analyze CSV structure
    analyze_csv_structure()
    
    # Step 3: Extract product types
    all_products = extract_product_types_from_csv()
    
    if all_products:
        print(f"\n✅ Success! Found {len(all_products)} unique product types.")
        print("📁 Check the CSV_Data folder for the converted files.")
        print("⚙️ Use the configuration code above in your optimizer settings.")
    else:
        print("❌ No product types found. Check the CSV structure.")

if __name__ == "__main__":
    main() 