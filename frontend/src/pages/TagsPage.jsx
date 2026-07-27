import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import { createTag, deleteTag, listTags, updateTag } from '../api'

function TagsPage() {
  const [tags, setTags] = useState([])
  const [newTag, setNewTag] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    listTags().then(setTags).catch((err) => setError(err.message))
  }, [])

  async function handleCreate(event) {
    event.preventDefault()
    if (!newTag.trim()) return
    setError('')
    try {
      const tag = await createTag(newTag)
      setTags((current) => {
        const exists = current.some((item) => item.id === tag.id)
        return exists ? current : [...current, tag].sort((a, b) => a.name.localeCompare(b.name))
      })
      setNewTag('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveRename(tagId) {
    if (!editingName.trim()) return
    try {
      const updated = await updateTag(tagId, editingName)
      setTags((current) => current.map((tag) => tag.id === tagId ? updated : tag).sort((a, b) => a.name.localeCompare(b.name)))
      setEditingId(null)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(tag) {
    if (!window.confirm(`Delete the “${tag.name}” tag? Notes will be kept.`)) return
    try {
      await deleteTag(tag.id)
      setTags((current) => current.filter((item) => item.id !== tag.id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AppShell title="Tags Management" subtitle="Organize notes across topics">
      <section className="management-toolbar panel">
        <div>
          <span className="section-eyebrow">Tags</span>
          <strong>{tags.length}</strong>
        </div>
        <form onSubmit={handleCreate}>
          <input value={newTag} onChange={(event) => setNewTag(event.target.value)} placeholder="New tag name" maxLength={30} />
          <button className="primary-button" type="submit"><Icon name="plus" size={15} /> Add tag</button>
        </form>
      </section>

      {error && <div className="alert alert--error">{error}</div>}

      <div className="management-grid">
        {tags.map((tag, index) => (
          <article className={`management-card ${index === 0 ? 'is-featured' : ''}`} key={tag.id}>
            <div className="management-card__top">
              <span className="management-icon"><Icon name="tag" size={16} /></span>
              <div className="management-actions">
                <button onClick={() => { setEditingId(tag.id); setEditingName(tag.name) }} title="Rename"><Icon name="edit" size={14} /></button>
                <button onClick={() => handleDelete(tag)} title="Delete"><Icon name="trash" size={14} /></button>
              </div>
            </div>
            {editingId === tag.id ? (
              <div className="inline-edit">
                <input autoFocus value={editingName} onChange={(event) => setEditingName(event.target.value)} onKeyDown={(event) => {
                  if (event.key === 'Enter') saveRename(tag.id)
                  if (event.key === 'Escape') setEditingId(null)
                }} />
                <button onClick={() => saveRename(tag.id)}><Icon name="check" size={14} /></button>
              </div>
            ) : <h2>{tag.name}</h2>}
            <p>{tag.note_count || 0} note{tag.note_count === 1 ? '' : 's'}</p>
            <Link to={`/notes?tag=${encodeURIComponent(tag.name)}`}>View notes <span>→</span></Link>
          </article>
        ))}
        {!tags.length && (
          <div className="empty-state panel management-empty">
            <span className="empty-state__icon"><Icon name="tag" size={28} /></span>
            <h2>No tags yet</h2>
            <p>Add your first tag above.</p>
          </div>
        )}
      </div>
    </AppShell>
  )
}

export default TagsPage
