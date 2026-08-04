import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  acceptBrainDumpSuggestion,
  getAISuggestion,
  listAISuggestions,
  rejectBrainDumpSuggestion,
} from '../api'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import './AISuggestions.css'
import { readInstantCache, writeInstantCache } from '../utils/instantCache'



const FILTERS = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'rejected', label: 'Rejected' },
]

function splitTags(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function StatusPill({ status }) {
  return (
    <span className={`suggestion-status suggestion-status--${status}`}>
      {status}
    </span>
  )
}

export default function AISuggestions() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('')
  const initialSuggestionData = readInstantCache('suggestions:all', null)
  const [data, setData] = useState(initialSuggestionData || {
    items: [], total: 0, pending: 0, accepted: 0, rejected: 0,
  })
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(!initialSuggestionData)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [relatedNotesOpen, setRelatedNotesOpen] = useState(false)
  const [selectedRelatedNoteIds, setSelectedRelatedNoteIds] = useState([])
  const listRequestIdRef = useRef(0)

  const counts = useMemo(() => ({
    all: data.total,
    pending: data.pending,
    accepted: data.accepted,
    rejected: data.rejected,
  }), [data])

  async function loadList(nextFilter = filter, options = {}) {
    const requestId = listRequestIdRef.current + 1
    listRequestIdRef.current = requestId
    const cacheKey = `suggestions:${nextFilter || 'all'}`
    const cached = readInstantCache(cacheKey, null)

    if (cached) {
      setData(cached)
      setLoading(false)
    } else if (!options.background) {
      setLoading(true)
    }

    setError('')
    setNotice('')

    try {
      const response = await listAISuggestions(nextFilter || null)
      if (requestId !== listRequestIdRef.current) return

      setData(response)
      writeInstantCache(cacheKey, response)
      if (!nextFilter) writeInstantCache('suggestions:all', response)

      if (selected) {
        const updated = response.items.find(
          (item) => item.suggestion_id === selected.suggestion_id,
        )
        if (!updated && nextFilter) setSelected(null)
      }
    } catch (requestError) {
      if (requestId !== listRequestIdRef.current) return
      // Cached suggestions remain usable while Railway wakes up.
      if (!cached) {
        setError(
          requestError?.message || 'Unable to load AI suggestions.',
        )
      }
    } finally {
      if (requestId === listRequestIdRef.current) setLoading(false)
    }
  }

  useEffect(() => {
    loadList(filter)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  function applySuggestion(response) {
    setSelected(response)
    setTitle(response.suggested_title || '')
    setBody(response.suggested_content || response.brain_dump_text || response.summary || '')
    setTagInput((response.tags || []).join(', '))
    setRejectionReason(response.rejection_reason || '')
    const availableRelatedIds = (response.related_notes || []).map(
      (note) => note.note_id,
    )
    setSelectedRelatedNoteIds(availableRelatedIds)
    setRelatedNotesOpen(true)
  }

  async function openSuggestion(id) {
    setError('')
    setNotice('')

    const detailKey = `suggestion-detail:${id}`
    const cachedDetail = readInstantCache(detailKey, null)
    const listItem = data.items.find((item) => item.suggestion_id === id)

    // Open immediately using cached detail or data already present in the list.
    if (cachedDetail) {
      applySuggestion(cachedDetail)
      setDetailsLoading(false)
    } else if (listItem) {
      applySuggestion({
        ...listItem,
        suggested_content: listItem.summary || '',
        brain_dump_text: '',
        related_notes: [],
        keywords: listItem.keywords || [],
      })
      setDetailsLoading(false)
    } else {
      setDetailsLoading(true)
    }

    try {
      const response = await getAISuggestion(id)
      applySuggestion(response)
      writeInstantCache(detailKey, response)
    } catch (requestError) {
      if (!cachedDetail && !listItem) {
        setError(requestError.message || 'Unable to load suggestion details.')
      }
    } finally {
      setDetailsLoading(false)
    }
  }

  async function acceptSelected() {
    if (!selected || selected.status !== 'pending' || saving) return
    if (!title.trim()) {
      setError('The note title cannot be empty.')
      return
    }
    const confirmed = window.confirm(
      'Accept this suggestion and create a permanent note?',
    )
    if (!confirmed) return

    setSaving(true)
    setError('')
    try {
      const response = await acceptBrainDumpSuggestion(
        selected.brain_dump_id,
        {
          title: title.trim(),
          body_md: body,
          tags: splitTags(tagInput),
          selected_related_note_ids: selectedRelatedNoteIds,
        },
      )
      setNotice(response.message || 'Suggestion accepted successfully.')
      await loadList(filter)
      await openSuggestion(selected.suggestion_id)
    } catch (requestError) {
      setError(requestError.message || 'Unable to accept suggestion.')
    } finally {
      setSaving(false)
    }
  }

  async function rejectSelected() {
    if (!selected || selected.status !== 'pending' || saving) return
    const confirmed = window.confirm(
      'Reject this suggestion? No note will be created.',
    )
    if (!confirmed) return

    setSaving(true)
    setError('')
    try {
      const response = await rejectBrainDumpSuggestion(
        selected.brain_dump_id,
        rejectionReason,
      )
      setNotice(response.message || 'Suggestion rejected.')
      await loadList(filter)
      await openSuggestion(selected.suggestion_id)
    } catch (requestError) {
      setError(requestError.message || 'Unable to reject suggestion.')
    } finally {
      setSaving(false)
    }
  }


  function toggleRelatedNote(noteId) {
    if (!selected || selected.status !== 'pending') return
    setSelectedRelatedNoteIds((current) => (
      current.includes(noteId)
        ? current.filter((value) => value !== noteId)
        : [...current, noteId]
    ))
  }

  return (
    <AppShell
      title="AI Suggestions"
      subtitle="Review, edit, accept, or reject every AI-generated suggestion."
      contentClassName="suggestions-page"
      actions={(
        <button
          type="button"
          className="suggestions-refresh"
          onClick={() => loadList(filter)}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      )}
    >
      {(error || notice) && (
        <div className={`suggestions-message ${error ? 'is-error' : 'is-success'}`}>
          {error || notice}
          <button type="button" onClick={() => { setError(''); setNotice('') }}>
            <Icon name="close" size={15} />
          </button>
        </div>
      )}

      <section className="suggestions-summary">
        {[
          ['All suggestions', counts.all],
          ['Pending review', counts.pending],
          ['Accepted', counts.accepted],
          ['Rejected', counts.rejected],
        ].map(([label, value]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <div className="suggestions-toolbar">
        <div className="suggestions-filters" role="tablist" aria-label="Suggestion status filters">
          {FILTERS.map((item) => (
            <button
              key={item.value || 'all'}
              type="button"
              className={filter === item.value ? 'is-active' : ''}
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="suggestions-layout">
        <section className="suggestions-list-card">
          {loading ? (
            <div className="suggestions-empty">Loading suggestions…</div>
          ) : data.items.length === 0 ? (
            <div className="suggestions-empty">
              <div className="suggestions-empty__icon">✨</div>
              <h2>No suggestions found</h2>
              <p>Create a Brain Dump to generate a new AI suggestion.</p>
              <button type="button" onClick={() => navigate('/brain-dump')}>
                Open Brain Dump
              </button>
            </div>
          ) : (
            <div className="suggestions-list">
              {data.items.map((item) => (
                <button
                  type="button"
                  key={item.suggestion_id}
                  className={`suggestion-row ${selected?.suggestion_id === item.suggestion_id ? 'is-selected' : ''}`}
                  onClick={() => openSuggestion(item.suggestion_id)}
                >
                  <div className="suggestion-row__top">
                    <h3>{item.suggested_title}</h3>
                    <div className="suggestion-row__badges">
                      {item.reasoning_tier === 'large' && (
                        <span className="reasoning-tier-badge">AI Reasoned</span>
                      )}
                      <StatusPill status={item.status} />
                    </div>
                  </div>
                  <p>{item.summary}</p>
                  <div className="suggestion-row__tags">
                    {(item.tags || []).slice(0, 3).map((tag) => (
                      <span key={tag}>#{tag}</span>
                    ))}
                  </div>
                  <footer>
                    <span>{formatDate(item.created_at)}</span>
                    <span>{item.model_name}</span>
                  </footer>
                </button>
              ))}
            </div>
          )}
        </section>

        <aside className="suggestion-detail-card">
          {detailsLoading ? (
            <div className="suggestions-empty">Loading details…</div>
          ) : !selected ? (
            <div className="suggestions-empty">
              <div className="suggestions-empty__icon">🧠</div>
              <h2>Select a suggestion</h2>
              <p>Choose an item to review its title, content, tags, keywords, and decision history.</p>
            </div>
          ) : (
            <div className="suggestion-detail">
              <div className="suggestion-detail__header">
                <div>
                  <span className="suggestion-detail__eyebrow">Suggestion details</span>
                  <h2>{selected.suggested_title}</h2>
                </div>
                <StatusPill status={selected.status} />
              </div>

              <label>
                <span>Note title</span>
                <input
                  value={title}
                  disabled={selected.status !== 'pending'}
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>

              <label>
                <span>Note content</span>
                <textarea
                  rows={8}
                  value={body}
                  disabled={selected.status !== 'pending'}
                  onChange={(event) => setBody(event.target.value)}
                />
              </label>

              <label>
                <span>Tags <small>comma separated</small></span>
                <input
                  value={tagInput}
                  disabled={selected.status !== 'pending'}
                  onChange={(event) => setTagInput(event.target.value)}
                />
              </label>

              <div className="suggestion-detail__section">
                <span>AI summary</span>
                <p>{selected.summary}</p>
              </div>

              <div className="suggestion-detail__section">
                <span>Keywords</span>
                <div className="suggestion-keywords">
                  {(selected.keywords || []).map((keyword) => (
                    <em key={keyword}>{keyword}</em>
                  ))}
                </div>
              </div>

              {selected.reasoning_tier === 'large' && selected.reasoning && (
                <section className="reasoning-card">
                  <div className="reasoning-card__header">
                    <div>
                      <span>Large-model reasoning</span>
                      <strong>Why did AI suggest this?</strong>
                    </div>
                    <div className="confidence-badge" title="Model-reported confidence">
                      {selected.confidence_score ?? 0}% confidence
                    </div>
                  </div>
                  <p>{selected.reasoning}</p>
                  <footer>
                    Decision: <strong>{
                      selected.reasoning_decision === 'extend_existing'
                        ? 'Extend an existing note'
                        : selected.reasoning_decision === 'new_note'
                          ? 'Create a new note'
                          : 'Needs user judgment'
                    }</strong>
                  </footer>
                </section>
              )}

              <div className="suggestion-detail__meta">
                <div><span>Model</span><strong>{selected.model_name}</strong></div>
                <div><span>Tier</span><strong>{selected.reasoning_tier === 'large' ? 'Large reasoning' : 'Small metadata'}</strong></div>
                <div><span>Total tokens</span><strong>{selected.total_tokens}</strong></div>
                <div><span>Related notes</span><strong>{selected.related_notes?.length || 0}</strong></div>
                <div><span>Created</span><strong>{formatDate(selected.created_at)}</strong></div>
              </div>

              <section className="related-notes-review">
                <button
                  type="button"
                  className="related-notes-review__toggle"
                  onClick={() => setRelatedNotesOpen((current) => !current)}
                  aria-expanded={relatedNotesOpen}
                >
                  <span>
                    <strong>Related notes ({selected.related_notes?.length || 0})</strong>
                    <small>
                      {selected.status === 'pending'
                        ? `${selectedRelatedNoteIds.length} of ${selected.related_notes?.length || 0} selected`
                        : `${selected.related_notes?.length || 0} suggested notes`}
                    </small>
                  </span>
                  <span className={`related-notes-review__chevron ${relatedNotesOpen ? 'is-open' : ''}`}>⌄</span>
                </button>

                {relatedNotesOpen && (
                  <div className="related-notes-review__list">
                    {(selected.related_notes || []).length === 0 ? (
                      <p className="related-notes-review__empty">
                        No valid related notes were found. They may have been deleted.
                      </p>
                    ) : (
                      (selected.related_notes || []).map((note) => {
                        const checked = selectedRelatedNoteIds.includes(note.note_id)
                        return (
                          <article
                            key={note.note_id}
                            className={`related-note-option ${checked ? 'is-selected' : ''}`}
                          >
                            <label>
                              <input
                                type="checkbox"
                                checked={checked}
                                disabled={selected.status !== 'pending'}
                                onChange={() => toggleRelatedNote(note.note_id)}
                              />
                              <span className="related-note-option__content">
                                <button
                                  type="button"
                                  className="related-note-option__title"
                                  onClick={(event) => {
                                    event.preventDefault()
                                    event.stopPropagation()
                                    navigate(`/notes/${note.note_id}`)
                                  }}
                                  title={`Open ${note.title}`}
                                >
                                  {note.title}
                                </button>
                                <small>{note.preview || 'This note has no content preview.'}</small>
                              </span>
                            </label>
                            <div className="related-note-option__actions">
                              <div
                                className={`match-meter ${
                                  note.similarity_percentage >= 90
                                    ? 'is-excellent'
                                    : note.similarity_percentage >= 70
                                      ? 'is-good'
                                      : 'is-weak'
                                }`}
                                title={`Cosine similarity: ${(note.similarity_score || 0).toFixed(3)}`}
                              >
                                <span className="match-meter__label">Match</span>
                                <strong className="match-meter__value">{note.similarity_percentage ?? 0}%</strong>
                                <span className="match-meter__track" aria-hidden="true">
                                  <span
                                    className="match-meter__fill"
                                    style={{ width: `${Math.max(0, Math.min(100, note.similarity_percentage ?? 0))}%` }}
                                  />
                                </span>
                              </div>
                              <button
                                type="button"
                                className="related-note-option__open"
                                aria-label={`Open ${note.title}`}
                                title="Open note"
                                onClick={() => navigate(`/notes/${note.note_id}`)}
                              >
                                ↗
                              </button>
                            </div>
                          </article>
                        )
                      })
                    )}
                    {selected.status === 'pending' && (selected.related_notes || []).length > 0 && (
                      <div className="related-notes-review__controls">
                        <button
                          type="button"
                          onClick={() => setSelectedRelatedNoteIds(
                            (selected.related_notes || []).map((note) => note.note_id),
                          )}
                        >
                          Select all
                        </button>
                        <button type="button" onClick={() => setSelectedRelatedNoteIds([])}>
                          Clear all
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </section>

              {selected.status === 'pending' ? (
                <>
                  <label>
                    <span>Optional rejection reason</span>
                    <input
                      value={rejectionReason}
                      maxLength={500}
                      placeholder="Why is this suggestion not useful?"
                      onChange={(event) => setRejectionReason(event.target.value)}
                    />
                  </label>
                  <div className="suggestion-detail__actions">
                    <button
                      type="button"
                      className="suggestion-button suggestion-button--reject"
                      disabled={saving}
                      onClick={rejectSelected}
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      className="suggestion-button suggestion-button--accept"
                      disabled={saving}
                      onClick={acceptSelected}
                    >
                      {saving ? 'Saving…' : `Accept & create note (${selectedRelatedNoteIds.length} ${selectedRelatedNoteIds.length === 1 ? 'link' : 'links'})`}
                    </button>
                  </div>
                </>
              ) : (
                <div className="suggestion-decision-box">
                  <strong>This suggestion was {selected.status}.</strong>
                  {selected.rejection_reason && <p>Reason: {selected.rejection_reason}</p>}
                  {selected.accepted_note_id && (
                    <button type="button" onClick={() => navigate(`/notes/${selected.accepted_note_id}`)}>
                      Open created note
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </AppShell>
  )
}
