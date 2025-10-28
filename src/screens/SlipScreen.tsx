import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  Button,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { StopList } from '../components/StopList';
import { PalletCompleteModal } from '../components/PalletCompleteModal';
import { OneDriveAuth } from '../components/OneDriveAuth';
import { OneDriveFileBrowser } from '../components/OneDriveFileBrowser';
import { SheetPicker } from '../components/SheetPicker';
import { initDb, insertPalletRows, getPalletsByDate } from '../lib/db';
import { exportDay, exportSummaryByStop } from '../lib/exports';
import {
  pickSlip,
  readSheet,
  getHeaderMeta,
  findStopHeaderRow,
  listLinesForStop,
  sha256Like
} from '../lib/slip';
import { getOneDriveFiles, downloadOneDriveFile, getAuthData, OneDriveFile } from '../lib/onedrive';
import * as XLSX from 'xlsx';
import type { StopMapping, OrderLine, PalletRow } from '../types';

const BYPASS_SCAN_ON_TAP = false; // <-- flip to true to verify taps themselves don't crash

// Debug flag for this screen
const SHOW_DEBUG = false;

// Debug logger (keeps logs small and safe for iOS)
const dlog = (...args: any[]) => {
  if (__DEV__ && SHOW_DEBUG) {
    try {
      console.log(...args.map(x => 
        typeof x === 'string' ? x : JSON.stringify(x).slice(0,200) // keep logs small
      ));
    } catch {
      console.log(...args);
    }
  }
};

type BestConfig = { startCol:number; width:number; qtyColOffset:number; skuColOffset:number };
type StopKey = string; // title is our key

