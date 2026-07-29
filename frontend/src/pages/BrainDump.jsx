import { useEffect, useState } from 'react'
import {
  submitBrainDump,
  getBrainDumpStatus,
  getBrainDump,
} from '../api'

export default function BrainDump() {
  const [text, setText] = useState('')
  const [brainDumpId, setBrainDumpId] = useState(null)

  const [status, setStatus] = useState(null)

  const [result, setResult] = useState(null)

  const [loading, setLoading] = useState(false)

  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()

    setError('')
    setResult(null)

    const response = await submitBrainDump(text)

    setBrainDumpId(response.id)

    setStatus(response.status)

    setLoading(true)
  }

  useEffect(() => {
    if (!brainDumpId) return

    const interval = setInterval(async () => {
      const res = await getBrainDumpStatus(brainDumpId)

      setStatus(res.status)

      if (res.status === 'ready') {
        clearInterval(interval)

        const completed = await getBrainDump(brainDumpId)

        setResult(completed)

        setLoading(false)
      }

      if (res.status === 'failed') {
        clearInterval(interval)

        setLoading(false)

        setError('Processing failed.')
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [brainDumpId])

  return (
    <div style={{ padding: 40 }}>

      <h1>Brain Dump</h1>

      <form onSubmit={handleSubmit}>

        <textarea
          rows={12}
          style={{ width: '100%' }}
          value={text}
          onChange={(e)=>setText(e.target.value)}
        />

        <br/><br/>

        <button disabled={loading}>
          Process Brain Dump
        </button>

      </form>

      {loading && (
        <div
          style={{
            marginTop:30,
            padding:20,
            background:'#eef',
            borderRadius:10
          }}
        >

          <h2>🤖 Agent is thinking...</h2>

          <p>Status: {status}</p>

        </div>
      )}

      {result && (

        <div
          style={{
            marginTop:30,
            padding:20,
            background:'#efe',
            borderRadius:10
          }}
        >

          <h2>Completed</h2>

          <pre>{result.raw_text}</pre>

        </div>

      )}

      {error &&

        <p style={{color:'red'}}>
          {error}
        </p>

      }

    </div>
  )
}