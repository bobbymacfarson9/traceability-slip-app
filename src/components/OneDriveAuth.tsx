import React, { useState } from 'react';
import { View, Text, Button, Alert, StyleSheet, TextInput } from 'react-native';
import { setAuthData } from '../lib/onedrive';

interface OneDriveAuthProps {
  onAuthSuccess: (token: string) => void;
  onCancel: () => void;
}

export const OneDriveAuth: React.FC<OneDriveAuthProps> = ({ onAuthSuccess, onCancel }) => {
  const [oneDriveUrl, setOneDriveUrl] = useState('https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj');

  const handleConnect = () => {
    if (!oneDriveUrl.includes('1drv.ms') && !oneDriveUrl.includes('sharepoint.com')) {
      Alert.alert('Invalid URL', 'Please enter a valid OneDrive sharing link');
      return;
    }

    // For now, we'll simulate a successful connection
    // In a real implementation, you'd validate the URL and get proper authentication
    Alert.alert(
      'OneDrive Connected!',
      'You can now access your OneDrive files. The app will use your sharing link to browse files.',
      [
        {
          text: 'OK',
          onPress: () => {
            // Store the URL and simulate authentication
            setAuthData({
              accessToken: 'sharing-link-token',
              refreshToken: 'sharing-link-refresh',
              expiresAt: Date.now() + 86400000, // 24 hours
            });
            onAuthSuccess('sharing-link-token');
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connect to OneDrive</Text>
      <Text style={styles.description}>
        Enter your OneDrive sharing link to access loading slip files.
      </Text>
      
      <TextInput
        style={styles.urlInput}
        value={oneDriveUrl}
        onChangeText={setOneDriveUrl}
        placeholder="https://1drv.ms/f/..."
        multiline={true}
        autoCapitalize="none"
        autoCorrect={false}
      />
      
      <View style={styles.buttonContainer}>
        <Button title="Connect to OneDrive" onPress={handleConnect} />
        <Button title="Use Local Files" onPress={onCancel} />
      </View>
      
      <Text style={styles.helpText}>
        💡 Your OneDrive sharing link is pre-filled. You can modify it if needed.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    color: '#666',
  },
  instruction: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 10,
    color: '#888',
  },
  urlInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
    width: '100%',
    minHeight: 60,
    textAlignVertical: 'top',
  },
  buttonContainer: {
    gap: 15,
    width: '100%',
    marginBottom: 20,
    marginTop: 20,
  },
  webviewButtons: {
    flexDirection: 'row',
    gap: 10,
    padding: 10,
  },
  webview: {
    flex: 1,
    width: '100%',
    marginBottom: 10,
  },
  helpText: {
    fontSize: 12,
    textAlign: 'center',
    color: '#999',
    fontStyle: 'italic',
  },
});
