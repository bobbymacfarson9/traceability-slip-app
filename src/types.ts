export type StopMapping = {
  stopTitle: string;      // e.g., "4. Sobeys - North Sydney"
  startCol: number;       // leftmost column of the block
  width: number;          // typically 3 or 4
  qtyColOffset: number;   // offset from startCol to qty cell
  skuColOffset: number;   // offset from startCol to sku cell
  row?: number;           // row where this stop header appears
};

export type OrderLine = {
  rowIdx: number;         // row index within the sheet grid
  qty: number;
  sku: string;
};

export type PalletRow = {
  id?: number;
  shipmentDate: string;   // 'YYYY-MM-DD'
  stop: string;
  palletNo: number;
  sku: string;
  qtyBoxes: number;
  bbDate: string;         // ThisWeekBB or prior-week BB
  barnCode?: string | null;
  isPrevWeek: 0 | 1;
  createdAt?: string;
};

export type SlipMeta = {
  fileName: string;
  sha256: string;
  sheetName: string;      // e.g., 'Mon'
  shipDate?: string | null;
  bbDate?: string | null; // ThisWeekBB
};
