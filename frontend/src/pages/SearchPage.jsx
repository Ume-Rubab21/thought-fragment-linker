import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import { listCollections, listNotes, listTags, searchNotes } from '../api'
import { shortText } from '../utils/richText'

function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [notes, setNotes] = useState([])
  const [tags, setTags] = useState([])
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      query.trim() ? searchNotes(query.trim()) : listNotes(),
      listTags(),
      listCollections(),
    ])
      .then(([noteData, tagData, collectionData]) => {
        setNotes(noteData)
        setTags(tagData)
        setCollections(collectionData)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const matchingTags = useMemo(() => {
    if (!query.trim()) return tags.slice(0, 8)
    const needle = query.toLowerCase()
    return tags.filter((tag) => tag.name.includes(needle)).slice(0, 8)
  }, [query, tags])

  const matchingCollections = useMemo(() => {
    if (!query.trim()) return collections.slice(0, 8)
    const needle = query.toLowerCase()
    return collections.filter((collection) => collection.name.toLowerCase().includes(needle)).slice(0, 8)
  }, [query, collections])

  async function runSearch(event) {
    event?.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = query.trim() ? await searchNotes(query.trim()) : await listNotes()
      setNotes(result)
      setSearchParams(query.trim() ? { q: query.trim() } : {}, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell title="Search" subtitle="Find notes, tags, and collections">
      <form className="global-search panel" onSubmit={runSearch}>
        <Icon name="search" size={18} />
        <input
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search your knowledge base..."
        />
        <button className="primary-button" type="submit">Search</button>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      <section className="search-section">
        <div className="section-title-row">
          <h2>Notes</h2>
          <span>{loading ? 'Searching…' : notes.length}</span>
        </div>
        <div className="search-note-results">
          {!loading && notes.length === 0 && <div className="panel empty-search-result">No matching notes were found.</div>}
          {notes.slice(0, 10).map((note) => (
            <Link className="search-note-card panel" to={`/notes/${note.id}`} key={note.id}>
              <span className="search-result-icon"><Icon name="notes" size={17} /></span>
              <div>
                <h3>{note.title}</h3>
                <p>{shortText(note.body_md, 220) || 'Empty note'}</p>
                <div className="inline-chips">
                  {note.tags.slice(0, 5).map((tag) => <span key={tag.id}>{tag.name}</span>)}
                </div>
              </div>
              <Icon name="arrowLeft" className="result-arrow" size={17} />
            </Link>
          ))}
        </div>
      </section>

      <section className="search-section">
        <div className="section-title-row"><h2>Tags</h2><span>{matchingTags.length}</span></div>
        <div className="search-chip-panel panel">
          {matchingTags.length ? matchingTags.map((tag) => (
            <Link key={tag.id} to={`/notes?tag=${encodeURIComponent(tag.name)}`} className="search-chip">
              <Icon name="tag" size={14} /> {tag.name} <small>{tag.note_count || 0}</small>
            </Link>
          )) : <span className="muted-copy">No matching tags.</span>}
        </div>
      </section>

      <section className="search-section">
        <div className="section-title-row"><h2>Collections</h2><span>{matchingCollections.length}</span></div>
        <div className="search-chip-panel panel">
          {matchingCollections.length ? matchingCollections.map((collection) => (
            <Link key={collection.id} to={`/notes?collection=${collection.id}`} className="search-chip">
              <Icon name="folder" size={14} /> {collection.name} <small>{collection.note_count || 0}</small>
            </Link>
          )) : <span className="muted-copy">No matching collections.</span>}
        </div>
      </section>
    </AppShell>
  )
}

export default SearchPage
