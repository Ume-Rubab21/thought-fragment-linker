import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initializeTheme } from './utils/theme'
import { initializePreferences } from './utils/preferences'
import './index.css'
import App from './App.jsx'

initializeTheme()
initializePreferences()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
