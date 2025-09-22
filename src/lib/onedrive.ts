import * as FileSystem from 'expo-file-system';

// OneDrive sharing link configuration
const ONEDRIVE_SHARING_URL = 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj';

export interface OneDriveFile {
  id: string;
  name: string;
  downloadUrl: string;
  lastModifiedDateTime: string;
  size: number;
  webUrl: string;
}

export interface OneDriveAuth {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

// Store auth in memory (in production, use secure storage)
let authData: OneDriveAuth | null = null;

export const setAuthData = (auth: OneDriveAuth) => {
  authData = auth;
};

export const getAuthData = (): OneDriveAuth | null => {
  return authData;
};

// Convert OneDrive sharing URL to API endpoint
const getApiEndpointFromSharingUrl = (sharingUrl: string): string => {
  // Extract the sharing token from the URL
  const match = sharingUrl.match(/\/c\/([a-zA-Z0-9_-]+)/);
  if (!match) {
    throw new Error('Invalid OneDrive sharing URL');
  }
  
  const sharingToken = match[1];
  return `https://graph.microsoft.com/v1.0/shares/${sharingToken}/driveItem/children`;
};

// Get OneDrive files from the shared folder
export const getOneDriveFiles = async (): Promise<OneDriveFile[]> => {
  if (!authData) {
    throw new Error('Not authenticated with OneDrive');
  }

  try {
    // For now, return mock data to test the UI
    // In a real implementation, you'd use the Microsoft Graph API
    const mockFiles: OneDriveFile[] = [
      {
        id: '1',
        name: 'Loading Slip Week 10 2025.xlsx',
        downloadUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
        lastModifiedDateTime: new Date().toISOString(),
        size: 45678,
        webUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
      },
      {
        id: '2',
        name: 'Loading Slip Week 9 2025.xlsx',
        downloadUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
        lastModifiedDateTime: new Date(Date.now() - 86400000).toISOString(),
        size: 42345,
        webUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
      },
      {
        id: '3',
        name: 'Loading Slip Week 8 2025.xlsx',
        downloadUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
        lastModifiedDateTime: new Date(Date.now() - 172800000).toISOString(),
        size: 41234,
        webUrl: 'https://1drv.ms/f/c/3d6fd4998059ff0f/Eg8xBD2kZ5JCgjBb1DZCxz8BunT3ljPB98zLLkB84OI0Hg?e=GPylzj',
      },
    ];

    return mockFiles;
  } catch (error) {
    console.error('Error fetching OneDrive files:', error);
    throw error;
  }
};

// Download a file from OneDrive - simplified approach
export const downloadOneDriveFile = async (file: OneDriveFile): Promise<ArrayBuffer> => {
  if (!authData) {
    throw new Error('Not authenticated with OneDrive');
  }

  try {
    console.log(`OneDrive file selected: ${file.name}`);
    
    // For now, we'll show a message that OneDrive integration is in progress
    // and suggest using local files for testing
    throw new Error('OneDrive direct download requires proper authentication setup. Please use "Pick local file" to test the app with your Excel files.');
  } catch (error) {
    console.error('OneDrive download not yet implemented:', error);
    throw error;
  }
};

// Get the latest loading slip file (by date in filename)
export const getLatestLoadingSlip = async (): Promise<OneDriveFile | null> => {
  try {
    const files = await getOneDriveFiles();
    
    // Filter for loading slip files and sort by name (which should contain dates)
    const loadingSlips = files
      .filter(file => file.name.toLowerCase().includes('loading slip'))
      .sort((a, b) => b.name.localeCompare(a.name)); // Sort descending to get latest first
    
    return loadingSlips.length > 0 ? loadingSlips[0] : null;
  } catch (error) {
    console.error('Error getting latest loading slip:', error);
    return null;
  }
};

// Check for updates to the current file
export const checkForFileUpdates = async (currentFileName: string): Promise<boolean> => {
  try {
    const files = await getOneDriveFiles();
    const currentFile = files.find(file => file.name === currentFileName);
    
    if (!currentFile) {
      return false; // File not found
    }
    
    // You could store the last modified time and compare
    // For now, we'll just return true to indicate updates are possible
    return true;
  } catch (error) {
    console.error('Error checking for file updates:', error);
    return false;
  }
};

// Simple authentication using device credentials
export const authenticateWithOneDrive = async (): Promise<OneDriveAuth> => {
  // For now, we'll use a simple approach that works with your existing login
  // In production, you'd use proper OAuth flow
  
  // This is a placeholder - in reality, you'd implement proper OAuth
  // For testing, we can use the WebView approach but store the token properly
  throw new Error('Authentication not implemented yet - use WebView approach for now');
};
