import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Dev: /api is proxied to the FastAPI backend. Production: `npm run build` writes web/dist, which FastAPI serves at "/".
// assetsDir is "bundle" so hashed JS/CSS never mix with the copied art in public/assets.
export default defineConfig({
  plugins: [react()],
  build: { assetsDir: 'bundle', sourcemap: false, chunkSizeWarningLimit: 700 },
  server: { port: 5173, proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } } },
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
});
