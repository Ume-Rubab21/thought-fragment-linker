import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import { createNote, listCollections, listNotes, listTags } from '../api'
import { shortText } from '../utils/richText'

function MetricCard({ label, value, children }) {
  return (
    <article className="metric-card">
      <div className="metric-card__heading">
        <span>{label}</span>
        <span className="metric-card__dot" />
      </div>
      <strong>{value}</strong>
      {children}
    </article>
  )
}

function MiniSparkline({ points = '0,24 20,18 40,23 60,11 80,15 100,4' }) {
  return (
    <svg className="mini-sparkline" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={points} fill="none" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function Dashboard() {
  const [notes, setNotes] = useState([])
  const [tags, setTags] = useState([])
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([listNotes(), listTags(), listCollections()])
      .then(([noteData, tagData, collectionData]) => {
        setNotes(noteData)
        setTags(tagData)
        setCollections(collectionData)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const recentNotes = notes.slice(0, 5)
  const tagRanking = useMemo(
    () => [...tags].sort((a, b) => (b.note_count || 0) - (a.note_count || 0)).slice(0, 5),
    [tags],
  )

  async function createNewNote() {
    try {
      const note = await createNote('Untitled note', '<p></p>')
      navigate(`/notes/${note.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AppShell
      title="Dashboard"
      subtitle="Back Dashboard"
      actions={
        <button className="primary-button header-primary" onClick={createNewNote}>
          <Icon name="plus" size={16} /> New note
        </button>
      }
    >
      {error && <div className="alert alert--error">{error}</div>}

      <section className="dashboard-metrics">
        <MetricCard label="Note statistics" value={loading ? '—' : notes.length}>
          <MiniSparkline points="0,22 18,17 34,20 53,13 72,17 100,6" />
        </MetricCard>
        <MetricCard label="Tags statistics" value={loading ? '—' : tags.length}>
          <MiniSparkline points="0,5 18,9 38,14 57,18 77,21 100,24" />
        </MetricCard>
        <MetricCard label="Connections statistics" value="0">
          <MiniSparkline points="0,22 16,18 33,8 48,17 63,12 78,23 100,11" />
        </MetricCard>
        <article className="metric-card metric-card--ranking">
          <div className="metric-card__heading"><span>Recent notes</span></div>
          <div className="ranking-list">
            {(tagRanking.length ? tagRanking : [{ name: 'No tags yet', note_count: 0 }]).map((tag, index) => (
              <div className="ranking-row" key={tag.id || tag.name}>
                <span>{index + 1}</span>
                <i style={{ width: `${Math.max(12, Math.min(100, (tag.note_count || 0) * 18))}%` }} />
                <small>{tag.note_count || 0}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="panel recent-panel">
          <div className="panel__header">
            <h2>Recent activity</h2>
            <Link to="/notes">View all</Link>
          </div>
          {loading ? (
            <div className="skeleton-list"><span /><span /><span /></div>
          ) : recentNotes.length ? (
            <div className="activity-list">
              {recentNotes.map((note, index) => (
                <Link to={`/notes/${note.id}`} className={index === 0 ? 'activity-row is-highlighted' : 'activity-row'} key={note.id}>
                  <span className="activity-icon"><Icon name="notes" size={15} /></span>
                  <span className="activity-copy">
                    <strong>{note.title}</strong>
                    <small>{shortText(note.body_md, 70) || 'Empty note'}</small>
                  </span>
                  <time>{new Date(note.updated_at).toLocaleDateString()}</time>
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state compact-empty">Create your first note to start building your knowledge base.</div>
          )}
        </article>

        <article className="panel knowledge-gap-card">
          <div className="panel__header"><h2>Knowledge gap</h2></div>
          <div className="knowledge-gap-card__body">
            <Icon name="brain" size={34} />
            <strong>{tags.length ? 'Keep connecting your ideas' : 'Build your first topic cluster'}</strong>
            <p>{tags.length ? `You have ${tags.length} tags across ${notes.length} notes.` : 'Add tags and collections to make your notes easier to find.'}</p>
          </div>
        </article>

        <article className="panel graph-preview">
          <div className="panel__header">
            <h2>Knowledge graph</h2>
            <span className="coming-soon">Day 5+</span>
          </div>
          <svg viewBox="0 0 320 190" aria-label="Knowledge graph preview">
            <g className="graph-lines">
              <line x1="160" y1="95" x2="55" y2="46" />
              <line x1="160" y1="95" x2="93" y2="154" />
              <line x1="160" y1="95" x2="258" y2="47" />
              <line x1="160" y1="95" x2="265" y2="142" />
              <line x1="160" y1="95" x2="160" y2="25" />
            </g>
            <g className="graph-nodes">
              <circle cx="160" cy="95" r="19" className="is-main" />
              <circle cx="55" cy="46" r="10" />
              <circle cx="93" cy="154" r="9" />
              <circle cx="258" cy="47" r="11" />
              <circle cx="265" cy="142" r="8" />
              <circle cx="160" cy="25" r="9" />
            </g>
            <text x="160" y="100" textAnchor="middle">Ideas</text>
            <text x="55" y="29" textAnchor="middle">Notes</text>
            <text x="258" y="27" textAnchor="middle">Tags</text>
            <text x="90" y="178" textAnchor="middle">Links</text>
          </svg>
        </article>
      </section>

      <section className="collection-strip">
        <div>
          <span className="section-eyebrow">Collections</span>
          <strong>{collections.length}</strong>
        </div>
        <p>Use flat collections for broad grouping, and tags for flexible cross-linking.</p>
        <Link className="secondary-button" to="/collections">Manage collections</Link>
      </section>
    </AppShell>
  )
}

export default Dashboard
