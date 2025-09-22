# Egg Room Packing Predictor - User Guide

## Quick Start

### Option 1: Use the Batch File (Easiest)
1. Double-click `RUN_PACKING_PREDICTOR.bat`
2. Choose from the menu options
3. Follow the prompts

### Option 2: Use Command Line

## Common Commands

### Get Actual Packing List (When Orders Are Released)
```bash
# Get actuals for Monday from the latest week file
python egg_packing_predictor.py actuals --day Mon

# Get actuals for Tuesday
python egg_packing_predictor.py actuals --day Tues
```

### Forecast Next Week (Thursday Planning)
```bash
# Forecast all weekdays for next week
python egg_packing_predictor.py forecast-next-week --window 8 --alpha 0.7
```

### Forecast Specific Day/Week
```bash
# Forecast Monday for week 36, 2025
python egg_packing_predictor.py forecast-day --day Mon --week 36 --year 2025 --window 8 --alpha 0.7
```

## Understanding the Output

The system shows two columns:
- **product**: The egg product name
- **boxes**: Number of boxes to pack (actual or forecast)

### Sample Output:
```
          product  boxes
        OC 30 Lrg    104
            OC Br      1
            OC Lg     12
  OC Lg Cozy Coop     14
           OC Med      1
           OC Xlg      2
```

## Parameters Explained

- **--window**: Number of recent weeks to use for forecasting (6-8 recommended)
- **--alpha**: Blend weight between recent data and last year's data (0.7 = 70% recent, 30% last year)
- **--no-last-year**: Disable blending with last year's data (use only recent data)

## Workflow Examples

### Thursday Planning (Before Orders Drop)
```bash
# Forecast next week to plan Monday packing
python egg_packing_predictor.py forecast-next-week --window 8 --alpha 0.7
```

### Friday Morning (After Monday Orders Arrive)
```bash
# Get actual Monday packing list
python egg_packing_predictor.py actuals --day Mon
```

### Monday Morning (Final Packing List)
```bash
# Get actual Monday packing list for final confirmation
python egg_packing_predictor.py actuals --day Mon
```

## File Requirements

The system automatically finds Excel files matching the pattern:
- `Week *Loading Slip*.xlsx`
- Examples: `Week 5 Loading Slip 2025.xlsx`, `Week 10 Loading Slip 2025.xlsx`

## Troubleshooting

### No Data Found
- Ensure Excel files are in the same folder as the script
- Check that files follow the naming pattern `Week *Loading Slip*.xlsx`

### All Boxes Show 0
- The system may be using fallback row ranges
- Check that your Excel files have "Our Compliments" or "DAILY TOTALS" markers

### Get Help
```bash
python egg_packing_predictor.py --help
python egg_packing_predictor.py forecast-day --help
```

## Business Context

- **Monday orders**: Released Friday, packed Monday morning
- **Tuesday-Friday orders**: Released previous day, packed same day morning
- **Packing times**: Mon 6:45 AM, Tue-Fri 7:45 AM, finish ~11 AM
- **NFLD**: Packed after Mon-Fri orders (excluded from predictor)
