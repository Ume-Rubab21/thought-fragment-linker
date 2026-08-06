import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import {
  createNote,
  deleteNote,
  listCollections,
  listNotes,
  listTags,
  searchNotes,
} from '../api'
import { shortText } from '../utils/richText'
import {
  readInstantCache,
  removeInstantCacheByPrefix,
  writeInstantCache,
} from '../utils/instantCache'

function AllNotes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialNotes = readInstantCache('notes:::', null)
  const initialTags = readInstantCache('tags', null)
  const initialCollections = readInstantCache('collections', null)
  const [notes, setNotes] = useState(initialNotes || [])
  const [tags, setTags] = useState(initialTags || [])
  const [collections, setCollections] = useState(initialCollections || [])
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [tag, setTag] = useState(searchParams.get('tag') || '')
  const [collectionId, setCollectionId] = useState(searchParams.get('collection') || '')
  const [view, setView] = useState(localStorage.getItem('tfl_notes_view') || 'grid')
  const [loading, setLoading] = useState(!initialNotes)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const loadNotes = useCallback(async (searchValue = query, options = {}) => {
    const cleanedSearch = searchValue.trim()
    const cacheKey = `notes:${cleanedSearch}:${tag}:${collectionId}`
    const cached = readInstantCache(cacheKey, null)

    if (cached) {
      setNotes(cached)
      setLoading(false)
    } else if (!options.background) {
      setLoading(true)
    }

    setError('')

    try {
      const filters = { tag, collection_id: collectionId }
      const data = cleanedSearch
        ? await searchNotes(cleanedSearch, filters)
        : await listNotes(filters)
      setNotes(data)
      writeInstantCache(cacheKey, data)
      if (!cleanedSearch && !tag && !collectionId) {
        writeInstantCache('notes:::', data)
      }
    } catch (err) {
      // Keep already displayed cached notes if the backend is waking up.
      if (!cached) setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [query, tag, collectionId])

  useEffect(() => {
    Promise.all([listTags(), listCollections()])
      .then(([tagData, collectionData]) => {
        setTags(tagData)
        setCollections(collectionData)
        writeInstantCache('tags', tagData)
        writeInstantCache('collections', collectionData)
      })
      .catch((err) => {
        if (!initialTags && !initialCollections) setError(err.message)
      })
  }, []) // cached values make this page display immediately

  useEffect(() => {
    loadNotes()
    const next = {}
    if (query) next.q = query
    if (tag) next.tag = tag
    if (collectionId) next.collection = collectionId
    setSearchParams(next, { replace: true })
  }, [tag, collectionId]) // eslint-disable-line react-hooks/exhaustive-deps

  const collectionLookup = useMemo(
    () => Object.fromEntries(collections.map((item) => [item.id, item.name])),
    [collections],
  )

  async function handleNewNote() {
    try {
      const note = await createNote('Untitled note', '<p></p>', collectionId || null)
      navigate(`/notes/${note.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(event, noteId) {
    event.stopPropagation()
    if (!window.confirm('Delete this note? This cannot be undone.')) return
    try {
      await deleteNote(noteId)

      setNotes((current) =>
        current.filter((note) => note.id !== noteId),
      )

      // Clear every filtered Notes cache and every AI Suggestions cache.
      // Otherwise old cached records can remain visible after deletion.
      removeInstantCacheByPrefix('notes:')
      removeInstantCacheByPrefix('suggestions:')
      removeInstantCacheByPrefix('suggestion-detail:')
    } catch (err) {
      setError(err.message)
    }
  }

  function submitSearch(event) {
    event.preventDefault()
    loadNotes(query)
    const next = {}
    if (query) next.q = query
    if (tag) next.tag = tag
    if (collectionId) next.collection = collectionId
    setSearchParams(next, { replace: true })
  }

  async function clearFilters() {
    setTag('')
    setCollectionId('')
    setQuery('')
    setSearchParams({}, { replace: true })
    setLoading(true)
    try {
      setNotes(await listNotes())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function changeView(next) {
    setView(next)
    localStorage.setItem('tfl_notes_view', next)
  }

  return (
    <AppShell title="All Notes" actions={
      <button className="primary-button" onClick={handleNewNote}><Icon name="plus" size={16} /> New</button>
    }>
      <section className="notes-toolbar panel">
        <form className="notes-search" onSubmit={submitSearch}>
          <Icon name="search" size={17} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search notes..." />
          {query && <button type="button" className="clear-search" onClick={() => { setQuery(''); loadNotes('') }}><Icon name="close" size={14} /></button>}
        </form>
        <select value={tag} onChange={(event) => setTag(event.target.value)} aria-label="Filter by tag">
          <option value="">All tags</option>
          {tags.map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}
        </select>
        <select value={collectionId} onChange={(event) => setCollectionId(event.target.value)} aria-label="Filter by collection">
          <option value="">All collections</option>
          {collections.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <div className="view-toggle" aria-label="Note view">
          <button className={view === 'grid' ? 'is-active' : ''} onClick={() => changeView('grid')} title="Grid view"><Icon name="grid" size={16} /></button>
          <button className={view === 'list' ? 'is-active' : ''} onClick={() => changeView('list')} title="List view"><Icon name="list" size={16} /></button>
        </div>
      </section>

      {error && <div className="alert alert--error">{error}</div>}
      <div className="notes-results-heading">
        <span>{loading ? 'Loading notes…' : `${notes.length} note${notes.length === 1 ? '' : 's'}`}</span>
        {(tag || collectionId || query) && <button className="text-button" onClick={clearFilters}>Clear filters</button>}
      </div>

      {loading ? (
        <div className={`notes-${view}`}>
          {Array.from({ length: 6 }).map((_, index) => <div className="note-card skeleton-card" key={index} />)}
        </div>
      ) : notes.length ? (
        <div className={`notes-${view}`}>
          {notes.map((note, index) => (
            <article
              className={`note-card ${index === 1 && view === 'grid' ? 'is-featured' : ''}`}
              key={note.id}
              onClick={() => navigate(`/notes/${note.id}`)}
              tabIndex="0"
              onKeyDown={(event) => event.key === 'Enter' && navigate(`/notes/${note.id}`)}
            >
              <div className="note-card__top">
                <span className="note-card__icon"><Icon name="notes" size={15} /></span>
                <button className="note-card__menu danger-icon" title="Delete" onClick={(event) => handleDelete(event, note.id)}><Icon name="trash" size={15} /></button>
              </div>
              <h2>{note.title}</h2>
              <p>{shortText(note.body_md, view === 'grid' ? 145 : 220) || 'Start writing your ideas…'}</p>
              <div className="note-card__tags">
                {note.tags.slice(0, 3).map((item) => <span key={item.id}>{item.name}</span>)}
              </div>
              <footer>
                <span><Icon name="clock" size={13} /> {new Date(note.updated_at).toLocaleDateString()}</span>
                {note.collection_id && <span><Icon name="folder" size={13} /> {collectionLookup[note.collection_id] || 'Collection'}</span>}
              </footer>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state panel">
          <span className="empty-state__icon"><Icon name="notes" size={28} /></span>
          <h2>No notes found</h2>
          <p>Try another search or create a new note.</p>
          <button className="primary-button" onClick={handleNewNote}><Icon name="plus" size={16} /> New note</button>
        </div>
      )}
    </AppShell>
  )
}

export default AllNotes
