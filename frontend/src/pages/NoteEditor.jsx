import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getNote, updateNote, deleteNote } from '../api'

function NoteEditor() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [title, setTitle] = useState('')
  const [bodyMd, setBodyMd] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    loadNote()
  }, [id])

  async function loadNote() {
    setLoading(true)
    try {
      const note = await getNote(id)
      setTitle(note.title)
      setBodyMd(note.body_md)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      await updateNote(id, { title, body_md: bodyMd })
      setSavedMessage('Saved')
      setTimeout(() => setSavedMessage(''), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm('Delete this note? This cannot be undone.')
    if (!confirmed) return

    try {
      await deleteNote(id)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return <div className="max-w-4xl mx-auto mt-12 px-4 font-sans">Loading...</div>
  }

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4 font-sans">
      <div className="flex justify-between items-center mb-4">
        <Link to="/dashboard" className="text-blue-600 hover:underline text-sm">
          &larr; Back to notes
        </Link>
        <div className="flex items-center gap-3">
          {savedMessage && <span className="text-green-600 text-sm">{savedMessage}</span>}
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 text-sm"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handleDelete}
            className="text-red-500 text-sm hover:underline"
          >
            Delete
          </button>
        </div>
      </div>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full text-xl font-bold border-b pb-2 mb-4 focus:outline-none"
        placeholder="Note title"
      />

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400 uppercase mb-1">Markdown</p>
          <textarea
            value={bodyMd}
            onChange={(e) => setBodyMd(e.target.value)}
            className="w-full h-[500px] border rounded p-3 font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-400"
            placeholder="Write in markdown..."
          />
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase mb-1">Preview</p>
          <div className="w-full h-[500px] border rounded p-3 overflow-y-auto prose prose-sm max-w-none">
            <ReactMarkdown>{bodyMd || '*Nothing to preview yet*'}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NoteEditor