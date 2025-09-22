import React, { useState } from 'react';
import { View, Text, TextInput, Button } from 'react-native';
import type { StopMapping } from '../types';

export function StopPicker({ stopTitle, startCol, onConfirm }:{ stopTitle:string; startCol:number; onConfirm:(m:StopMapping)=>void }){
  const [width,setWidth] = useState('3');
  const [qtyOff,setQtyOff] = useState('0');
  const [skuOff,setSkuOff] = useState('1');
  return (
    <View style={{ padding:12, borderWidth:1, borderColor:'#ddd', borderRadius:12, gap:8 }}>
      <Text style={{ fontWeight:'600' }}>{stopTitle}</Text>
      <Text>Block starts at column {startCol}. Choose mapping (adjust if needed):</Text>
      <View style={{ flexDirection:'row', gap:12 }}>
        <View style={{ width:100 }}>
          <Text>Width</Text>
          <TextInput keyboardType='number-pad' value={width} onChangeText={setWidth} style={{ borderWidth:1, padding:6 }}/>
        </View>
        <View style={{ width:140 }}>
          <Text>Qty offset</Text>
          <TextInput keyboardType='number-pad' value={qtyOff} onChangeText={setQtyOff} style={{ borderWidth:1, padding:6 }}/>
        </View>
        <View style={{ width:140 }}>
          <Text>SKU offset</Text>
          <TextInput keyboardType='number-pad' value={skuOff} onChangeText={setSkuOff} style={{ borderWidth:1, padding:6 }}/>
        </View>
      </View>
      <Button title="Use this mapping" onPress={()=> onConfirm({ stopTitle, startCol, width: Number(width)||3, qtyColOffset:Number(qtyOff)||0, skuColOffset:Number(skuOff)||1 }) } />
    </View>
  );
}
