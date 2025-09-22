# Pallet Optimizer for Hilly Acres Farm Ltd.

A Python script that reads Loading Slip Excel files and generates optimized Pallet Plans based on specific business rules and constraints.

## Features

- **Automatic Data Parsing**: Reads complex Excel Loading Slip files with multiple sheets
- **NFLD Order Handling**: Special handling for NFLD orders (must be on separate pallets of exactly 48 units)
- **Product Sizing Rules**: Configurable sizing rules for different product types
- **Pallet Optimization**: Intelligent pallet loading with capacity constraints
- **Validation**: Comprehensive validation of pallet plans against business rules
- **Excel Output**: Generates detailed Pallet Plan Excel files with summary sheets

## Business Rules

### Core Constraints
- **NFLD Orders**: Must remain together and can only go on pallets of exactly 48 units
- **Other Orders**: Default truck capacity is 12 pallets (configurable)
- **Standard Pallet Capacity**: 48 boxes (configurable)
- **Loading Order**: Stops load in ascending StopNumber order

### Product Sizing Rules
- **Nova 30 pack & SV/Loblaws 30 pack**: 2 units per box
- **OC 30 pack**: 1 unit per box
- **ED XL 18 pack**: 1 unit per box (uses cart capacity of 24)
- **Dozens**: 1 unit per box (uses cart capacity of 24)
- **Default**: 1 unit per box

### Splitting Rules
- If a single stop has more than 48 boxes, split across multiple pallets
- Small orders can be combined on the same pallet if they load on the same truck run

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Installation**:
   ```bash
   python pallet_optimizer.py --help
   ```

## Usage

### Basic Usage
```bash
python pallet_optimizer.py "Week 1 Loading Slip 2025.xlsx"
```

### Specify Output File
```bash
python pallet_optimizer.py "Week 1 Loading Slip 2025.xlsx" "Week 1 Pallet Plan.xlsx"
```

### Example Output
The script will generate:
1. **Console Summary**: Detailed pallet plan summary with utilization statistics
2. **Excel File**: Two sheets:
   - **Pallet Plan**: Detailed breakdown of each pallet with items and utilization
   - **Summary**: Overall statistics and configuration parameters

## Configuration

All parameters are configurable in the `PalletConfig` class:

```python
class PalletConfig:
    STANDARD_PALLET_CAPACITY = 48    # Standard pallet capacity
    TRUCK_CAPACITY = 12              # Number of pallets per truck
    CART_CAPACITY = 24               # Cart capacity for special products
    
    # Product sizing rules
    PRODUCT_SIZING = {
        'Nova 30 pack': 2,
        'SV/Loblaws 30 pack': 2,
        'OC 30 pack': 1,
        'ED XL 18 pack': 1,
        'dozens': 1,
        'default': 1
    }
```

## Input File Format

The script expects Loading Slip Excel files with the following structure:

### Sheet Structure
- **Mon, Tues, Wed, Thurs, Fri**: Regular delivery sheets
- **NFLD**: Special NFLD orders sheet
- **Total**: Summary sheet (not processed)

### Data Format
Each sheet contains:
- **Stop Number**: Integer defining delivery sequence
- **Product Type**: Product description
- **Boxes**: Integer count of boxes
- **Region**: Determined automatically based on product type

## Output Format

### Pallet Plan Sheet
| Column | Description |
|--------|-------------|
| Pallet # | Pallet identifier |
| Region | NFLD or Other |
| Stop # | Delivery stop number |
| Product Type | Product description |
| Boxes | Number of boxes |
| Units | Calculated units based on sizing rules |
| Used Capacity | Units used on this pallet |
| Total Capacity | Pallet capacity |
| Utilization % | Percentage of capacity used |
| Unused Capacity | Remaining capacity |

### Summary Sheet
- Total pallets required
- Overall utilization percentage
- Total unused capacity
- NFLD vs Other pallet counts
- Configuration parameters
- Validation errors (if any)

## Validation

The script validates against:
- NFLD pallets must be exactly 48 units
- NFLD pallets must only contain NFLD items
- No pallet exceeds capacity
- Truck capacity constraints
- Product sizing rules

## Error Handling

- **File Not Found**: Clear error message with usage instructions
- **Invalid Data**: Graceful handling of missing or invalid data
- **Validation Errors**: Detailed error messages in summary
- **Logging**: Comprehensive logging for debugging

## Troubleshooting

### Common Issues

1. **"No order items found"**
   - Check that the Excel file has the expected sheet names (Mon, Tues, etc.)
   - Verify data is in the expected format

2. **"Validation errors"**
   - Review the error messages in the Summary sheet
   - Check configuration parameters

3. **"File not found"**
   - Ensure the file path is correct
   - Check file permissions

### Debug Mode
Enable detailed logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## Extending the Script

### Adding New Product Types
1. Add to `PRODUCT_SIZING` in `PalletConfig`
2. Update `determine_region()` if needed

### Modifying Business Rules
1. Update constraints in `validate_pallet_plan()`
2. Modify optimization logic in `optimize_pallets()`

### Custom Output Formats
1. Modify `create_pallet_plan_excel()` for different Excel formats
2. Add new output functions for different file types

## License

This script is provided as-is for Hilly Acres Farm Ltd. usage.

## Support

For issues or questions:
1. Check the console output for error messages
2. Review the validation errors in the Summary sheet
3. Verify input file format matches expected structure 