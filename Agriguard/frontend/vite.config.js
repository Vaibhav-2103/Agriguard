import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/conversations': 'http://127.0.0.1:8000',
      '/expert': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
      '/supported-crops': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000'
    }
  }
})
