# Pallet Optimizer Constraints Configuration

## Current Constraints (Need Verification)

### 1. PALLET CAPACITY CONSTRAINTS
```
STANDARD_PALLET_CAPACITY = 48    # How many boxes fit on a standard pallet?
TRUCK_CAPACITY = 12              # How many pallets fit on one truck?
CART_CAPACITY = 24               # How many boxes fit on a cart (for special products)?
```

### 2. PRODUCT SIZING RULES
```
PRODUCT_SIZING = {
    'Nova 30 pack': 2,           # How many "units" does each box take?
    'SV/Loblaws 30 pack': 2,     # How many "units" does each box take?
    'OC 30 pack': 1,             # How many "units" does each box take?
    'ED XL 18 pack': 1,          # How many "units" does each box take?
    'dozens': 1,                 # How many "units" does each box take?
    'default': 1                 # Default for any product not listed above
}
```

### 3. REGIONAL CONSTRAINTS
```
NFLD_REGION = 'NFLD'             # What region identifier is used for NFLD orders?
NFLD_PALLET_SIZE = 48            # Must NFLD orders be exactly 48 units per pallet?
NFLD_SEPARATE_PALLETS = True     # Can NFLD orders be mixed with other orders?
```

### 4. LOADING ORDER CONSTRAINTS
```
LOAD_BY_STOP_NUMBER = True       # Should orders load in ascending stop number order?
COMBINE_SMALL_ORDERS = True      # Can small orders be combined on same pallet?
MAX_STOP_SPLIT = 48              # Maximum boxes per pallet when splitting a stop
```

### 5. TRUCK CONSTRAINTS
```
TRUCK_CAPACITY = 12              # Maximum pallets per truck
SEPARATE_TRUCKS_BY_REGION = False # Do different regions need separate trucks?
```

### 6. PRODUCT-SPECIFIC CONSTRAINTS
```
CART_PRODUCTS = ['ED XL 18 pack', 'dozens']  # Which products use cart capacity?
DOUBLE_STACK_PRODUCTS = ['Nova 30 pack', 'SV/Loblaws 30 pack']  # Which products count as 2 units?
```

## Questions for Your Team

### 1. Pallet Capacity
- **Q**: What is the actual capacity of your standard pallets? (Currently set to 48)
- **Q**: Do different product types have different pallet capacities?
- **Q**: Are there weight limits in addition to box count limits?

### 2. Truck Capacity
- **Q**: How many pallets can fit on your delivery trucks? (Currently set to 12)
- **Q**: Are there different truck types with different capacities?
- **Q**: Do you have weight limits per truck?

### 3. Product Sizing
- **Q**: Which products are "double-stack" (take 2 units of space)?
- **Q**: Which products use cart capacity (24 units)?
- **Q**: Are there any products that take more than 2 units of space?

### 4. Regional Rules
- **Q**: Do NFLD orders really need to be exactly 48 units per pallet?
- **Q**: Can NFLD orders be mixed with other orders on the same pallet?
- **Q**: Are there other regions besides NFLD with special rules?

### 5. Loading Order
- **Q**: How important is the stop number order for loading?
- **Q**: Can orders from different stops be combined on the same pallet?
- **Q**: What's the maximum number of boxes that can be split across pallets?

### 6. Business Rules
- **Q**: Are there any products that cannot be mixed with others?
- **Q**: Do you have time constraints (certain orders must be delivered first)?
- **Q**: Are there any customer-specific requirements?

## Current Product Types Found in Your Data
Based on your Loading Slip files, these product types were detected:
- OC Xlg, OC Lg, OC Med, OC Br, OC 30 Lrg
- Lob Xlg, Lob Lg, Lob br, Lob 30 Lg
- Wal GV Xlrg, Wal GV Lg, Wal Nova Xlg Brn, Wal Nova Brn
- ED Jumbo, ED 18 XL, ED 18 LG
- Nova Jumbo, Nova 6 Pack, XLrg 30 pack Nova, Lrg 30 pack Nova
- Eyk Xlg, Eyk Lg, Eyk Br
- All Grain Nova
- Box Total

## How to Update This File
1. Replace the values in the code blocks above with your actual constraints
2. Answer the questions above with your team
3. Add any additional constraints specific to your business
4. Save this file and the optimizer will use your updated constraints

## Example Updates
```
# If your pallets can hold 60 boxes instead of 48:
STANDARD_PALLET_CAPACITY = 60

# If Nova 30 pack takes 3 units instead of 2:
'Nova 30 pack': 3,

# If you can fit 15 pallets on a truck instead of 12:
TRUCK_CAPACITY = 15
``` 