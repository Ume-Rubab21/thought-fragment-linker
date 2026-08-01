import {
  useEffect,
  useState,
} from 'react'
import { useNavigate } from 'react-router-dom'

import {
  acceptBrainDumpSuggestion,
  createNote,
  clearDashboardSummaryCache,
  getBrainDumpGaps,
  getModelCallDashboard,
  inspectBrainDumpGraph,
  getBrainDumpStatus,
  getBrainDumpSuggestion,
  rejectBrainDumpSuggestion,
  submitBrainDump,
} from '../api'
import AppShell from '../components/AppShell'
import './BrainDump.css'


const POLLING_INTERVAL_MS = 1200


function normalizeTagInput(value) {
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}


function StatusBadge({ status }) {
  const labelMap = {
    queued: 'Queued',
    processing: 'Processing',
    ready: 'Ready for review',
    failed: 'Failed',
  }

  return (
    <span
      className={`brain-dump-status brain-dump-status--${
        status || 'idle'
      }`}
    >
      <span className="brain-dump-status__dot" />

      {labelMap[status] || 'Not started'}
    </span>
  )
}


function formatGraphNode(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}


function RoutingSnapshot({ dashboard }) {
  const summary = dashboard?.summary

  if (!summary) {
    return (
      <div className="brain-dump-mini-empty">
        Routing analytics will appear after the first model call.
      </div>
    )
  }

  return (
    <>
      <div className="brain-dump-routing-metrics">
        <div><span>Total calls</span><strong>{summary.total_calls || 0}</strong></div>
        <div><span>Large model</span><strong>{summary.large_model_calls || 0}</strong></div>
        <div><span>Small model</span><strong>{summary.small_model_calls || 0}</strong></div>
        <div><span>Successful</span><strong>{summary.successful_calls || 0}</strong></div>
      </div>

      {(dashboard.recent_calls || []).slice(0, 3).length > 0 && (
        <div className="brain-dump-routing-history">
          <div className="brain-dump-routing-history__head">
            <span>Recent route</span><span>Status</span>
          </div>

          {(dashboard.recent_calls || []).slice(0, 3).map((call) => (
            <div
              className="brain-dump-routing-history__row"
              key={call.id || `${call.model_name}-${call.created_at}`}
            >
              <div>
                <strong>
                  {String(call.routing_decision || '')
                    .replace(/-/g, ' ')
                    .replace(/\b\w/g, (character) => character.toUpperCase())}
                </strong>
                <small>{call.model_name}</small>
              </div>

              <span
                className={`brain-dump-route-status ${
                  call.success
                    ? 'brain-dump-route-status--success'
                    : 'brain-dump-route-status--failed'
                }`}
              >
                {call.success ? 'Success' : 'Failed'}
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}


function WorkflowGraph({ graphInfo }) {
  const nodes =
    graphInfo?.nodes?.length
      ? graphInfo.nodes
      : [
          'load',
          'mark_processing',
          'normalize',
          'route_and_generate',
          'detect_gaps',
          'mark_ready',
        ]

  return (
    <section className="brain-dump-workflow">
      <div className="brain-dump-workflow__header">
        <div>
          <span className="brain-dump-eyebrow">Inspectable workflow</span>
          <h2>Brain Dump processing graph</h2>
          <p>
            Each step is separated so the pipeline is easier to inspect,
            test, and debug.
          </p>
        </div>

        <span className="brain-dump-engine-badge">
          <span />
          {graphInfo?.engine === 'langgraph'
            ? 'LangGraph active'
            : 'Pipeline fallback'}
        </span>
      </div>

      <div className="brain-dump-workflow__track">
        <div className="brain-dump-workflow__terminal">Start</div>

        {nodes.map((node, index) => (
          <div className="brain-dump-workflow__segment" key={node}>
            <span className="brain-dump-workflow__arrow">→</span>
            <article className="brain-dump-workflow__node">
              <small>Step {index + 1}</small>
              <strong>{formatGraphNode(node)}</strong>
            </article>
          </div>
        ))}

        <span className="brain-dump-workflow__arrow">→</span>
        <div className="brain-dump-workflow__terminal">End</div>
      </div>
    </section>
  )
}


export default function BrainDump() {
  const navigate = useNavigate()

  const [text, setText] = useState('')
  const [brainDumpId, setBrainDumpId] =
    useState(null)
  const [status, setStatus] = useState(null)

  const [suggestion, setSuggestion] =
    useState(null)

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tagInput, setTagInput] =
    useState('')

  const [rejectionReason, setRejectionReason] =
    useState('')

  const [submitting, setSubmitting] =
    useState(false)
  const [deciding, setDeciding] =
    useState(false)

  const [error, setError] = useState('')
  const [generationFailed, setGenerationFailed] = useState(false)
  const [success, setSuccess] =
    useState(null)
  const [knowledgeGaps, setKnowledgeGaps] =
    useState([])
  const [routingDashboard, setRoutingDashboard] =
    useState(null)
  const [graphInfo, setGraphInfo] = useState(null)


  useEffect(() => {
    let active = true

    Promise.allSettled([
      getModelCallDashboard(3),
      inspectBrainDumpGraph(),
    ]).then(([routingResult, graphResult]) => {
      if (!active) return

      if (routingResult.status === 'fulfilled') {
        setRoutingDashboard(routingResult.value)
      }

      if (graphResult.status === 'fulfilled') {
        setGraphInfo(graphResult.value)
      }
    })

    return () => {
      active = false
    }
  }, [])


  async function loadSuggestion(id) {
    const response =
      await getBrainDumpSuggestion(id)

    setSuggestion(response)
    setTitle(response.suggested_title || '')
    setBody(text.trim())
    setTagInput(
      (response.tags || []).join(', '),
    )

    try {
      const gapResponse = await getBrainDumpGaps(id)
      setKnowledgeGaps(gapResponse.gaps || [])

      getModelCallDashboard(3)
        .then(setRoutingDashboard)
        .catch(() => undefined)
    } catch (gapError) {
      console.warn('Knowledge-gap detection unavailable:', gapError)
      setKnowledgeGaps([])
    }
  }


  async function handleSubmit(event) {
    event.preventDefault()

    const cleanedText = text.trim()

    if (cleanedText.length < 3) {
      setError(
        'Please enter at least 3 characters.',
      )
      return
    }

    setSubmitting(true)
    setError('')
    setSuccess(null)
    setSuggestion(null)
    setBrainDumpId(null)
    setStatus(null)
    setGenerationFailed(false)
    setKnowledgeGaps([])

    try {
      const response =
        await submitBrainDump(cleanedText)

      setBrainDumpId(response.id)
      setStatus(response.status)
    } catch (requestError) {
      setError(
        requestError.message ||
          'Unable to submit the Brain Dump.',
      )
      setSubmitting(false)
    }
  }


  useEffect(() => {
    if (!brainDumpId) {
      return undefined
    }

    let cancelled = false
    let timerId = null

    async function poll() {
      try {
        const response =
          await getBrainDumpStatus(
            brainDumpId,
          )

        if (cancelled) {
          return
        }

        setStatus(response.status)

        if (response.status === 'ready') {
          await loadSuggestion(brainDumpId)

          if (!cancelled) {
            setSubmitting(false)
          }

          return
        }

        if (response.status === 'failed') {
          // Keep technical provider/validation details out of the normal UI.
          // The original text can still be saved as a regular note.
          if (response.error_message) {
            console.warn('Brain Dump generation failed:', response.error_message)
          }
          setError('')
          setGenerationFailed(true)
          setSubmitting(false)
          return
        }

        timerId = window.setTimeout(
          poll,
          POLLING_INTERVAL_MS,
        )
      } catch (requestError) {
        if (!cancelled) {
          setError(
            requestError.message ||
              'Unable to check processing status.',
          )
          setSubmitting(false)
        }
      }
    }

    poll()

    return () => {
      cancelled = true

      if (timerId) {
        window.clearTimeout(timerId)
      }
    }
  }, [brainDumpId])


  async function handleAccept() {
    if (!brainDumpId || deciding) {
      return
    }

    const cleanedTitle = title.trim()

    if (!cleanedTitle) {
      setError(
        'The note title cannot be empty.',
      )
      return
    }

    setDeciding(true)
    setError('')

    try {
      const response =
        await acceptBrainDumpSuggestion(
          brainDumpId,
          {
            title: cleanedTitle,
            body_md: body,
            tags:
              normalizeTagInput(tagInput),
          },
        )

      setSuccess(response)

      if (response.note_id) {
        window.setTimeout(() => {
          navigate(
            `/notes/${response.note_id}`,
          )
        }, 900)
      }
    } catch (requestError) {
      setError(
        requestError.message ||
          'Unable to accept the suggestion.',
      )
    } finally {
      setDeciding(false)
    }
  }


  async function handleReject() {
    if (!brainDumpId || deciding) {
      return
    }

    const confirmed = window.confirm(
      'Reject this AI suggestion? No note will be created.',
    )

    if (!confirmed) {
      return
    }

    setDeciding(true)
    setError('')

    try {
      const response =
        await rejectBrainDumpSuggestion(
          brainDumpId,
          rejectionReason,
        )

      setSuccess(response)
    } catch (requestError) {
      setError(
        requestError.message ||
          'Unable to reject the suggestion.',
      )
    } finally {
      setDeciding(false)
    }
  }


  function buildFallbackTitle(value) {
    const firstLine = value
      .trim()
      .split(/\n+/)[0]
      .replace(/\s+/g, ' ')
      .trim()

    if (!firstLine) return 'Untitled Brain Dump'
    return firstLine.length > 90
      ? `${firstLine.slice(0, 87)}...`
      : firstLine
  }


  function plainTextToRichText(value) {
    const escapeHtml = (part) => part
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')

    return value
      .trim()
      .split(/\n{2,}/)
      .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, '<br>')}</p>`)
      .join('')
  }


  async function handleSaveOriginalNote() {
    const cleanedText = text.trim()
    if (!cleanedText || deciding) return

    setDeciding(true)
    setError('')

    try {
      const note = await createNote(
        buildFallbackTitle(cleanedText),
        plainTextToRichText(cleanedText),
      )
      clearDashboardSummaryCache()
      setSuccess({
        decision: 'accepted',
        note_id: note.id,
        message: 'Original text saved as a normal note.',
      })
      window.setTimeout(() => navigate(`/notes/${note.id}`), 700)
    } catch (requestError) {
      setError(requestError.message || 'Unable to save the original note.')
    } finally {
      setDeciding(false)
    }
  }


  function handleCancelFailure() {
    setBrainDumpId(null)
    setStatus(null)
    setSuggestion(null)
    setGenerationFailed(false)
    setError('')
    setSubmitting(false)
    // Deliberately retain the text so the user can edit and try again.
  }


  function resetPage() {
    setText('')
    setBrainDumpId(null)
    setStatus(null)
    setSuggestion(null)
    setTitle('')
    setBody('')
    setTagInput('')
    setRejectionReason('')
    setSubmitting(false)
    setDeciding(false)
    setError('')
    setSuccess(null)
    setGenerationFailed(false)
    setKnowledgeGaps([])
  }


  return (
    <AppShell
      title="Brain Dump"
      subtitle={
        'Capture an unstructured thought and review the AI suggestion before saving it.'
      }
      contentClassName="brain-dump-page"
    >
      <div className="brain-dump-grid">
        <section className="brain-dump-card brain-dump-compose">
          <div className="brain-dump-card__header">
            <div>
              <span className="brain-dump-eyebrow">
                Quick capture
              </span>

              <h2>What is on your mind?</h2>

              <p>
                Write freely. ThoughtLinker will
                suggest a title, summary, tags, and
                keywords for your review.
              </p>
            </div>

            <StatusBadge status={status} />
          </div>

          <form onSubmit={handleSubmit}>
            <textarea
              className="brain-dump-textarea"
              rows={13}
              value={text}
              disabled={
                submitting ||
                Boolean(suggestion) ||
                Boolean(success)
              }
              placeholder={
                'Example: I want to build semantic search using PostgreSQL, pgvector, and MiniLM embeddings...'
              }
              onChange={(event) =>
                setText(event.target.value)
              }
            />

            <div className="brain-dump-compose__footer">
              <span>
                {text.length.toLocaleString()}
                {' / '}
                20,000 characters
              </span>

              <button
                type="submit"
                className="brain-dump-button brain-dump-button--primary"
                disabled={
                  submitting ||
                  text.trim().length < 3 ||
                  Boolean(suggestion) ||
                  Boolean(success)
                }
              >
                {submitting
                  ? 'Processing…'
                  : 'Generate suggestion'}
              </button>
            </div>
          </form>

          {submitting && (
            <div className="brain-dump-progress">
              <div className="brain-dump-progress__icon">
                <span />
                <span />
                <span />
              </div>

              <div>
                <strong>
                  ThoughtLinker is organizing your
                  thought
                </strong>

                <p>
                  Current status:{' '}
                  <b>{status || 'queued'}</b>
                </p>
              </div>
            </div>
          )}
        </section>

        <aside className="brain-dump-card brain-dump-guidance">
          <span className="brain-dump-eyebrow">
            Human in control
          </span>

          <h2>Nothing is saved automatically</h2>

          <p>
            The model only prepares a suggestion.
            You can edit every field before accepting
            it or reject it completely.
          </p>

          <div className="brain-dump-guidance__step">
            <span>1</span>

            <div>
              <strong>Capture</strong>
              <p>Write your unstructured idea.</p>
            </div>
          </div>

          <div className="brain-dump-guidance__step">
            <span>2</span>

            <div>
              <strong>Review</strong>
              <p>
                Check the generated title, tags, and
                summary.
              </p>
            </div>
          </div>

          <div className="brain-dump-guidance__step">
            <span>3</span>

            <div>
              <strong>Decide</strong>
              <p>
                Accept to create a note, or reject
                without saving one.
              </p>
            </div>
          </div>
        </aside>
      </div>

      {error && (
        <div
          className="brain-dump-alert brain-dump-alert--error"
          role="alert"
        >
          {error}
        </div>
      )}

      {generationFailed && !success && (
        <section className="brain-dump-fallback" role="status">
          <div className="brain-dump-fallback__icon">!</div>
          <div className="brain-dump-fallback__copy">
            <span className="brain-dump-eyebrow">No suggestion</span>
            <h2>No AI suggestion could be generated</h2>
            <p>
              Your original text is safe. Save it as a normal note now,
              or cancel and edit the text before trying again.
            </p>
          </div>
          <div className="brain-dump-fallback__actions">
            <button
              type="button"
              className="brain-dump-button brain-dump-button--secondary"
              disabled={deciding}
              onClick={handleCancelFailure}
            >
              Cancel
            </button>
            <button
              type="button"
              className="brain-dump-button brain-dump-button--primary"
              disabled={deciding || !text.trim()}
              onClick={handleSaveOriginalNote}
            >
              {deciding ? 'Saving…' : 'Save original note'}
            </button>
          </div>
        </section>
      )}

      {suggestion && !success && (
        <div className="brain-dump-workspace">
          <section className="brain-dump-review">
            <div className="brain-dump-review__heading">
              <div>
                <span className="brain-dump-eyebrow">
                  AI suggestion · Review before saving
                </span>
                <h2>Organized note draft</h2>
                <p>
                  Edit every field before accepting. Nothing is saved
                  automatically.
                </p>
              </div>

              <span className="brain-dump-model">
                Model: {suggestion.model_name}
              </span>
            </div>

            <div className="brain-dump-review__main brain-dump-review__main--wide">
              <label className="brain-dump-field">
                <span>Note title</span>
                <input
                  value={title}
                  maxLength={180}
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>

              <div className="brain-dump-summary-panel">
                <span>Note summary</span>
                <p>{suggestion.summary}</p>
              </div>

              <div className="brain-dump-tags-row">
                <span>Key tags</span>
                <div className="brain-dump-chips">
                  {normalizeTagInput(tagInput).map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              </div>

              <label className="brain-dump-field">
                <span>
                  AI suggested content
                  <small>Editable</small>
                </span>
                <textarea
                  rows={10}
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                />
              </label>

              <label className="brain-dump-field">
                <span>
                  Tags
                  <small>Separate tags with commas</small>
                </span>
                <input
                  value={tagInput}
                  placeholder="semantic-search, postgresql"
                  onChange={(event) => setTagInput(event.target.value)}
                />
              </label>

              <div className="brain-dump-keywords">
                <span>Keywords</span>
                <div className="brain-dump-chips">
                  {(suggestion.keywords || []).map((keyword) => (
                    <span key={keyword}>{keyword}</span>
                  ))}
                </div>
              </div>

              <label className="brain-dump-field">
                <span>
                  Rejection reason
                  <small>Optional</small>
                </span>
                <textarea
                  rows={3}
                  maxLength={500}
                  value={rejectionReason}
                  placeholder="Why is this suggestion not useful?"
                  onChange={(event) => setRejectionReason(event.target.value)}
                />
              </label>
            </div>

            <div className="brain-dump-review__actions">
              <button
                type="button"
                className="brain-dump-button brain-dump-button--danger"
                disabled={deciding}
                onClick={handleReject}
              >
                {deciding ? 'Please wait…' : 'Reject suggestion'}
              </button>

              <button
                type="button"
                className="brain-dump-button brain-dump-button--primary"
                disabled={deciding || !title.trim()}
                onClick={handleAccept}
              >
                {deciding ? 'Saving…' : 'Accept and create note'}
              </button>
            </div>
          </section>

          <aside className="brain-dump-day10-sidebar">
            <section className="brain-dump-side-panel brain-dump-gap-panel">
              <div className="brain-dump-side-panel__header">
                <div>
                  <span className="brain-dump-eyebrow">Knowledge-gap insights</span>
                  <h3>Topics you may be missing</h3>
                </div>
                <span className="brain-dump-count-badge">
                  {knowledgeGaps.length}
                </span>
              </div>

              {knowledgeGaps.length > 0 ? (
                <div className="brain-dump-gap-list brain-dump-gap-list--large">
                  {knowledgeGaps.map((gap, index) => (
                    <article key={`${gap.title}-${index}`}>
                      <div className="brain-dump-gap-icon">✦</div>
                      <div>
                        <strong>{gap.title}</strong>
                        <p>{gap.description}</p>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="brain-dump-mini-empty">
                  No important knowledge gaps were detected for this note.
                </div>
              )}
            </section>

            <section className="brain-dump-side-panel">
              <div className="brain-dump-side-panel__header">
                <div>
                  <span className="brain-dump-eyebrow">Model routing</span>
                  <h3>Live pipeline activity</h3>
                </div>
              </div>
              <RoutingSnapshot dashboard={routingDashboard} />
            </section>

            <section className="brain-dump-side-panel brain-dump-processing-panel">
              <div className="brain-dump-side-panel__header">
                <div>
                  <span className="brain-dump-eyebrow">Processing details</span>
                  <h3>Suggestion generation</h3>
                </div>
              </div>
              <dl>
                <div><dt>Attempts</dt><dd>{suggestion.attempts}</dd></div>
                <div><dt>Retries</dt><dd>{suggestion.retry_count}</dd></div>
                <div><dt>Total tokens</dt><dd>{suggestion.total_tokens}</dd></div>
              </dl>
            </section>
          </aside>
        </div>
      )}

      <WorkflowGraph graphInfo={graphInfo} />

      {success && (
        <section className="brain-dump-result">
          <div className="brain-dump-result__icon">
            {success.decision === 'accepted'
              ? '✓'
              : '×'}
          </div>

          <div>
            <span className="brain-dump-eyebrow">
              Decision saved
            </span>

            <h2>{success.message}</h2>

            <p>
              {success.decision === 'accepted'
                ? 'The note has been created. Opening the editor…'
                : 'No note was created from this suggestion.'}
            </p>
          </div>

          <button
            type="button"
            className="brain-dump-button brain-dump-button--secondary"
            onClick={resetPage}
          >
            Start another Brain Dump
          </button>
        </section>
      )}
    </AppShell>
  )
}