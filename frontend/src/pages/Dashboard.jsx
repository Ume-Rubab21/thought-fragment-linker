import { useEffect, useId, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import {
  clearDashboardSummaryCache,
  createNote,
  getDashboardSummary,
} from '../api'
import { shortText } from '../utils/richText'

function MetricCard({ label, value, icon, trend, points, gradientId }) {
  return (
    <article className="metric-card metric-card--enhanced">
      <div className="metric-card__heading">
        <span className="metric-card__icon"><Icon name={icon} size={17} /></span>
        <span>{label}</span>
        <span className="metric-card__info">i</span>
      </div>
      <strong>{value}</strong>
      <span className="metric-card__trend">↑ {trend}</span>
      <MiniAreaChart points={points} gradientId={gradientId} />
    </article>
  )
}

function MiniAreaChart({ points, gradientId }) {
  const first = points.split(' ')[0].split(',')[0]
  const last = points.split(' ').at(-1).split(',')[0]
  const areaPoints = `${first},28 ${points} ${last},28`

  return (
    <svg className="mini-sparkline mini-sparkline--filled" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#75b27f" stopOpacity="0.72" />
          <stop offset="100%" stopColor="#dfeedd" stopOpacity="0.1" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradientId})`} />
      <polyline points={points} fill="none" vectorEffect="non-scaling-stroke" />
      {points.split(' ').map((point) => {
        const [cx, cy] = point.split(',')
        return <circle key={point} cx={cx} cy={cy} r="1.15" />
      })}
    </svg>
  )
}

const EMPTY_SUMMARY = {
  note_count: 0,
  tag_count: 0,
  collection_count: 0,
  connection_count: 0,
  recent_notes: [],
  top_tags: [],
}

function Dashboard() {
  const [summary, setSummary] = useState(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const idPrefix = useId().replace(/:/g, '')

  useEffect(() => {
    let cancelled = false

    getDashboardSummary()
      .then((data) => {
        if (!cancelled) setSummary({ ...EMPTY_SUMMARY, ...data })
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  async function createNewNote() {
    try {
      const note = await createNote('Untitled note', '<p></p>')
      clearDashboardSummaryCache()
      navigate(`/notes/${note.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  const recentNotes = summary.recent_notes || []
  const tagRanking = summary.top_tags || []

  return (
    <AppShell
      title="Dashboard"
      titleVariant="dashboard"
      subtitle="Your knowledge, organized and connected."
      contentClassName="dashboard-page"
      actions={
        <button className="primary-button header-primary" onClick={createNewNote}>
          <Icon name="plus" size={16} /> New note
        </button>
      }
    >
      {error && <div className="alert alert--error">{error}</div>}

      <section className="dashboard-metrics">
        <MetricCard
          label="Note statistics"
          value={loading ? '—' : summary.note_count}
          icon="notes"
          trend="12 this week"
          points="0,23 18,17 34,18 53,11 72,16 90,7 100,11"
          gradientId={`${idPrefix}-notes`}
        />
        <MetricCard
          label="Tags statistics"
          value={loading ? '—' : summary.tag_count}
          icon="tag"
          trend="8 this week"
          points="0,22 18,13 36,8 56,16 72,7 87,2 100,6"
          gradientId={`${idPrefix}-tags`}
        />
        <MetricCard
          label="Connections statistics"
          value={loading ? '—' : summary.connection_count}
          icon="link"
          trend="5 this week"
          points="0,22 18,16 35,9 55,14 73,5 88,8 100,10"
          gradientId={`${idPrefix}-connections`}
        />

        <article className="metric-card metric-card--ranking metric-card--enhanced">
          <div className="metric-card__heading">
            <span className="metric-card__icon"><Icon name="dashboard" size={17} /></span>
            <span>Top tags</span>
          </div>
          <div className="ranking-list ranking-list--named">
            {(tagRanking.length ? tagRanking : [{ name: 'No tags yet', note_count: 0 }]).slice(0, 5).map((tag, index) => (
              <div className="ranking-row" key={tag.id || tag.name}>
                <span>{index + 1}</span>
                <strong>{tag.name}</strong>
                <i><b style={{ width: `${Math.max(10, Math.min(100, (tag.note_count || 0) * 17))}%` }} /></i>
                <small>{tag.note_count || 0}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="dashboard-grid dashboard-grid--enhanced">
        <article className="panel recent-panel">
          <div className="panel__header">
            <h2>Recent activity</h2>
            <Link to="/notes">View all</Link>
          </div>
          {loading ? (
            <div className="skeleton-list"><span /><span /><span /></div>
          ) : recentNotes.length ? (
            <>
              <div className="activity-list">
                {recentNotes.slice(0, 5).map((note, index) => (
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
              <Link className="activity-view-all" to="/notes">View all activity <span>→</span></Link>
            </>
          ) : (
            <div className="empty-state compact-empty">Create your first note to start building your knowledge base.</div>
          )}
        </article>

        <article className="panel knowledge-gap-card">
          <div className="panel__header"><h2>Knowledge gap</h2></div>
          <div className="knowledge-gap-card__body">
            <div className="knowledge-gap-orbit" aria-hidden="true">
              <span className="knowledge-gap-question knowledge-gap-question--one">?</span>
              <span className="knowledge-gap-question knowledge-gap-question--two">?</span>
              <span className="knowledge-gap-question knowledge-gap-question--three">?</span>
              <span className="knowledge-gap-question knowledge-gap-question--four">?</span>
              <span className="knowledge-gap-brain"><Icon name="brain" size={48} /></span>
            </div>
            <strong>{summary.tag_count ? 'Keep connecting your ideas' : 'Build your first topic cluster'}</strong>
            <p>{summary.tag_count ? `You have ${summary.tag_count} tags across ${summary.note_count} notes.` : 'Add tags and collections to make your notes easier to find.'}</p>
            <Link className="knowledge-gap-action" to="/ai-suggestions"><Icon name="sparkles" size={14} /> Explore suggestions</Link>
          </div>
        </article>

        <article className="panel graph-preview">
          <div className="panel__header">
            <h2>Knowledge graph</h2>
            <Link className="coming-soon" to="/knowledge-graph">Open graph</Link>
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
            <text x="265" y="165" textAnchor="middle">Collections</text>
          </svg>
        </article>
      </section>

      <section className="collection-strip collection-strip--enhanced">
        <div>
          <span className="section-eyebrow">Collections</span>
          <strong>{loading ? '—' : summary.collection_count}</strong>
          <small>Total collections</small>
        </div>
        <p>Use flat collections for broad grouping, and tags for flexible cross-linking.</p>
        <Link className="secondary-button" to="/collections">Manage collections</Link>
      </section>

      <footer className="dashboard-quote" aria-label="ThoughtLinker motto">
        <span>✦</span><b>“</b> Capture ideas. Connect knowledge. Grow smarter. <b>”</b><span>✦</span>
      </footer>
    </AppShell>
  )
}

export default Dashboard
