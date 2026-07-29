import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import {
  getBrainDump,
  getBrainDumpStatus,
  submitBrainDump,
} from '../api'

const EXAMPLE_PROMPTS = [
  'A stray idea about a side project…',
  'Something you learned today…',
  'A question you keep circling back to…',
]

const BENEFITS = [
  {
    emoji: '⭐',
    title: 'Capture anything',
    description: 'No thought is too small or messy.',
  },
  {
    emoji: '🔗',
    title: 'Connect the dots',
    description: 'Everything links to what you know.',
  },
  {
    emoji: '🌱',
    title: 'Ideas become growth',
    description: 'A small thought can become progress.',
  },
]

export default function BrainDump() {
  const navigate = useNavigate()
  const textareaRef = useRef(null)

  const [text, setText] = useState('')
  const [brainDumpId, setBrainDumpId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const isProcessing =
    loading &&
    status &&
    status !== 'ready' &&
    status !== 'failed'

  async function handleSubmit(event) {
    event.preventDefault()

    if (!text.trim() || loading) {
      return
    }

    setError('')
    setResult(null)

    try {
      const response = await submitBrainDump(text.trim())

      setBrainDumpId(response.id)
      setStatus(response.status)
      setLoading(true)
    } catch (err) {
      setError(
        err.message ||
          'Could not submit your Brain Dump.',
      )
    }
  }

  useEffect(() => {
    if (!brainDumpId) {
      return undefined
    }

    const interval = window.setInterval(
      async () => {
        try {
          const response =
            await getBrainDumpStatus(brainDumpId)

          setStatus(response.status)

          if (response.status === 'ready') {
            window.clearInterval(interval)

            const completed =
              await getBrainDump(brainDumpId)

            setResult(completed)
            setLoading(false)
          }

          if (response.status === 'failed') {
            window.clearInterval(interval)
            setLoading(false)

            setError(
              response.error_message ||
                'Processing failed. Please try again.',
            )
          }
        } catch (err) {
          window.clearInterval(interval)
          setLoading(false)

          setError(
            err.message ||
              'Lost connection while processing.',
          )
        }
      },
      1000,
    )

    return () => {
      window.clearInterval(interval)
    }
  }, [brainDumpId])

  function startAnother() {
    setText('')
    setBrainDumpId(null)
    setStatus(null)
    setResult(null)
    setError('')

    window.setTimeout(() => {
      textareaRef.current?.focus()
    }, 50)
  }

  return (
    <AppShell
      title={
        <>
            🌿 <span className="brain-title">Brain Dump</span> ✨
        </>
    }
      subtitle="Capture every thought. We'll organize the rest."
      contentClassName="brain-dump-page"
    >
      {error && (
        <div className="alert alert--error">
          {error}
        </div>
      )}

      <div className="brain-dump-workspace">
        <div className="brain-dump-left">
          <section className="panel braindump-composer">
            <div className="braindump-hero">
              <span
                className="braindump-hero__emoji"
                role="img"
                aria-label="Brain"
              >
                🧠
              </span>

              <div>
                <h2>What&apos;s on your mind?</h2>

                <p>
                  Write freely — half-formed thoughts,
                  questions, links, anything. ThoughtLinker
                  will organize and connect it to what you
                  already know.
                </p>
              </div>
            </div>

            <form
              onSubmit={handleSubmit}
              className="braindump-form"
            >
              <textarea
                ref={textareaRef}
                className="braindump-textarea"
                rows={12}
                placeholder={EXAMPLE_PROMPTS[0]}
                value={text}
                onChange={(event) =>
                  setText(event.target.value)
                }
                disabled={loading}
                maxLength={20000}
              />

              <div className="braindump-form__footer">
                <div className="brain-dump-writing-details">
                  <span className="braindump-counter">
                    {text.length.toLocaleString()} characters
                  </span>

                  <span className="brain-dump-save-message">
                    Saved in All Notes after processing
                  </span>
                </div>

                <button
                  type="submit"
                  className="primary-button brain-dump-submit"
                  disabled={loading || !text.trim()}
                >
                  <Icon name="brain" size={16} />

                  {loading
                    ? 'Processing…'
                    : 'Process Brain Dump'}
                </button>
              </div>
            </form>
          </section>

          {isProcessing && (
            <section className="panel braindump-status is-thinking">
              <div className="braindump-status__icon">
                <span className="braindump-pulse" />

                <span
                  role="img"
                  aria-label="Thinking"
                >
                  🤖
                </span>
              </div>

              <div>
                <strong>
                  ThoughtLinker is organizing your idea…
                </strong>

                <p>
                  Status:{' '}
                  <span className="braindump-status__badge">
                    {status}
                  </span>
                </p>
              </div>
            </section>
          )}

          {result && (
            <section className="panel braindump-status is-complete">
              <div className="braindump-status__icon braindump-status__icon--done">
                <Icon name="check" size={20} />
              </div>

              <div className="braindump-result">
                <strong>
                  Your thought has been saved
                </strong>

                <p>
                  It is now available in your knowledge
                  base.
                </p>

                <p className="braindump-result__text">
                  {result.raw_text}
                </p>

                <div className="braindump-result__actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={startAnother}
                  >
                    <Icon name="plus" size={14} />
                    New Brain Dump
                  </button>

                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => navigate('/notes')}
                  >
                    <Icon name="notes" size={14} />
                    View All Notes
                  </button>
                </div>
              </div>
            </section>
          )}
        </div>

        <aside className="brain-illustration-panel" aria-label="Relaxing Brain Dump illustration" >

          <picture>

            <source
             srcSet="/assets/brain_dump_relaxing_panel.gif"
            type="image/gif"
            />

            <img
             src="/assets/brain_dump_relaxing_panel.png"
             alt="A peaceful floating brain surrounded by ideas, plants, a gift, and encouraging messages"
             className="brain-illustration-panel__image"
            />
          </picture>
        </aside>
      </div>
    </AppShell>
  )
}