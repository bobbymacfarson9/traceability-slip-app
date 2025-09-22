# Expo Traceability Slip Replicator

This is a **drop-in Expo starter kit** for tracking loading slips with the exact workflow you described:

- Shipper **doesn't tap per-SKU while picking**
- They only tap **"Pallet complete"** for a stop
- If they toggle **"Used prior-week BB?"**, they then **select SKUs and enter counts** just for those items
- Everything autosaves to SQLite; you can refresh the slip at noon without losing progress
- End-of-day you can export `pallets.csv` for traceability

## Quick Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the app:**
   ```bash
   npx expo start
   ```

3. **Open on your iPad** and follow the workflow below.

## How to Use

### 1. Load Today's Slip
- Tap **"Pick today's slip"** and choose your XLSX loading slip file
- The app will automatically detect Ship Date and BB Date from the header
- The grid view shows your slip data

### 2. Select a Stop
- **Tap any stop name** in the header row (e.g., "4. Sobeys - North Sydney")
- The app will highlight that stop's column block
- Configure the mapping once per stop (width, qty offset, SKU offset)

### 3. Complete Pallets
- Review the items listed for the selected stop
- Tap **"Pallet complete"** when done with that stop
- **Toggle "Used prior-week BB?"** if you used any cartons stamped before the BB date
- If yes, enter quantities and barn codes for those specific SKUs
- Save the pallet

### 4. Export Data
- All data is automatically saved to SQLite
- Use the export functionality to generate CSV files for traceability
- Files are saved to `Loading Slips Finished/[date]/pallets.csv`

## Key Features

- **Lightweight parsing**: No heavy Excel processing, just grid display
- **Stop isolation**: Tap store names to focus on one stop at a time
- **One-time mapping**: Set column offsets once per stop format
- **Prior-week BB tracking**: Toggle and enter counts only when needed
- **Offline-safe**: All data stored locally in SQLite
- **Progress preservation**: Refresh slip without losing work

## File Structure

```
├── App.tsx                          # Main app with QueryClient
├── app/
│   ├── _layout.tsx                  # Expo router layout
│   └── index.tsx                    # Routes to SlipScreen
├── src/
│   ├── types.ts                     # TypeScript definitions
│   ├── lib/
│   │   ├── db.ts                    # SQLite database operations
│   │   ├── slip.ts                  # XLSX import and parsing
│   │   └── exports.ts               # CSV export functionality
│   ├── components/
│   │   ├── Grid.tsx                 # Grid display component
│   │   ├── StopPicker.tsx           # Stop mapping configuration
│   │   └── PalletCompleteModal.tsx  # Pallet completion modal
│   └── screens/
│       └── SlipScreen.tsx           # Main screen
└── package.json                     # Dependencies
```

## Dependencies

- `expo-document-picker` - File selection
- `expo-file-system` - File operations
- `expo-sqlite` - Local database
- `xlsx` - Excel file parsing
- `@tanstack/react-query` - State management
- `date-fns` - Date utilities
- `crypto-js` - Hashing utilities

## Database Schema

The app creates two main tables:

- **`pallets`**: Stores completed pallet data with traceability info
- **`slip_meta`**: Stores slip file metadata

## Customization

- **Default column offsets**: Modify the default values in `StopPicker.tsx`
- **Barn code picker**: Add per-SKU barn code selection in `PalletCompleteModal.tsx`
- **Export format**: Customize CSV output in `exports.ts`
- **Timezone**: Adjust date handling in `exports.ts` (currently set for America/Moncton)

## Troubleshooting

- **File not loading**: Ensure XLSX file is not corrupted and has proper headers
- **Stop detection**: Check that stop names follow the pattern "1. Store Name"
- **Mapping issues**: Adjust width and offset values in the StopPicker
- **Export problems**: Check file permissions and available storage space

## Integration with Python Tools

This Expo app works alongside your existing Python forecasting and parsing tools. The Python tools can:
- Generate loading slips that this app can import
- Process exported CSV data for analysis
- Provide forecasting data for planning

The app focuses purely on the shipper workflow while your Python tools handle the data analysis and forecasting aspects.
