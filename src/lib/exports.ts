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

export async function exportDay(shipmentDate:string, pallets:PalletRow[]): Promise<string> {
  try {
    // Validate inputs
    if (!shipmentDate || !/^\d{4}-\d{2}-\d{2}$/.test(shipmentDate)) {
      throw new Error('Invalid shipment date format. Expected YYYY-MM-DD');
    }
    
    if (!Array.isArray(pallets) || pallets.length === 0) {
      throw new Error('No pallet data to export');
    }

    const dir = FileSystem.documentDirectory + `Loading Slips Finished/${shipmentDate}/`;
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });

    const palletsCsv = ['shipment_date,stop,pallet_no,sku,qty_boxes,bb_date,barn_code,is_prev_week,created_at']
      .concat(pallets.map(p => toCsvRow([
        p.shipmentDate,
        p.stop,
        p.palletNo,
        p.sku,
        p.qtyBoxes,
        p.bbDate,
        p.barnCode,
        p.isPrevWeek,
        p.createdAt || new Date().toISOString()
      ])))
      .join('\n');

    const filePath = dir + 'pallets.csv';
    await FileSystem.writeAsStringAsync(filePath, palletsCsv, { encoding: FileSystem.EncodingType.UTF8 });
    
    console.log(`Exported ${pallets.length} pallets to ${filePath}`);
    return filePath;
  } catch (error) {
    console.error('Export error:', error);
    throw new Error(`Failed to export data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Export summary by stop for quick overview
export async function exportSummaryByStop(shipmentDate: string, pallets: PalletRow[]): Promise<string> {
  try {
    if (!shipmentDate || !/^\d{4}-\d{2}-\d{2}$/.test(shipmentDate)) {
      throw new Error('Invalid shipment date format. Expected YYYY-MM-DD');
    }
    
    if (!Array.isArray(pallets) || pallets.length === 0) {
      throw new Error('No pallet data to export');
    }

    const dir = FileSystem.documentDirectory + `Loading Slips Finished/${shipmentDate}/`;
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });

    // Group by stop and summarize
    const stopSummary = pallets.reduce((acc, pallet) => {
      const key = pallet.stop;
      if (!acc[key]) {
        acc[key] = {
          stop: pallet.stop,
          totalBoxes: 0,
          uniqueSkus: new Set(),
          palletCount: new Set(),
          priorWeekItems: 0
        };
      }
      
      acc[key].totalBoxes += pallet.qtyBoxes;
      acc[key].uniqueSkus.add(pallet.sku);
      acc[key].palletCount.add(pallet.palletNo);
      if (pallet.isPrevWeek) {
        acc[key].priorWeekItems += pallet.qtyBoxes;
      }
      
      return acc;
    }, {} as Record<string, any>);

    const summaryCsv = ['stop,total_boxes,unique_skus,pallet_count,prior_week_boxes']
      .concat(Object.values(stopSummary).map((summary: any) => toCsvRow([
        summary.stop,
        summary.totalBoxes,
        summary.uniqueSkus.size,
        summary.palletCount.size,
        summary.priorWeekItems
      ])))
      .join('\n');

    const filePath = dir + 'summary_by_stop.csv';
    await FileSystem.writeAsStringAsync(filePath, summaryCsv, { encoding: FileSystem.EncodingType.UTF8 });
    
    console.log(`Exported stop summary to ${filePath}`);
    return filePath;
  } catch (error) {
    console.error('Summary export error:', error);
    throw new Error(`Failed to export summary: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
