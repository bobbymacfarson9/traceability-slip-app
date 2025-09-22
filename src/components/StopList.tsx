import React, { useRef, useState } from 'react';
import { View, Text, Button, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';

interface Stop {
  title: string;
  col: number;
  row: number;
}

interface StopListProps {
  stops: Stop[];
  onStopSelect: (stop: Stop) => void;
  onStopComplete: (stopTitle: string) => void;
  completedStops: string[];
  disabled?: boolean; // NEW: disable taps while loading
}

export const StopList: React.FC<StopListProps> = ({
  stops,
  onStopSelect,
  onStopComplete,
  completedStops,
  disabled = false,
}) => {
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const lastTapRef = useRef<number>(0);

  const handleStopPress = (stop: Stop) => {
    if (disabled) return;
    if (completedStops.includes(stop.title)) return;

    // debounce rapid taps
    const now = Date.now();
    if (now - lastTapRef.current < 400) return;
    lastTapRef.current = now;

    setSelectedStop(stop.title);
    onStopSelect(stop);
  };

  const handleComplete = (stopTitle: string) => {
    onStopComplete(stopTitle);
    setSelectedStop(null);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Stops ({stops.length})</Text>

      <ScrollView style={styles.list} keyboardShouldPersistTaps="handled">
        {stops.map((stop, index) => {
          const isCompleted = completedStops.includes(stop.title);
          const isSelected = selectedStop === stop.title;

          return (
            <TouchableOpacity
              key={`${stop.title}-${index}`}
              style={[
                styles.stopItem,
                isCompleted && styles.completedStop,
                isSelected && styles.selectedStop,
                disabled && { opacity: 0.5 },
              ]}
              onPress={() => handleStopPress(stop)}
              disabled={isCompleted || disabled}
            >
              <View style={styles.stopContent}>
                <Text style={[styles.stopTitle, isCompleted && styles.completedText]}>
                  {stop.title}
                </Text>
                {isCompleted && (
                  <Text style={styles.completedLabel}>✓ Completed</Text>
                )}
              </View>

              {!isCompleted && (
                <Button
                  title="Complete"
                  onPress={() => handleComplete(stop.title)}
                  color="#16a34a"
                />
              )}
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 16,
  },
  list: {
    flex: 1,
  },
  stopItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    marginBottom: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  completedStop: {
    backgroundColor: '#f0fdf4',
    borderColor: '#16a34a',
  },
  selectedStop: {
    backgroundColor: '#eff6ff',
    borderColor: '#3b82f6',
  },
  stopContent: {
    flex: 1,
  },
  stopTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  completedText: {
    color: '#16a34a',
  },
  completedLabel: {
    fontSize: 16,
    color: '#16a34a',
    fontWeight: '500',
    marginTop: 4,
  },
});