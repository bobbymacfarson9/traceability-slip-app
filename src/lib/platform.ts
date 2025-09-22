// Platform constants workaround for Expo Go compatibility
import { Platform } from 'react-native';

// Safe platform constants that work with Expo Go
export const PlatformConstants = {
  get: (key: string) => {
    // Return safe defaults for common platform constants
    switch (key) {
      case 'reactNativeVersion':
        return { major: 0, minor: 76, patch: 3 };
      case 'osVersion':
        return Platform.OS === 'ios' ? '17.0' : '14.0';
      case 'interfaceIdiom':
        return 'phone';
      default:
        return null;
    }
  }
};

// Export a safe version that won't crash
export default PlatformConstants;
