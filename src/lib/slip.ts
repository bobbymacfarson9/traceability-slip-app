import * as FileSystem from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
import * as XLSX from 'xlsx';
import { MD5 } from 'crypto-js';
import type { StopMapping, OrderLine, SlipMeta } from '../types';

export async function pickSlip(): Promise<{bytes:ArrayBuffer, uri:string, name:string}> {
  const res = await DocumentPicker.getDocumentAsync({ 
    type: [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'application/excel',
      'application/x-excel',
      'application/x-msexcel'
    ],
    copyToCacheDirectory: true
  });
  if (res.canceled || !res.assets?.[0]) throw new Error('No file chosen');
  const asset = res.assets[0];
  const file = await FileSystem.readAsStringAsync(asset.uri, { encoding: FileSystem.EncodingType.Base64 });
  const bytes = base64ToArrayBuffer(file);
  return { bytes, uri: asset.uri, name: asset.name ?? 'loading-slip.xlsx' };
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary_string = globalThis.atob ? atob(base64) : Buffer.from(base64,'base64').toString('binary');
  const len = binary_string.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binary_string.charCodeAt(i);
  return bytes.buffer;
}

export function readSheet(bytes:ArrayBuffer, sheetName?:string) {
  const wb = XLSX.read(bytes, { type:'array', cellDates:false, cellText:false });
  const wsName = sheetName ?? wb.SheetNames[0];
  const ws = wb.Sheets[wsName];
  const aoa: any[][] = XLSX.utils.sheet_to_json(ws, { header:1, raw:true });
  return { aoa, wsName, wb };
}

// Convert Excel serial number to readable date
function excelSerialToDate(serial: number): string {
  // Excel serial date starts from 1900-01-01, but Excel incorrectly treats 1900 as a leap year
  const excelEpoch = new Date(1900, 0, 1);
  const date = new Date(excelEpoch.getTime() + (serial - 2) * 24 * 60 * 60 * 1000);
  return date.toISOString().split('T')[0]; // YYYY-MM-DD
}

export function getHeaderMeta(aoa:any[][]): {shipDate?:string|null; bbDate?:string|null; headerRowIdx:number} {
  for (let i=0;i<Math.min(10, aoa.length);i++){
    const row = aoa[i] || [];
    let shipDate: string | null = null;
    let bbDate: string | null = null;
    for (let j=0; j<row.length; j++){
      const cell = row[j];
      const cellStr = String(cell || '').toLowerCase();
      if (cellStr.includes('ship date') && j+1 < row.length) {
        const nextCell = row[j+1];
        if (typeof nextCell === 'number' && nextCell > 40000) shipDate = excelSerialToDate(nextCell);
      }
      if (cellStr.includes('bbd') && j+1 < row.length) {
        const nextCell = row[j+1];
        if (typeof nextCell === 'number' && nextCell > 40000) bbDate = excelSerialToDate(nextCell);
      }
    }
    if (shipDate || bbDate) return { shipDate, bbDate, headerRowIdx: i };
  }
  return { shipDate:null, bbDate:null, headerRowIdx:0 };
}

// Treat these as stop headers, e.g. "7.Superstore", "14. Colbourne", "5-Foodland", "3: Walmart"
const STOP_HEADER_RE = /^\s*\d+\s*(?:[.\-:])\s*/; // number + . or - or : , optional spaces

function isStopHeaderCell(cell: any): boolean {
  return typeof cell === 'string' && STOP_HEADER_RE.test(cell);
}

function isHeaderRow(row: any[]): boolean {
  return row.some(isStopHeaderCell);
}

/** Stop headers may appear multiple times on one worksheet ("second sheet" effect).
 *  Return the first row index we saw headers in, plus EVERY stop with its col AND row.
 */