export default function SlipScreen(){
  const [aoa,setAoa] = useState<any[][]>([]);
  const [fileName,setFileName] = useState('');
  const [sheetName,setSheetName] = useState('');
  const [shipDate,setShipDate] = useState<string>('');
  const [bbDate,setBbDate] = useState<string>('');
  const [headerRow,setHeaderRow] = useState<number>(0);
  const [stopHeaderRow,setStopHeaderRow] = useState<number>(0);
  const [stopTitles,setStopTitles] = useState<{title:string; col:number; row:number}[]>([]);
  const [selectedStop,setSelectedStop] = useState<StopMapping|null>(null);
  const [lines,setLines] = useState<OrderLine[]>([]);
  const [palletVisible,setPalletVisible] = useState(false);
  const [todayPallets,setTodayPallets] = useState<PalletRow[]>([]);
  const [showOneDriveAuth,setShowOneDriveAuth] = useState(false);
  const [showOneDriveBrowser,setShowOneDriveBrowser] = useState(false);
  const [oneDriveFiles,setOneDriveFiles] = useState<OneDriveFile[]>([]);
  const [isOneDriveConnected,setIsOneDriveConnected] = useState(false);
  const [completedStops,setCompletedStops] = useState<string[]>([]);
  const [showStopList,setShowStopList] = useState(true); // Start with stop list as primary view
  const [showSheetPicker,setShowSheetPicker] = useState(false);
  const [availableSheets,setAvailableSheets] = useState<string[]>([]);
  const [workbook,setWorkbook] = useState<any>(null);

  // indexing state
  const [isLoading,setIsLoading] = useState(false);
  const [isIndexing,setIsIndexing] = useState(false);
  const [indexProgress,setIndexProgress] = useState(0);

  // precomputed results
  const [bestConfigByStop, setBestConfigByStop] = useState<Record<StopKey, BestConfig>>({});
  const [linesByStop, setLinesByStop] = useState<Record<StopKey, OrderLine[]>>({});

  // debug state
  const [showDebug, setShowDebug] = useState(false);

  const lastSelectedRef = useRef<{title:string; col:number; row:number} | null>(null);

  // Sort stops numerically by leading number
  const sortStops = (arr: {title:string; col:number; row:number}[]) =>
    arr.slice().sort((a, b) => {
      const na = parseInt(a.title, 10);
      const nb = parseInt(b.title, 10);
      const aHas = !isNaN(na);
      const bHas = !isNaN(nb);
      if (aHas && bHas) return na - nb;
      if (aHas) return -1;
      if (bHas) return 1;
      return a.title.localeCompare(b.title, undefined, { numeric: true, sensitivity: 'base' });
    });

  useEffect(()=>{ 
    initDb(); 
    const auth = getAuthData();
    if (auth) {
      setIsOneDriveConnected(true);
      loadOneDriveFiles();
    }
  },[]);

  const handlePick = async () => {
    try {
      setIsLoading(true);
      const { bytes, name } = await pickSlip();
      const { aoa:rows, wsName, wb } = readSheet(bytes);

      if (wb.SheetNames.length > 1) {
        setAvailableSheets(wb.SheetNames);
        setWorkbook(wb);
        setFileName(name);
        setShowSheetPicker(true);
        return;
      }
      await loadSheetData(rows, wsName, name);
    } catch (e:any) {
      Alert.alert('Error picking file', String(e?.message ?? e));
    } finally {
      setIsLoading(false);
    }
  };

  const loadSheetData = async (rows: any[][], wsName: string, fileName: string) => {
    setIsLoading(true);
    try {
      const meta = getHeaderMeta(rows);
      sha256Like(fileName); // noop uniqueness
      setAoa(rows); setFileName(fileName); setSheetName(wsName);
      setHeaderRow(meta.headerRowIdx);
      setShipDate(meta.shipDate ?? '');
      setBbDate(meta.bbDate ?? '');
      const sh = findStopHeaderRow(rows, meta.headerRowIdx+1);
      setStopHeaderRow(sh.rowIdx);
      setStopTitles(sortStops(sh.titles)); // {title,col,row}

      // clear any previous index
      setBestConfigByStop({});
      setLinesByStop({});
      setIndexProgress(0);

      if (meta.shipDate) {
        const pals = await getPalletsByDate(meta.shipDate);
        setTodayPallets(pals as any);
      }
    } catch (e:any) {
      console.error('loadSheetData error', e);
      Alert.alert('Error', String(e?.message ?? e));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSheetSelect = async (sheetName: string) => {
    if (!workbook) return;
    const ws = workbook.Sheets[sheetName];
    if (!ws) return;
    const rows: any[][] = XLSX.utils.sheet_to_json(ws, { header:1, raw:true });
    setShowSheetPicker(false);
    await loadSheetData(rows, sheetName, fileName);
  };

  const loadOneDriveFiles = async () => {
    try {
      const files = await getOneDriveFiles();
      setOneDriveFiles(files);
    } catch (error) {
      Alert.alert('Error', 'Failed to load OneDrive files.');
    }
  };

  const handleOneDriveAuthSuccess = () => {
    setIsOneDriveConnected(true);
    setShowOneDriveAuth(false);
    setShowOneDriveBrowser(true);
  };

  const handleOneDriveFileSelect = async (file: OneDriveFile) => {
    setIsLoading(true);
    try {
      const bytes = await downloadOneDriveFile(file);
      const { aoa:rows, wsName, wb } = readSheet(bytes);

      // Handle multiple sheets
      if (wb.SheetNames.length > 1) {
        setAvailableSheets(wb.SheetNames);
        setWorkbook(wb);
        setFileName(file.name);
        setShowOneDriveBrowser(false);
        setShowSheetPicker(true);
        return;
      }

      await loadSheetData(rows, wsName, file.name);
      setShowOneDriveBrowser(false);
    } catch (error:any) {
      console.error('Error loading OneDrive file:', error);
      Alert.alert(
        'OneDrive Error', 
        `${error.message}\n\nTip: You can use "Pick local file" to test with files from your device.`,
        [
          { text: 'Use Local Files', onPress: () => setShowOneDriveBrowser(false) },
          { text: 'Try Again', onPress: () => {} }
        ]
      );
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Pre-index all stops OFF the tap path.
   * Processes one stop per tick with an await yield to avoid long blocking work.
   */
  useEffect(() => {
    if (aoa.length === 0 || stopTitles.length === 0) return;

    let cancelled = false;
    const doIndex = async () => {
      setIsIndexing(true);
      const cfgByStop: Record<StopKey, BestConfig> = {};
      const linesBy: Record<StopKey, OrderLine[]> = {};

      const configs = (startCol:number): BestConfig[] => ([
        { startCol, width: 3, qtyColOffset: 0, skuColOffset: 1 },
        { startCol, width: 2, qtyColOffset: 0, skuColOffset: 1 },
        { startCol, width: 4, qtyColOffset: 0, skuColOffset: 1 },
        { startCol, width: 3, qtyColOffset: 1, skuColOffset: 0 },
        { startCol, width: 3, qtyColOffset: 2, skuColOffset: 1 },
      ]);

      for (let i = 0; i < stopTitles.length; i++) {
        if (cancelled) break;
        const s = stopTitles[i];
        const startRow = Number.isInteger(s.row) && s.row >= 0 && s.row < aoa.length ? s.row : Math.max(0, stopHeaderRow);
        const startCol = Number.isInteger(s.col) && s.col >= 0 ? s.col : 0;

        let bestCfg = configs(startCol)[0];
        let bestLines: OrderLine[] = [];
        try {
          for (const cfg of configs(startCol)) {
            const mapping = { stopTitle: s.title, ...cfg };
            const ls = listLinesForStop(aoa, mapping, startRow);
            if (ls.length > bestLines.length) {
              bestLines = ls;
              bestCfg = cfg;
            }
          }
        } catch (e:any) {
          // Skip this stop if anything odd occurs
          console.log('[index] skip stop due to error:', s.title, String(e?.message || e));
        }

        cfgByStop[s.title] = bestCfg;
        linesBy[s.title] = bestLines;

        // update progress every stop
        setIndexProgress(Math.round(((i + 1) / stopTitles.length) * 100));

        // yield to event loop every stop
        // eslint-disable-next-line no-await-in-loop
        await new Promise(res => setTimeout(res, 0));
      }

      if (!cancelled) {
        setBestConfigByStop(cfgByStop);
        setLinesByStop(linesBy);
        setIsIndexing(false);
      }
    };

    doIndex();
    return () => { cancelled = true; };
  }, [aoa, stopTitles, stopHeaderRow]);

  const openPallet = () => {
    setPalletVisible(true);
  };
  
  const closePallet = async (rows:PalletRow[]|null) => {
    setPalletVisible(false);
    if (!rows || rows.length === 0) return;
    
    try {
      await insertPalletRows(rows);
      if (selectedStop) {
        setCompletedStops(prev => [...prev, selectedStop.stopTitle]);
      }
      
      if (shipDate) {
        const pals = await getPalletsByDate(shipDate);
        setTodayPallets(pals as any);
      }
      
      Alert.alert('Success', `Pallet completed for ${selectedStop?.stopTitle || 'stop'}`);
    } catch (error: any) {
      console.error('Error saving pallet:', error);
      Alert.alert('Error', `Failed to save pallet: ${error.message || 'Unknown error'}`);
    }
  };

  // TAP handler: pure lookup (no scanning)
  const handleStopListSelect = useCallback((stop: { title: string; col: number; row: number }) => {
    try {
      lastSelectedRef.current = stop;

      if (BYPASS_SCAN_ON_TAP) {
        // Prove tap flow is harmless: do NOT read anything, just open modal with empty lines
        setSelectedStop({ stopTitle: stop.title, startCol: 0, width: 3, qtyColOffset: 0, skuColOffset: 1 });
        setLines([]);
        setPalletVisible(true);
        return;
      }

      const cfg = bestConfigByStop[stop.title] ?? { startCol: stop.col ?? 0, width: 3, qtyColOffset: 0, skuColOffset: 1 };
      const ls = linesByStop[stop.title] ?? [];

      setSelectedStop({ stopTitle: stop.title, ...cfg });
      setLines(ls);
      setPalletVisible(true);
    } catch (e:any) {
      console.log('[tap stop] error', String(e?.message || e));
    }
  }, [bestConfigByStop, linesByStop]);

  const handleStopComplete = (stopTitle: string) => {
    setCompletedStops(prev => [...prev, stopTitle]);
  };

  const handleExportData = async () => {
    if (!shipDate || todayPallets.length === 0) {
      Alert.alert('No Data', 'No pallet data available for export.');
      return;
    }

    try {
      const palletPath = await exportDay(shipDate, todayPallets);
      const summaryPath = await exportSummaryByStop(shipDate, todayPallets);
      
      Alert.alert(
        'Export Complete',
        `Data exported successfully!\n\nPallets: ${palletPath}\nSummary: ${summaryPath}`,
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      Alert.alert('Export Error', error.message || 'Failed to export data');
    }
  };

  if (showOneDriveAuth) {
    return <OneDriveAuth onAuthSuccess={handleOneDriveAuthSuccess} onCancel={() => setShowOneDriveAuth(false)} />;
  }

  if (showOneDriveBrowser) {
    return <OneDriveFileBrowser onFileSelect={handleOneDriveFileSelect} onClose={() => setShowOneDriveBrowser(false)} />;
  }

  if (showSheetPicker) {
    return (
      <SheetPicker 
        sheetNames={availableSheets}
        onSheetSelect={handleSheetSelect}
        onCancel={() => setShowSheetPicker(false)}
      />
    );
  }

  return (
    <View style={{ flex:1, padding:16, gap:10 }}>
      <View style={{ flexDirection:'row', gap:16, alignItems:'center', flexWrap:'wrap' }}>
        <Button title="Pick local file" onPress={handlePick} />
        {isOneDriveConnected ? (
          <Button title="Browse OneDrive" onPress={() => setShowOneDriveBrowser(true)} />
        ) : (
          <Button title="Connect OneDrive" onPress={() => setShowOneDriveAuth(true)} />
        )}
        {!!stopTitles.length && (
          <TouchableOpacity onPress={() => setShowDebug(s => !s)} style={{ marginLeft: 'auto' }}>
            <Text style={{ color:'#2563eb' }}>{showDebug ? 'Hide Debug' : 'Show Debug'}</Text>
          </TouchableOpacity>
        )}
      </View>

      {(isLoading || isIndexing) && (
        <View style={{ padding:12, borderWidth:1, borderColor:'#ddd', borderRadius:8, flexDirection:'row', gap:10, alignItems:'center' }}>
          <ActivityIndicator />
          <Text>{isLoading ? 'Loading slip…' : `Indexing stops… ${indexProgress}%`}</Text>
        </View>
      )}

      <Text>· Sheet: {sheetName || '(none)'}</Text>
      <Text>Ship Date: {shipDate || '(unknown)'} · BB (ThisWeekBB): {bbDate || '(unknown)'}</Text>

      {/* Debug info */}
      {showDebug && (
        <View style={{ borderWidth:1, borderColor:'#ddd', borderRadius:8, padding:10, backgroundColor:'#fafafa', gap:6 }}>
          <Text style={{ fontWeight:'700' }}>Debug</Text>
          <Text>aoa rows: {aoa.length}</Text>
          <Text>stops: {stopTitles.length}</Text>
          <Text>headerRow: {headerRow} · firstStopRow: {stopHeaderRow}</Text>
          <Text>indexed: {Object.keys(bestConfigByStop).length} stops</Text>
          {lastSelectedRef.current && <Text>last tap: {lastSelectedRef.current.title} (row {lastSelectedRef.current.row}, col {lastSelectedRef.current.col})</Text>}
        </View>
      )}

      {/* Main Content */}
      <View style={{ flex: 1 }}>
        {/* StopList is the primary UI; only active when data is loaded */}
        {aoa.length > 0 && stopTitles.length > 0 && (
          <StopList
            stops={stopTitles}
            onStopSelect={handleStopListSelect}
            onStopComplete={handleStopComplete}
            completedStops={completedStops}
            disabled={isLoading || isIndexing}
          />
        )}

        {/* Show message if no file loaded */}
        {!fileName && (
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 }}>
            <Text style={{ fontSize: 18, color: '#6b7280', textAlign: 'center', marginBottom: 20 }}>
              Load a loading slip to get started
            </Text>
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <Button title="Pick local file" onPress={handlePick} />
              <Button title="Connect OneDrive" onPress={() => setShowOneDriveAuth(true)} />
            </View>
          </View>
        )}
      </View>

      {/* Modal stays mounted regardless of StopList visibility */}
      <PalletCompleteModal
        visible={palletVisible}
        onClose={closePallet}
        lines={lines}
        stop={selectedStop?.stopTitle || ''}
        meta={{ shipmentDate: shipDate || '', bbDate: bbDate || '' }}
      />

      {/* Status Bar */}
      {todayPallets.length > 0 && (
        <View style={{ padding: 12, backgroundColor: '#f0fdf4', borderTopWidth: 1, borderTopColor: '#bbf7d0' }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: 14, color: '#166534' }}>
              ✓ {todayPallets.length} pallets saved today
            </Text>
            <TouchableOpacity 
              onPress={handleExportData}
              style={{ 
                backgroundColor: '#166534', 
                paddingHorizontal: 12, 
                paddingVertical: 6, 
                borderRadius: 6 
              }}
            >
              <Text style={{ color: 'white', fontSize: 12, fontWeight: '600' }}>
                Export CSV
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}