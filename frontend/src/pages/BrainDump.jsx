import {
  useEffect,
  useState,
} from 'react'
import { useNavigate } from 'react-router-dom'

import {
  acceptBrainDumpSuggestion,
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
  const [success, setSuccess] =
    useState(null)

  async function loadSuggestion(id) {
    const response =
      await getBrainDumpSuggestion(id)

    setSuggestion(response)
    setTitle(response.suggested_title || '')
    setBody(text.trim())
    setTagInput(
      (response.tags || []).join(', '),
    )
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
          setError(
            response.error_message ||
              'Brain Dump processing failed.',
          )
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

      {suggestion && !success && (
        <section className="brain-dump-review">
          <div className="brain-dump-review__heading">
            <div>
              <span className="brain-dump-eyebrow">
                AI suggestion
              </span>

              <h2>Review before saving</h2>

              <p>
                Edit the generated information below.
                Accepting creates one real note.
              </p>
            </div>

            <span className="brain-dump-model">
              {suggestion.model_name}
            </span>
          </div>

          <div className="brain-dump-review__grid">
            <div className="brain-dump-review__main">
              <label className="brain-dump-field">
                <span>Note title</span>

                <input
                  value={title}
                  maxLength={180}
                  onChange={(event) =>
                    setTitle(event.target.value)
                  }
                />
              </label>

              <label className="brain-dump-field">
                <span>Note body</span>

                <textarea
                  rows={12}
                  value={body}
                  onChange={(event) =>
                    setBody(event.target.value)
                  }
                />
              </label>

              <label className="brain-dump-field">
                <span>
                  Tags
                  <small>
                    Separate tags with commas
                  </small>
                </span>

                <input
                  value={tagInput}
                  placeholder={
                    'semantic-search, postgresql'
                  }
                  onChange={(event) =>
                    setTagInput(
                      event.target.value,
                    )
                  }
                />
              </label>
            </div>

            <aside className="brain-dump-review__side">
              <div className="brain-dump-insight">
                <span>AI summary</span>

                <p>{suggestion.summary}</p>
              </div>

              <div className="brain-dump-insight">
                <span>Keywords</span>

                <div className="brain-dump-chips">
                  {(suggestion.keywords || []).map(
                    (keyword) => (
                      <span key={keyword}>
                        {keyword}
                      </span>
                    ),
                  )}
                </div>
              </div>

              <div className="brain-dump-insight">
                <span>Processing details</span>

                <dl>
                  <div>
                    <dt>Attempts</dt>
                    <dd>
                      {suggestion.attempts}
                    </dd>
                  </div>

                  <div>
                    <dt>Retries</dt>
                    <dd>
                      {suggestion.retry_count}
                    </dd>
                  </div>

                  <div>
                    <dt>Total tokens</dt>
                    <dd>
                      {suggestion.total_tokens}
                    </dd>
                  </div>
                </dl>
              </div>

              <label className="brain-dump-field">
                <span>
                  Rejection reason
                  <small>Optional</small>
                </span>

                <textarea
                  rows={4}
                  maxLength={500}
                  value={rejectionReason}
                  placeholder={
                    'Why is this suggestion not useful?'
                  }
                  onChange={(event) =>
                    setRejectionReason(
                      event.target.value,
                    )
                  }
                />
              </label>
            </aside>
          </div>

          <div className="brain-dump-review__actions">
            <button
              type="button"
              className="brain-dump-button brain-dump-button--danger"
              disabled={deciding}
              onClick={handleReject}
            >
              {deciding
                ? 'Please wait…'
                : 'Reject suggestion'}
            </button>

            <button
              type="button"
              className="brain-dump-button brain-dump-button--primary"
              disabled={
                deciding || !title.trim()
              }
              onClick={handleAccept}
            >
              {deciding
                ? 'Saving…'
                : 'Accept and create note'}
            </button>
          </div>
        </section>
      )}

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