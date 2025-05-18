import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        host: true,
        port: 3000,
        proxy: {
            '/api': {
                // Целевой адрес бэкенда в Docker сети
                target: 'http://backend:5000',
                changeOrigin: true,
            }
        }
    },
    preview: {
        host: true,
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://backend:5000',
                changeOrigin: true,
            }
        }
    },
});