import * as FileSystem from 'expo-file-system';
import { format } from 'date-fns';
import type { PalletRow } from '../types';

function toCsvRow(fields:(string|number|null|undefined)[]) {
  return fields.map(v => {
    if (v==null) return '';
    const s=String(v);
    return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s;
  }).join(',');
}

export async function exportDay(shipmentDate:string, pallets:PalletRow[]) {
  const dir = FileSystem.documentDirectory + `Loading Slips Finished/${shipmentDate}/`;
  await FileSystem.makeDirectoryAsync(dir, { intermediates: true });

  const palletsCsv = ['shipment_date,stop,pallet_no,sku,qty_boxes,bb_date,barn_code,is_prev_week']
    .concat(pallets.map(p => toCsvRow([p.shipmentDate,p.stop,p.palletNo,p.sku,p.qtyBoxes,p.bbDate,p.barnCode,p.isPrevWeek])))
    .join('\n');

  // Simple recall view grouped client-side later; write same file for now
  await FileSystem.writeAsStringAsync(dir + 'pallets.csv', palletsCsv, { encoding: FileSystem.EncodingType.UTF8 });
  return dir + 'pallets.csv';
}
