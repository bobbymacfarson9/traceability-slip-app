import * as SQLite from 'expo-sqlite';

// Initialize database
let db: SQLite.SQLiteDatabase | null = null;

const initDatabase = () => {
  if (!db) {
    db = SQLite.openDatabaseSync('traceability.db');
  }
  return db;
};

export function initDb() {
  const database = initDatabase();
  
  database.execSync(`
    CREATE TABLE IF NOT EXISTS pallets(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      shipment_date TEXT,
      stop TEXT,
      pallet_no INTEGER,
      sku TEXT,
      qty_boxes INTEGER,
      bb_date TEXT,
      barn_code TEXT,
      is_prev_week INTEGER,
      created_at TEXT DEFAULT (datetime('now'))
    );
  `);
  
  database.execSync(`
    CREATE TABLE IF NOT EXISTS slip_meta(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_name TEXT,
      sha256 TEXT,
      sheet_name TEXT,
      ship_date TEXT,
      bb_date TEXT,
      imported_at TEXT DEFAULT (datetime('now'))
    );
  `);
}

export function insertPalletRows(rows: Omit<import('../types').PalletRow,'id'|'createdAt'>[]): Promise<void> {
  const database = initDatabase();
  
  for (const r of rows) {
    database.runSync(
      `INSERT INTO pallets (shipment_date, stop, pallet_no, sku, qty_boxes, bb_date, barn_code, is_prev_week)
       VALUES (?,?,?,?,?,?,?,?)`,
      [r.shipmentDate, r.stop, r.palletNo, r.sku, r.qtyBoxes, r.bbDate, r.barnCode ?? null, r.isPrevWeek]
    );
  }
}

export function getPalletsByDate(yyyyMmDd: string): Promise<any[]> {
  const database = initDatabase();
  
  const result = database.getAllSync(
    `SELECT * FROM pallets WHERE shipment_date = ? ORDER BY stop, pallet_no, sku`,
    [yyyyMmDd]
  );
  
  return Promise.resolve(result);
}
