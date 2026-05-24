import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [
    vue(),
    // ─── ADD THIS PLUGINS CONFIG FOR AUTOMATIC CLEANUP ───
    {
      name: 'remove-localhost-prefix',
      transform(code, id) {
        // Intercept and strip out the local address string across all Vue and JS components during build compilation
        if (id.endsWith('.vue') || id.endsWith('.js')) {
          const updatedCode = code.replace(/http:\/\/127\.0\.0\.1:5000/g, '');
          return { code: updatedCode, map: null };
        }
      }
    }
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});