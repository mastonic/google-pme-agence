import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { copyFileSync } from 'fs'
import path from 'path'

export default defineConfig({
    base: '/app/',
    plugins: [
        react(),
        tailwindcss(),
        {
            // After build: copy landing/index.html → dist/index.html so Firebase
            // serves it at "/" while the SPA lives at /app/**
            name: 'copy-landing-to-dist-root',
            closeBundle() {
                const src  = path.resolve(__dirname, '../landing/index.html')
                const dest = path.resolve(__dirname, 'dist/index.html')
                try {
                    copyFileSync(src, dest)
                    console.log('✅ Landing page copied to dist/index.html')
                } catch (e) {
                    console.warn('⚠️  copy-landing:', e.message)
                }
            },
        },
    ],
    build: {
        outDir: 'dist/app',
        emptyOutDir: true,
    },
    server: {
        proxy: {
            '/scan':              { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/businesses':        { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/orchestrate':       { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/deploy':            { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/stream':            { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/preview':           { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/sites':             { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/admin':             { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/status':            { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/geocode':           { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/crm':               { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/monitor':           { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/photo':             { target: 'http://127.0.0.1:8000', changeOrigin: true },
            '/recalculate-scores':{ target: 'http://127.0.0.1:8000', changeOrigin: true },
        }
    }
})
