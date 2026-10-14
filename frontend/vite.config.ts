import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Em desenvolvimento, /api e encaminhado ao FastAPI. Assim o frontend
// funciona tambem quando acessado pelo celular na rede local.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.API_PROXY_TARGET || 'http://127.0.0.1:8000';
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          ws: true,
          rewrite: (p) => p.replace(/^\/api/, ''),
        },
      },
    },
  };
});
