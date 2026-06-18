import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    base: '/app/',
    plugins: [
        react(),
        tailwindcss(),
    ],
    server: {
        proxy: {
            '/scan':         { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/businesses':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/orchestrate':  { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/deploy':       { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/stream':       { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/preview':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/sites':        { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/admin':        { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/status':       { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/geocode':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
        }
    }
})
