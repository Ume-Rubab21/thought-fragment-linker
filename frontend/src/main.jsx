import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initializeTheme } from './utils/theme'
import { initializePreferences } from './utils/preferences'
import './index.css'
import App from './App.jsx'
import { getToken } from './api'
import { prefetchCorePages } from './utils/instantData'

initializeTheme()
initializePreferences()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

if (getToken()) {
  window.setTimeout(() => prefetchCorePages(), 0)
}
