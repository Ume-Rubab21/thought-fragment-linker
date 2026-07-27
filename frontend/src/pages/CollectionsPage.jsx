import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import { createCollection, deleteCollection, listCollections, updateCollection } from '../api'

function CollectionsPage() {
  const [collections, setCollections] = useState([])
  const [newName, setNewName] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    listCollections().then(setCollections).catch((err) => setError(err.message))
  }, [])

  async function create(event) {
    event.preventDefault()
    if (!newName.trim()) return
    try {
      const result = await createCollection(newName)
      setCollections((current) => [...current, result].sort((a, b) => a.name.localeCompare(b.name)))
      setNewName('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function rename(id) {
    if (!editingName.trim()) return
    try {
      const result = await updateCollection(id, editingName)
      setCollections((current) => current.map((item) => item.id === id ? result : item).sort((a, b) => a.name.localeCompare(b.name)))
      setEditingId(null)
    } catch (err) {
      setError(err.message)
    }
  }

  async function remove(collection) {
    if (!window.confirm(`Delete “${collection.name}”? Notes inside it will become unfiled.`)) return
    try {
      await deleteCollection(collection.id)
      setCollections((current) => current.filter((item) => item.id !== collection.id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AppShell title="Collections" subtitle="Flat groups for broad organization">
      <section className="management-toolbar panel">
        <div><span className="section-eyebrow">Collections</span><strong>{collections.length}</strong></div>
        <form onSubmit={create}>
          <input value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="New collection name" maxLength={60} />
          <button className="primary-button" type="submit"><Icon name="plus" size={15} /> Add collection</button>
        </form>
      </section>
      {error && <div className="alert alert--error">{error}</div>}
      <div className="management-grid collections-grid">
        {collections.map((collection, index) => (
          <article className={`management-card ${index === 0 ? 'is-featured' : ''}`} key={collection.id}>
            <div className="management-card__top">
              <span className="management-icon"><Icon name="folder" size={16} /></span>
              <div className="management-actions">
                <button onClick={() => { setEditingId(collection.id); setEditingName(collection.name) }} title="Rename"><Icon name="edit" size={14} /></button>
                <button onClick={() => remove(collection)} title="Delete"><Icon name="trash" size={14} /></button>
              </div>
            </div>
            {editingId === collection.id ? (
              <div className="inline-edit">
                <input autoFocus value={editingName} onChange={(event) => setEditingName(event.target.value)} onKeyDown={(event) => {
                  if (event.key === 'Enter') rename(collection.id)
                  if (event.key === 'Escape') setEditingId(null)
                }} />
                <button onClick={() => rename(collection.id)}><Icon name="check" size={14} /></button>
              </div>
            ) : <h2>{collection.name}</h2>}
            <p>{collection.note_count || 0} note{collection.note_count === 1 ? '' : 's'}</p>
            <Link to={`/notes?collection=${collection.id}`}>Open collection <span>→</span></Link>
          </article>
        ))}
        {!collections.length && <div className="empty-state panel management-empty"><span className="empty-state__icon"><Icon name="folder" size={28} /></span><h2>No collections yet</h2><p>Create a flat collection above.</p></div>}
      </div>
    </AppShell>
  )
}

export default CollectionsPage
