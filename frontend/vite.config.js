import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    base: '/app/',
    // Firebase Hosting publishes landing-site/out. Build the React cockpit
    // directly into the /app subfolder so production always receives the
    // latest frontend instead of a stale previously-generated bundle.
    build: {
        outDir: '../landing-site/out/app',
        emptyOutDir: true,
    },
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
