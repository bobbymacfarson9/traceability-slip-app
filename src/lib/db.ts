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
  return new Promise((resolve, reject) => {
    try {
      const database = initDatabase();
      
      // Use a transaction for better performance and data integrity
      database.withTransactionSync(() => {
        for (const r of rows) {
          // Validate required fields
          if (!r.shipmentDate || !r.stop || !r.sku) {
            throw new Error(`Missing required fields: shipmentDate, stop, or sku`);
          }
          
          database.runSync(
            `INSERT INTO pallets (shipment_date, stop, pallet_no, sku, qty_boxes, bb_date, barn_code, is_prev_week)
             VALUES (?,?,?,?,?,?,?,?)`,
            [
              String(r.shipmentDate), 
              String(r.stop), 
              Number(r.palletNo) || 1, 
              String(r.sku), 
              Number(r.qtyBoxes) || 0, 
              String(r.bbDate), 
              r.barnCode ?? null, 
              Number(r.isPrevWeek) || 0
            ]
          );
        }
      });
      
      console.log(`Successfully inserted ${rows.length} pallet rows`);
      resolve();
    } catch (error) {
      console.error('Error inserting pallet rows:', error);
      reject(error);
    }
  });
}

export function getPalletsByDate(yyyyMmDd: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    try {
      const database = initDatabase();
      
      // Validate date format
      if (!yyyyMmDd || !/^\d{4}-\d{2}-\d{2}$/.test(yyyyMmDd)) {
        throw new Error('Invalid date format. Expected YYYY-MM-DD');
      }
      
      const result = database.getAllSync(
        `SELECT * FROM pallets WHERE shipment_date = ? ORDER BY stop, pallet_no, sku`,
        [yyyyMmDd]
      );
      
      console.log(`Found ${result.length} pallets for date ${yyyyMmDd}`);
      resolve(result);
    } catch (error) {
      console.error('Error getting pallets by date:', error);
      reject(error);
    }
  });
}

// Additional utility functions for better database management
export function getAllPallets(): Promise<any[]> {
  return new Promise((resolve, reject) => {
    try {
      const database = initDatabase();
      const result = database.getAllSync(
        `SELECT * FROM pallets ORDER BY shipment_date DESC, stop, pallet_no, sku`
      );
      resolve(result);
    } catch (error) {
      console.error('Error getting all pallets:', error);
      reject(error);
    }
  });
}

export function deletePalletsByDate(yyyyMmDd: string): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      const database = initDatabase();
      
      if (!yyyyMmDd || !/^\d{4}-\d{2}-\d{2}$/.test(yyyyMmDd)) {
        throw new Error('Invalid date format. Expected YYYY-MM-DD');
      }
      
      const result = database.runSync(
        `DELETE FROM pallets WHERE shipment_date = ?`,
        [yyyyMmDd]
      );
      
      console.log(`Deleted ${result.changes} pallets for date ${yyyyMmDd}`);
      resolve();
    } catch (error) {
      console.error('Error deleting pallets by date:', error);
      reject(error);
    }
  });
}

export function getDistinctShipmentDates(): Promise<string[]> {
  return new Promise((resolve, reject) => {
    try {
      const database = initDatabase();
      const result = database.getAllSync(
        `SELECT DISTINCT shipment_date FROM pallets ORDER BY shipment_date DESC`
      );
      
      const dates = result.map((row: any) => row.shipment_date);
      resolve(dates);
    } catch (error) {
      console.error('Error getting distinct shipment dates:', error);
      reject(error);
    }
  });
}
