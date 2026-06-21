import { fileURLToPath, URL } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: { port: 5173 },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          // Split only the heavy leaf libraries; keep React et al. in `vendor` to avoid
          // circular chunk references.
          if (id.includes('firebase') || id.includes('@firebase')) return 'firebase'
          if (id.includes('recharts') || id.includes('d3-') || id.includes('victory'))
            return 'charts'
          return 'vendor'
        },
      },
    },
  },
})
