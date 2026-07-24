import { useState, useEffect } from 'react'

// While developing locally, this falls back to localhost.
// Once deployed on Vercel, VITE_BACKEND_URL will be set to your
// live Railway URL instead (see Step 7 instructions).
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState('checking...')

  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('backend not reachable'))
  }, [])

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>Thought Fragment Linker</h1>
      <p>Backend status: <strong>{status}</strong></p>
    </div>
  )
}

export default App