import React from 'react';
import { View, Text, Button, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';

interface SheetPickerProps {
  sheetNames: string[];
  onSheetSelect: (sheetName: string) => void;
  onCancel: () => void;
}

export const SheetPicker: React.FC<SheetPickerProps> = ({ sheetNames, onSheetSelect, onCancel }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Select Loading Slip Sheet</Text>
      <Text style={styles.subtitle}>
        Choose which day's loading slip to work with:
      </Text>
      
      <ScrollView style={styles.scrollView}>
        {sheetNames.map((sheetName, index) => (
          <TouchableOpacity
            key={index}
            style={styles.sheetItem}
            onPress={() => onSheetSelect(sheetName)}
          >
            <Text style={styles.sheetName}>{sheetName}</Text>
            <Text style={styles.sheetDescription}>
              {getSheetDescription(sheetName)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      
      <View style={styles.footer}>
        <Button title="Cancel" onPress={onCancel} />
      </View>
    </View>
  );
};

// Helper function to provide descriptions for common sheet names
const getSheetDescription = (sheetName: string): string => {
  const name = sheetName.toLowerCase();
  if (name.includes('monday') || name.includes('mon')) return 'Monday loading slip';
  if (name.includes('tuesday') || name.includes('tue')) return 'Tuesday loading slip';
  if (name.includes('wednesday') || name.includes('wed')) return 'Wednesday loading slip';
  if (name.includes('thursday') || name.includes('thu')) return 'Thursday loading slip';
  if (name.includes('friday') || name.includes('fri')) return 'Friday loading slip';
  if (name.includes('week')) return 'Weekly loading slip';
  return 'Loading slip sheet';
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
    textAlign: 'center',
  },
  scrollView: {
    flex: 1,
  },
  sheetItem: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sheetName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  sheetDescription: {
    fontSize: 14,
    color: '#666',
  },
  footer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
});