export function findStopHeaderRow(
  aoa:any[][],
  fromRow:number
): {rowIdx:number; titles:{title:string; col:number; row:number}[]} {
  const titles: {title:string; col:number; row:number}[] = [];
  let first = -1;
  const STOP_HEADER_RE = /^\s*\d+\s*(?:[.\-:])\s*/;

  for (let i = fromRow; i < aoa.length; i++) {
    const row = aoa[i] || [];
    let found = false;
    // scan first ~24 cells only
    const lim = Math.min(row.length, 24);
    for (let col=0; col<lim; col++) {
      const cell = row[col];
      if (typeof cell === 'string' && STOP_HEADER_RE.test(cell)) {
        titles.push({ title: String(cell).trim(), col, row: i });
        found = true;
      }
    }
    if (found && first === -1) first = i;
  }

  return { rowIdx: first === -1 ? fromRow : first, titles };
}

/** List order lines for a given stop.
 *  - Start from THIS stop's header row.
 *  - Stop at "Daily Totals" OR the next header row (beginning of the next block).
 */
export function listLinesForStop(
  aoa:any[][],
  stop:StopMapping,
  fromRow:number,  // pass the stop's own header row
  maxRows=160 // clamp to a sane window
): OrderLine[] {
  const out: OrderLine[] = [];

  // Validate inputs early
  const totalRows = Array.isArray(aoa) ? aoa.length : 0;
  if (totalRows === 0) return out;

  const baseCol = Math.max(0, Number(stop?.startCol ?? 0));
  const qtyCol  = Math.max(0, baseCol + Math.max(0, Number(stop?.qtyColOffset ?? 0)));
  const skuCol  = Math.max(0, baseCol + Math.max(0, Number(stop?.skuColOffset ?? 0)));

  // Helper: is this row a header row (start of next stop)?
  const STOP_HEADER_RE = /^\s*\d+\s*(?:[.\-:])\s*/;
  const isHeaderRow = (row:any[]): boolean => {
    if (!Array.isArray(row)) return false;
    // Look only at first ~16 cells to avoid huge scans
    const lim = Math.min(row.length, 16);
    for (let i=0; i<lim; i++) {
      const c = row[i];
      if (typeof c === 'string' && STOP_HEADER_RE.test(c)) return true;
    }
    return false;
  };

  // Helper: make a tiny lowercased string sample without joining a giant row
  const tinyRowStr = (row:any[]): string => {
    if (!Array.isArray(row) || row.length === 0) return '';
    const lim = Math.min(row.length, 12);
    let s = '';
    for (let i=0; i<lim; i++) {
      const v = row[i];
      if (v == null) continue;
      // Append at most ~32 chars per cell
      const piece = String(v);
      s += (piece.length > 32 ? piece.slice(0,32) : piece) + ' ';
      if (s.length > 400) break; // clamp overall
    }
    return s.toLowerCase();
  };

  const hardEnd = Math.min(totalRows, fromRow + 1 + Math.max(1, maxRows));
  for (let r = Math.max(0, fromRow + 1); r < hardEnd; r++) {
    let row:any[] = [];
    try {
      row = Array.isArray(aoa[r]) ? aoa[r] : [];
      if (isHeaderRow(row)) break;

      const sample = tinyRowStr(row);
      const terminator =
        sample.includes('daily totals') ||
        (sample.includes('ship date') && sample.includes('bbd')) ||
        sample.includes('total of small stops');
      if (terminator) break;

      // Skip if row doesn't even have these columns
      if (row.length <= Math.max(qtyCol, skuCol)) continue;

      const rawQty = row[qtyCol];
      const rawSku = row[skuCol];

      const qty = toInt(rawQty);
      const sku = (typeof rawSku === 'string') ? cleanSku(rawSku) : '';

      if (qty > 0 && sku && !looksLikeStopWord(sku)) {
        out.push({ rowIdx: r, qty, sku });
      }
    } catch {
      // If something weird in this row, skip it—do not crash/log huge data
      continue;
    }
  }

  return out;
}

export function cleanSku(s:string){ return s.replace(/\s+/g,' ').trim(); }
export function toInt(v:any){
  if (typeof v==='number') return Math.round(v);
  if (typeof v==='string' && /^-?\d+(\.\d+)?$/.test(v.trim())) return Math.round(parseFloat(v));
  return 0;
}
export function looksLikeStopWord(s:string){
  const t=s.toLowerCase();
  return t.includes('box total') || t.includes('daily totals');
}

export function sha256Like(name:string): string {
  return MD5(name).toString();
}