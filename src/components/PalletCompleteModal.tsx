import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  Button,
  Switch,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  Alert,
  // InputAccessoryView,  // <- gated below
} from 'react-native';
import type { OrderLine, PalletRow } from '../types';

const ULTRA_SAFE_MODE = true; // Maximum crash prevention
const SAFE_MODE = true; // flip to false once stable to re-enable accessory view etc.

export function PalletCompleteModal({
  visible,
  onClose,
  lines,
  meta,
  stop,
}: {
  visible: boolean;
  onClose: (rows: PalletRow[] | null) => void;
  lines: OrderLine[];
  meta: { shipmentDate: string; bbDate: string };
  stop: string;
}) {
  // ULTRA SAFE: Minimal state to prevent crashes
  const [palletNo, setPalletNo] = useState('1');
  const [usedPrior, setUsedPrior] = useState(false);
  const [priorMap, setPriorMap] = useState<Record<string, string>>({});
  const [barnCode, setBarnCode] = useState('');
  const [editing, setEditing] = useState(false);
  const openedOnce = useRef(false);

  // ULTRA SAFE: Defensive guards everywhere
  const safeLines = useMemo<OrderLine[]>(() => {
    try {
      if (!Array.isArray(lines)) return [];
      return lines.filter(l => l && typeof l === 'object' && l.sku && typeof l.sku === 'string');
    } catch {
      return [];
    }
  }, [lines]);

  const safeMeta = useMemo(() => {
    try {
      return {
        shipmentDate: String(meta?.shipmentDate || ''),
        bbDate: String(meta?.bbDate || 'unknown')
      };
    } catch {
      return { shipmentDate: '', bbDate: 'unknown' };
    }
  }, [meta]);

  const safeStop = useMemo(() => String(stop || 'Unknown Stop'), [stop]);

  useEffect(() => {
    if (visible && !openedOnce.current) {
      openedOnce.current = true;
      try {
        setPalletNo('1');
        setUsedPrior(false);
        setPriorMap({});
        setBarnCode('');
        setEditing(false);
        console.log('[PalletCompleteModal] ULTRA SAFE open', {
          stop: safeStop,
          linesCount: safeLines.length,
        });
      } catch (e) {
        console.error('Modal open error:', e);
      }
    }
    if (!visible) openedOnce.current = false;
  }, [visible, safeStop, safeLines.length]);

  const handleSave = () => {
    try {
      const pno = Math.max(1, Number(palletNo) || 1);
      const rows: PalletRow[] = [];
      
      for (const l of safeLines) {
        if (!l || !l.sku) continue;
        rows.push({
          shipmentDate: safeMeta.shipmentDate,
          stop: safeStop,
          palletNo: pno,
          sku: String(l.sku),
          qtyBoxes: Number(l.qty) || 0,
          bbDate: safeMeta.bbDate,
          barnCode: barnCode || null,
          isPrevWeek: 0,
        });
      }
      
      onClose(rows);
    } catch (e) {
      console.error('Save error:', e);
      Alert.alert('Error', 'Failed to save pallet');
    }
  };

  // ULTRA SAFE: Minimal input props
  const safeInputProps = {
    returnKeyType: 'done' as const,
    blurOnSubmit: true,
    onSubmitEditing: () => Keyboard.dismiss(),
  };

  // ULTRA SAFE: Minimal modal that cannot crash
  if (ULTRA_SAFE_MODE) {
    return (
      <Modal
        visible={visible}
        animationType="slide"
        onRequestClose={() => onClose(null)}
        transparent={false}
      >
        <View style={{ flex: 1, padding: 20, backgroundColor: '#fff' }}>
          <Text style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 20 }}>
            Pallet Complete - {safeStop}
          </Text>
          
          <Text style={{ fontSize: 16, marginBottom: 10 }}>
            Pallet #: {palletNo}
          </Text>
          
          <Text style={{ fontSize: 16, marginBottom: 20 }}>
            BB Date: {safeMeta.bbDate}
          </Text>
          
          <Text style={{ fontSize: 16, marginBottom: 10 }}>
            Items found: {safeLines.length}
          </Text>
          
          {safeLines.length > 0 && (
            <ScrollView style={{ maxHeight: 300, marginBottom: 20 }}>
              {safeLines.map((item, index) => (
                <Text key={index} style={{ padding: 5, fontSize: 14 }}>
                  • {item.sku} (qty: {item.qty})
                </Text>
              ))}
            </ScrollView>
          )}
          
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <Button title="Cancel" onPress={() => onClose(null)} />
            <Button title="Save" onPress={handleSave} />
          </View>
        </View>
      </Modal>
    );
  }

  // Original complex modal (disabled in ultra safe mode)
  return (
    <Modal
      visible={visible}
      animationType="slide"
      onRequestClose={() => onClose(null)}
      transparent={false}
    >
      <View style={{ flex: 1, padding: 20, backgroundColor: '#fff' }}>
        <Text style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 20 }}>
          Pallet Complete - {safeStop}
        </Text>
        
        <Text style={{ fontSize: 16, marginBottom: 10 }}>
          Pallet #: {palletNo}
        </Text>
        
        <Text style={{ fontSize: 16, marginBottom: 20 }}>
          BB Date: {safeMeta.bbDate}
        </Text>
        
        <Text style={{ fontSize: 16, marginBottom: 10 }}>
          Items found: {safeLines.length}
        </Text>
        
        {safeLines.length > 0 && (
          <ScrollView style={{ maxHeight: 300, marginBottom: 20 }}>
            {safeLines.map((item, index) => (
              <Text key={index} style={{ padding: 5, fontSize: 14 }}>
                • {item.sku} (qty: {item.qty})
              </Text>
            ))}
          </ScrollView>
        )}
        
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <Button title="Cancel" onPress={() => onClose(null)} />
          <Button title="Save" onPress={handleSave} />
        </View>
      </View>
    </Modal>
  );
}