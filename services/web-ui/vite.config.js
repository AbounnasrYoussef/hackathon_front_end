import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/alerts': 'http://localhost:8001',
      '/incidents': 'http://localhost:8002',
      '/auth': 'http://localhost:8003',
      '/oncall': 'http://localhost:8003',
      '/notifications': 'http://localhost:8004'
    }
  }
})
