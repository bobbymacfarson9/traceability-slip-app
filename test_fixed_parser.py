import pandas as pd
import numpy as np
from pathlib import Path
from egg_packing_predictor_universal import parse_daily_totals_universal

def test_fixed_parser():
    """Test the fixed parser on Wednesday and Thursday"""
    print("=== TESTING FIXED PARSER ===")
    
    test_file = Path("Week 24 Loading Slip 2025.xlsx")
    if not test_file.exists():
        print(f"Test file {test_file} not found")
        return
    
    for day in ["Wed", "Thurs"]:
        print(f"\n{'='*50}")
        print(f"TESTING FIXED {day.upper()} PARSER")
        print(f"{'='*50}")
        
        try:
            result = parse_daily_totals_universal(test_file, day)
            
            if not result.empty:
                print(f"✅ Found {len(result)} products:")
                total_boxes = 0
                for _, row in result.iterrows():
                    print(f"  {row['product']:<30} {row['boxes']:>6} boxes")
                    total_boxes += row['boxes']
                print(f"\nTotal boxes: {total_boxes}")
            else:
                print(f"❌ No products found for {day}")
                
        except Exception as e:
            print(f"Error testing {day}: {e}")

if __name__ == "__main__":
    test_fixed_parser()
