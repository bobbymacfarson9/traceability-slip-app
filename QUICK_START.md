# Quick Start Guide - Pallet Optimizer

## Immediate Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Process a Single File
```bash
python pallet_optimizer.py "Week 1 Loading Slip 2025.xlsx"
```

### 3. Process All Files
```bash
python batch_process.py
```

### 4. Run Examples
```bash
python example_usage.py
```

## What You Get

### Console Output
- Detailed pallet plan summary
- Utilization statistics
- Validation results

### Excel Files
- **Pallet Plan Sheet**: Detailed breakdown of each pallet
- **Summary Sheet**: Overall statistics and configuration

## Key Features

✅ **NFLD Orders**: Automatically handled with 48-unit pallets  
✅ **Product Sizing**: Configurable rules for different products  
✅ **Truck Capacity**: Validates against 12-pallet limit  
✅ **Optimization**: Combines small orders efficiently  
✅ **Validation**: Checks all business rules  
✅ **Excel Output**: Professional formatting with summaries  

## Configuration

All parameters are in `pallet_optimizer.py`:
```python
class PalletConfig:
    STANDARD_PALLET_CAPACITY = 48    # Change pallet size
    TRUCK_CAPACITY = 12              # Change truck capacity
    PRODUCT_SIZING = {               # Modify product rules
        'Nova 30 pack': 2,
        'SV/Loblaws 30 pack': 2,
        # ... more products
    }
```

## Troubleshooting

**"No order items found"**
- Check file has Mon, Tues, Wed, Thurs, Fri, NFLD sheets
- Verify data format matches expected structure

**"Validation errors"**
- Review errors in Summary sheet
- Check configuration parameters

**"File not found"**
- Ensure file path is correct
- Check file permissions

## Support

- Check console output for detailed error messages
- Review validation errors in Excel Summary sheet
- Verify input file format matches expected structure 