import React, { useState, useEffect } from 'react';
import { View, Text, Button, FlatList, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { getOneDriveFiles, downloadOneDriveFile, OneDriveFile } from '../lib/onedrive';

interface OneDriveFileBrowserProps {
  onFileSelect: (file: OneDriveFile) => void;
  onClose: () => void;
}

export const OneDriveFileBrowser: React.FC<OneDriveFileBrowserProps> = ({ onFileSelect, onClose }) => {
  const [files, setFiles] = useState<OneDriveFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const fileList = await getOneDriveFiles();
      setFiles(fileList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  const handleFilePress = async (file: OneDriveFile) => {
    try {
      // Download the file and pass it to the parent
      const arrayBuffer = await downloadOneDriveFile(file);
      onFileSelect(file);
    } catch (err) {
      Alert.alert('Error', 'Failed to download file. Please try again.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const renderFileItem = ({ item }: { item: OneDriveFile }) => (
    <View style={styles.fileItem}>
      <View style={styles.fileInfo}>
        <Text style={styles.fileName}>📄 {item.name}</Text>
        <Text style={styles.fileDetails}>
          {formatFileSize(item.size)} • {formatDate(item.lastModifiedDateTime)}
        </Text>
      </View>
      <Button title="Load" onPress={() => handleFilePress(item)} />
    </View>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Loading OneDrive Files...</Text>
        <ActivityIndicator size="large" color="#007AFF" />
        <Button title="Cancel" onPress={onClose} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Error Loading Files</Text>
        <Text style={styles.errorText}>{error}</Text>
        <View style={styles.buttonContainer}>
          <Button title="Retry" onPress={loadFiles} />
          <Button title="Cancel" onPress={onClose} />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>OneDrive Files</Text>
        <Text style={styles.subtitle}>{files.length} Excel files found</Text>
      </View>
      
      <FlatList
        data={files}
        renderItem={renderFileItem}
        keyExtractor={(item) => item.id}
        style={styles.fileList}
        showsVerticalScrollIndicator={true}
      />
      
      <View style={styles.footer}>
        <Button title="Refresh" onPress={loadFiles} />
        <Button title="Close" onPress={onClose} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    color: '#666',
  },
  fileList: {
    flex: 1,
  },
  fileItem: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  fileInfo: {
    flex: 1,
    marginRight: 12,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  fileDetails: {
    fontSize: 12,
    color: '#666',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#ff4444',
    textAlign: 'center',
    marginBottom: 20,
  },
});
