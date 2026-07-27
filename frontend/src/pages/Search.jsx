import { useState } from 'react'
import { searchNotes } from '../api'
import NoteListItem from '../components/NoteListItem'

function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError('')
    try {
      const data = await searchNotes(query.trim())
      setResults(data)
      setSearched(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 lg:px-6 py-6 lg:py-8">
      <h1 className="font-bold text-lg text-gray-900 mb-1">Search</h1>
      <p className="text-sm text-gray-400 mb-6">
        Full-text search across note titles and content.
      </p>

      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search notes..."
          className="flex-1 border border-card-border rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent/30"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-accent hover:bg-accent-hover text-white text-sm font-semibold px-4 py-2 rounded-lg shrink-0 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {searched && !loading && (
        <p className="text-sm text-gray-400 mb-4">
          {results.length} {results.length === 1 ? 'result' : 'results'} for &ldquo;{query}&rdquo;
        </p>
      )}

      {results.length === 0 && searched && !loading && (
        <p className="text-gray-400 text-sm">No notes matched your search.</p>
      )}

      <ul className="space-y-2">
        {results.map((note) => (
          <NoteListItem
            key={note.id}
            note={note}
            onDelete={() => {}}
            showTags={false}
            showDelete={false}
          />
        ))}
      </ul>
    </div>
  )
}

export default Search
