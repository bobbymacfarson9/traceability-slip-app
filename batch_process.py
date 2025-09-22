#!/usr/bin/env python3
"""
Batch processing script for multiple Loading Slip files
"""

import os
import glob
from pallet_optimizer import parse_loading_slip, optimize_pallets, create_pallet_plan_excel, print_pallet_plan_summary

def process_all_files():
    """Process all Loading Slip files in the current directory"""
    
    # Find all Loading Slip files
    loading_slip_files = glob.glob("*Loading Slip*.xlsx")
    
    print(f"Found {len(loading_slip_files)} Loading Slip files:")
    for file in loading_slip_files:
        print(f"  - {file}")
    
    print("\n" + "="*60)
    print("BATCH PROCESSING STARTED")
    print("="*60)
    
    for input_file in loading_slip_files:
        try:
            print(f"\nProcessing: {input_file}")
            
            # Generate output filename
            base_name = input_file.replace(" Loading Slip", "").replace(".xlsx", "")
            output_file = f"{base_name} Pallet Plan.xlsx"
            
            # Parse and optimize
            order_items = parse_loading_slip(input_file)
            
            if not order_items:
                print(f"  No order items found in {input_file}")
                continue
            
            pallet_plan = optimize_pallets(order_items)
            
            # Create Excel output
            create_pallet_plan_excel(pallet_plan, output_file)
            
            print(f"  ✓ Created: {output_file}")
            print(f"  ✓ Total Pallets: {pallet_plan.total_pallets}")
            print(f"  ✓ Utilization: {pallet_plan.total_utilization:.1f}%")
            
        except Exception as e:
            print(f"  ✗ Error processing {input_file}: {e}")
    
    print("\n" + "="*60)
    print("BATCH PROCESSING COMPLETED")
    print("="*60)

if __name__ == "__main__":
    process_all_files() 