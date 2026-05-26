import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'https://api.spacecoaststudios.com',
      '/contact': 'https://api.spacecoaststudios.com',
      '/cal': 'https://api.spacecoaststudios.com',
      '/voice': 'https://api.spacecoaststudios.com',
      '/chat': 'https://api.spacecoaststudios.com',
    },
  },
})
