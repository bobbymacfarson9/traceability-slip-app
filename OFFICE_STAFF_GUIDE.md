# Office Staff Guide - Pallet Optimizer

## 🚀 Quick Start (For Office Staff)

### Option 1: Double-click to run
1. Put your Loading Slip Excel files in this folder
2. Double-click `RUN_OPTIMIZER.bat`
3. Follow the prompts on screen
4. Check your new Excel file with optimized pallets!

### Option 2: Command line
1. Open Command Prompt in this folder
2. Type: `python user_friendly_optimizer.py`
3. Follow the prompts

## ⚙️ How to Change Settings

If you need to change pallet capacity, truck capacity, or product rules, edit the `user_friendly_optimizer.py` file.

### Easy Settings to Change:

**Pallet Capacity:**
```python
BOXES_PER_PALLET = 48    # Change this number
```

**Truck Capacity:**
```python
PALLETS_PER_TRUCK = 12   # Change this number
```

**Product Sizing Rules:**
```python
PRODUCT_SIZING = {
    'Nova 30 pack': 2,    # This product takes 2 units of space
    'OC Xlg': 1,          # This product takes 1 unit of space
    # Add more products here...
}
```

## 📋 What the Optimizer Does

1. **Reads your Loading Slip files** (Mon, Tues, Wed, Thurs, Fri sheets)
2. **Groups orders by stop number** (delivery sequence)
3. **Optimizes pallet loading** by:
   - Putting small orders together on one pallet
   - Splitting large orders across multiple pallets
   - Maximizing pallet utilization
4. **Creates an Excel file** with:
   - Detailed pallet plan
   - Summary with utilization statistics
   - Warnings if you need multiple trucks

## 📊 Understanding the Output

### Pallet Plan Sheet
- **Pallet #**: Which pallet this item goes on
- **Stop #**: Delivery stop number
- **Product Type**: What product this is
- **Boxes**: Number of boxes
- **Units Used**: How much space this takes
- **Pallet Capacity**: Total space on this pallet
- **Utilization %**: How full this pallet is
- **Unused Space**: Empty space on this pallet

### Summary Sheet
- **Total Pallets**: How many pallets you need
- **Overall Utilization**: How efficiently you're using space
- **Configuration**: Your current settings

## ⚠️ Common Issues

**"No Loading Slip files found"**
- Make sure your Excel files have "Loading Slip" in the filename
- Put the files in the same folder as the optimizer

**"No order items found"**
- Check that your Excel file has Mon, Tues, Wed, Thurs, Fri sheets
- Make sure the data format matches the expected structure

**"Too many pallets for truck capacity"**
- You'll need multiple trucks for this delivery
- Consider adjusting your pallet capacity settings

## 🔧 Advanced Settings

If you need to change more complex settings, look for these in the code:

```python
# Business Rules
COMBINE_SMALL_ORDERS = True     # Can small orders be combined?
LOAD_BY_STOP_NUMBER = True      # Load in stop number order?
MAX_BOXES_PER_PALLET = 48       # Max boxes when splitting orders
```

## 📞 Getting Help

1. Check the console output for error messages
2. Look at the warnings in the Excel Summary sheet
3. Verify your file format matches the expected structure
4. Make sure all required Python packages are installed

## 📁 File Structure

```
Pallet Optimizer/
├── user_friendly_optimizer.py    # Main optimizer (edit settings here)
├── RUN_OPTIMIZER.bat            # Double-click to run
├── requirements.txt              # Python packages needed
├── CONSTRAINTS_CONFIG.md         # Detailed constraints guide
└── Your Loading Slip files.xlsx  # Your Excel files go here
``` 