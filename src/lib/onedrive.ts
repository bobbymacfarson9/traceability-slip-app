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
    // Create realistic mock files based on actual loading slip naming patterns
    // In production, this would call the Microsoft Graph API
    const mockFiles: OneDriveFile[] = [
      {
        id: '1',
        name: 'Week 37 Loading Slip 2025.xlsx',
        downloadUrl: 'https://api.onedrive.com/v1.0/shares/placeholder/items/file1',
        lastModifiedDateTime: new Date().toISOString(),
        size: 45678,
        webUrl: 'https://1drv.ms/x/placeholder1',
      },
      {
        id: '2',
        name: 'Week 36 Loading Slip 2025.xlsx',
        downloadUrl: 'https://api.onedrive.com/v1.0/shares/placeholder/items/file2',
        lastModifiedDateTime: new Date(Date.now() - 86400000 * 7).toISOString(),
        size: 42345,
        webUrl: 'https://1drv.ms/x/placeholder2',
      },
      {
        id: '3',
        name: 'Week 35 Loading Slip 2025.xlsx',
        downloadUrl: 'https://api.onedrive.com/v1.0/shares/placeholder/items/file3',
        lastModifiedDateTime: new Date(Date.now() - 86400000 * 14).toISOString(),
        size: 41234,
        webUrl: 'https://1drv.ms/x/placeholder3',
      },
      {
        id: '4',
        name: 'Week 34 Loading Slip 2025.xlsx',
        downloadUrl: 'https://api.onedrive.com/v1.0/shares/placeholder/items/file4',
        lastModifiedDateTime: new Date(Date.now() - 86400000 * 21).toISOString(),
        size: 43567,
        webUrl: 'https://1drv.ms/x/placeholder4',
      },
    ];

    console.log(`Found ${mockFiles.length} OneDrive files`);
    return mockFiles;
  } catch (error) {
    console.error('Error fetching OneDrive files:', error);
    throw new Error('Failed to load OneDrive files. Please check your connection and try again.');
  }
};

// Download a file from OneDrive - simplified approach using sharing links
export const downloadOneDriveFile = async (file: OneDriveFile): Promise<ArrayBuffer> => {
  if (!authData) {
    throw new Error('Not authenticated with OneDrive');
  }

  try {
    console.log(`Attempting to download OneDrive file: ${file.name}`);
    
    // Try to download using the sharing URL approach
    // This is a simplified implementation that works with public sharing links
    const response = await fetch(file.downloadUrl);
    
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.status} ${response.statusText}`);
    }
    
    const arrayBuffer = await response.arrayBuffer();
    console.log(`Successfully downloaded ${file.name}, size: ${arrayBuffer.byteLength} bytes`);
    
    return arrayBuffer;
  } catch (error) {
    console.error('OneDrive download error:', error);
    throw new Error(`Failed to download ${file.name}. Please try using "Pick local file" instead.`);
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
