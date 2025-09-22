const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add resolver to handle PlatformConstants
config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];
config.resolver.alias = {
  'react-native/Libraries/Utilities/PlatformConstants': require.resolve('./src/lib/platform.ts'),
};

module.exports = config;
