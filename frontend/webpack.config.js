const path = require('path');

module.exports = {
  // Other configuration options...
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
};
