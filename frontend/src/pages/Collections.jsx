import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listCollections, createCollection, deleteCollection } from '../api'

function Collections() {
  const [collections, setCollections] = useState([])
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadCollections()
  }, [])

  async function loadCollections() {
    setLoading(true)
    try {
      setCollections(await listCollections())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      const collection = await createCollection(newName.trim())
      setCollections([...collections, collection].sort((a, b) => a.name.localeCompare(b.name)))
      setNewName('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    const confirmed = window.confirm('Delete this collection? Notes will be kept but unassigned.')
    if (!confirmed) return
    try {
      await deleteCollection(id)
      setCollections(collections.filter((c) => c.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return <div className="p-8 text-gray-500">Loading...</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-4 lg:px-6 py-6 lg:py-8">
      <h1 className="font-bold text-lg text-gray-900 mb-1">Collections</h1>
      <p className="text-sm text-gray-400 mb-6">
        Flat groups to organize your notes. Click a collection to view its notes.
      </p>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <form onSubmit={handleCreate} className="flex gap-2 mb-8">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New collection name..."
          className="flex-1 border border-card-border rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent/30"
        />
        <button
          type="submit"
          className="bg-accent hover:bg-accent-hover text-white text-sm font-semibold px-4 py-2 rounded-lg shrink-0"
        >
          Create
        </button>
      </form>

      {collections.length === 0 && (
        <p className="text-gray-400 text-sm">No collections yet — create one above.</p>
      )}

      <ul className="space-y-2">
        {collections.map((collection) => (
          <li
            key={collection.id}
            className="bg-white border border-card-border rounded-lg px-4 py-3 flex justify-between items-center hover:shadow-sm transition-shadow"
          >
            <Link
              to={`/dashboard?collection=${collection.id}`}
              className="font-medium text-gray-900 hover:text-accent"
            >
              {collection.name}
              <span className="ml-2 text-xs text-gray-400 font-normal">
                {collection.note_count} {collection.note_count === 1 ? 'note' : 'notes'}
              </span>
            </Link>
            <button
              onClick={() => handleDelete(collection.id)}
              className="text-red-400 text-xs hover:text-red-600"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default Collections
