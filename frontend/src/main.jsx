import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { installAdminAuth } from './adminAuth.js'
import './index.css'

installAdminAuth()

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)
