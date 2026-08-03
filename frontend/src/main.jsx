import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initializeTheme } from './utils/theme'
import './index.css'
import App from './App.jsx'

initializeTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
