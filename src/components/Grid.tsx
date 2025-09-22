import React from 'react';
import { ScrollView, Text, View, Pressable } from 'react-native';

export function Grid({aoa, onStopTap}:{aoa:any[][]; onStopTap:(title:string,col:number)=>void}){
  return (
    <ScrollView style={{ flex: 1 }}>
      <ScrollView horizontal>
        <View>
          {aoa.slice(0,40).map((row,ri)=> (
            <View key={ri} style={{ flexDirection:'row' }}>
              {row.slice(0,28).map((cell,cj)=> {
                const val = cell==null? '' : String(cell);
                const isStop = /^\s*\d+\.\s+/.test(val);
                return (
                  <Pressable key={cj} onPress={()=>{ if(isStop) onStopTap(val.trim(), cj); }}>
                    <Text style={{ 
                      width: 120, 
                      height: 40,
                      borderWidth: 0.5, 
                      borderColor: '#ddd', 
                      padding: 6, 
                      backgroundColor: isStop? '#eef7ff':'#fff',
                      fontSize: 12,
                      textAlign: 'center',
                      textAlignVertical: 'center'
                    }} numberOfLines={2}>
                      {val}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </View>
      </ScrollView>
    </ScrollView>
  );
}
