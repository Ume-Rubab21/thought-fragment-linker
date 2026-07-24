import { useState, useEffect } from 'react'

// This is the address of your backend.
// While testing on your laptop, it points at localhost.
// Once the backend is deployed (Step 6), you'll change this
// to the real backend URL.
const BACKEND_URL = 'http://localhost:8000'

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