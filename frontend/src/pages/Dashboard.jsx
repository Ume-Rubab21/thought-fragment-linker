import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getMe, clearToken, listNotes, createNote, deleteNote } from '../api'

function Dashboard() {
  const [user, setUser] = useState(null)
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    loadEverything()
  }, [])

  async function loadEverything() {
    setLoading(true)
    try {
      const [meData, notesData] = await Promise.all([getMe(), listNotes()])
      setUser(meData)
      setNotes(notesData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateNote(e) {
    e.preventDefault()
    if (!newTitle.trim()) return

    try {
      const note = await createNote(newTitle)
      setNotes([note, ...notes])
      setNewTitle('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDeleteNote(id) {
    const confirmed = window.confirm('Delete this note? This cannot be undone.')
    if (!confirmed) return

    try {
      await deleteNote(id)
      setNotes(notes.filter((n) => n.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  if (loading) {
    return <div className="max-w-2xl mx-auto mt-12 px-4 font-sans">Loading...</div>
  }

  return (
    <div className="max-w-2xl mx-auto mt-12 px-4 font-sans">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Your Notes</h1>
        <button
          onClick={handleLogout}
          className="text-sm px-3 py-1 border rounded hover:bg-gray-100"
        >
          Log out
        </button>
      </div>

      {user && <p className="text-gray-500 text-sm mb-6">Logged in as: {user.email}</p>}
      {error && <p className="text-red-500 mb-4">{error}</p>}

      <form onSubmit={handleCreateNote} className="flex gap-2 mb-8">
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New note title..."
          className="flex-1 border rounded px-3 py-2"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Add
        </button>
      </form>

      {notes.length === 0 && (
        <p className="text-gray-400">No notes yet — create your first one above.</p>
      )}

      <ul className="space-y-2">
        {notes.map((note) => (
          <li
            key={note.id}
            className="border rounded px-4 py-3 flex justify-between items-center"
          >
            <Link to={`/notes/${note.id}`} className="text-blue-700 hover:underline">
              {note.title}
            </Link>
            <button
              onClick={() => handleDeleteNote(note.id)}
              className="text-red-500 text-sm hover:underline"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default Dashboard