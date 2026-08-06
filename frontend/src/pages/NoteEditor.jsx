import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import RichTextToolbar from '../components/RichTextToolbar'

import {
  attachTagToNote,
  deleteNote,
  getNote,
  getRelatedNotes,
  listCollections,
  listTags,
  removeTagFromNote,
  updateNote,
} from '../api'

import {
  sanitizeRichText,
} from '../utils/richText'

import {
  removeInstantCacheByPrefix,
} from '../utils/instantCache'


function formatSimilarity(value) {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return '0%'
  }

  const percentage = Math.round(
    Math.max(
      0,
      Math.min(1, numericValue),
    ) * 100,
  )

  return `${percentage}%`
}


function NoteEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const editorRef = useRef(null)

  const [title, setTitle] = useState('')
  const [bodyHtml, setBodyHtml] =
    useState('')

  const [
    collectionId,
    setCollectionId,
  ] = useState('')

  const [noteTags, setNoteTags] =
    useState([])

  const [allTags, setAllTags] =
    useState([])

  const [collections, setCollections] =
    useState([])

  const [tagInput, setTagInput] =
    useState('')

  const [loading, setLoading] =
    useState(true)

  const [saving, setSaving] =
    useState(false)

  const [
    savedMessage,
    setSavedMessage,
  ] = useState('')

  const [error, setError] =
    useState('')

  const [
    embeddingWarning,
    setEmbeddingWarning,
  ] = useState('')

  const [
    relatedNotes,
    setRelatedNotes,
  ] = useState([])

  const [
    relatedLoading,
    setRelatedLoading,
  ] = useState(true)

  const [
    relatedError,
    setRelatedError,
  ] = useState('')


  const loadRelatedNotes =
    useCallback(async () => {
      setRelatedLoading(true)
      setRelatedError('')

      try {
        const data =
          await getRelatedNotes(id, 5)

        setRelatedNotes(
          Array.isArray(data)
            ? data
            : [],
        )

        return true
      } catch (requestError) {
        setRelatedNotes([])

        setRelatedError(
          requestError.message ||
            'Unable to load related notes.',
        )

        return false
      } finally {
        setRelatedLoading(false)
      }
    }, [id])


  useEffect(() => {
    setLoading(true)
    setError('')
    setEmbeddingWarning('')

    Promise.all([
      getNote(id),
      listTags(),
      listCollections(),
    ])
      .then(
        ([
          note,
          tagData,
          collectionData,
        ]) => {
          const safeHtml =
            sanitizeRichText(
              note.body_md ||
                '<p></p>',
            )

          setTitle(note.title)
          setBodyHtml(safeHtml)

          setCollectionId(
            note.collection_id || '',
          )

          setNoteTags(
            note.tags || [],
          )

          setAllTags(
            tagData || [],
          )

          setCollections(
            collectionData || [],
          )

          requestAnimationFrame(() => {
            if (editorRef.current) {
              editorRef.current.innerHTML =
                safeHtml ||
                '<p><br></p>'
            }
          })
        },
      )
      .catch((requestError) => {
        setError(requestError.message)
      })
      .finally(() => {
        setLoading(false)
      })

    loadRelatedNotes()
  }, [id, loadRelatedNotes])


  function syncEditor() {
    const safeHtml =
      sanitizeRichText(
        editorRef.current?.innerHTML ||
          '',
      )

    setBodyHtml(safeHtml)
  }


  function runCommand(
    command,
    value = null,
  ) {
    editorRef.current?.focus()

    document.execCommand(
      command,
      false,
      value,
    )

    syncEditor()
  }


  async function save() {
    if (!title.trim()) {
      setError(
        'Please add a note title.',
      )

      return
    }

    setSaving(true)
    setError('')

    try {
      const safeHtml =
        sanitizeRichText(
          editorRef.current
            ?.innerHTML ||
            bodyHtml,
        )

      const result = await updateNote(
        id,
        {
          title: title.trim(),
          body_md: safeHtml,
          collection_id:
            collectionId || null,
        },
        {
          includeMeta: true,
        },
      )

      const embeddingStatus =
        result.headers.get(
          'x-embedding-status',
        )

      setBodyHtml(safeHtml)

      if (
        embeddingStatus === 'failed'
      ) {
        setSavedMessage(
          'Note saved',
        )

        setEmbeddingWarning(
          'Your note was saved, but semantic matching is temporarily unavailable. You can save again later to retry.',
        )
      } else {
        const relatedLoaded =
          await loadRelatedNotes()

        if (relatedLoaded) {
          setEmbeddingWarning('')
        }

        setSavedMessage('Saved')
      }

      window.setTimeout(() => {
        setSavedMessage('')
      }, 1800)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }


  async function removeNote() {
    const confirmed = window.confirm(
      'Delete this note? This cannot be undone.',
    )

    if (!confirmed) {
      return
    }

    try {
      await deleteNote(id)

      removeInstantCacheByPrefix('notes:')
      removeInstantCacheByPrefix('suggestions:')
      removeInstantCacheByPrefix('suggestion-detail:')

      navigate('/notes')
    } catch (requestError) {
      setError(requestError.message)
    }
  }


  async function addTag(event) {
    event.preventDefault()

    if (!tagInput.trim()) {
      return
    }

    try {
      const tag =
        await attachTagToNote(
          id,
          tagInput,
        )

      setNoteTags((current) =>
        current.some(
          (item) =>
            item.id === tag.id,
        )
          ? current
          : [...current, tag],
      )

      setAllTags((current) =>
        current.some(
          (item) =>
            item.id === tag.id,
        )
          ? current
          : [...current, tag],
      )

      setTagInput('')
    } catch (requestError) {
      setError(requestError.message)
    }
  }


  async function removeTag(tagId) {
    try {
      await removeTagFromNote(
        id,
        tagId,
      )

      setNoteTags((current) =>
        current.filter(
          (tag) =>
            tag.id !== tagId,
        ),
      )
    } catch (requestError) {
      setError(requestError.message)
    }
  }


  const availableTags =
    allTags
      .filter(
        (tag) =>
          !noteTags.some(
            (item) =>
              item.id === tag.id,
          ),
      )
      .slice(0, 6)


  return (
    <AppShell
      title="Rich Text Note Editor"
      contentClassName="editor-page-content"
      actions={
        <>
          <button
            type="button"
            className="icon-button"
            onClick={() =>
              runCommand('undo')
            }
            title="Undo"
          >
            ↶
          </button>

          <button
            type="button"
            className="icon-button"
            onClick={() =>
              runCommand('redo')
            }
            title="Redo"
          >
            ↷
          </button>

          <button
            type="button"
            className="secondary-button editor-cancel"
            onClick={() =>
              navigate('/notes')
            }
          >
            Back
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={save}
            disabled={saving}
          >
            {saving
              ? 'Saving…'
              : 'Save'}
          </button>
        </>
      }
    >
      {error && (
        <div className="alert alert--error">
          {error}
        </div>
      )}

      {embeddingWarning && (
        <div className="alert alert--warning">
          <Icon
            name="brain"
            size={17}
          />

          <span>
            {embeddingWarning}
          </span>
        </div>
      )}

      {savedMessage && (
        <div className="save-toast">
          <Icon
            name="check"
            size={15}
          />

          {savedMessage}
        </div>
      )}

      {loading ? (
        <div className="panel editor-loading">
          Loading editor…
        </div>
      ) : (
        <div className="editor-layout">
          <section className="rich-editor panel">
            <input
              className="note-title-input"
              value={title}
              onChange={(event) =>
                setTitle(
                  event.target.value,
                )
              }
              placeholder="Untitled note"
              maxLength={180}
            />

            <RichTextToolbar
              onCommand={runCommand}
            />

            <div
              ref={editorRef}
              className="rich-editor__content"
              contentEditable
              suppressContentEditableWarning
              data-placeholder="Write anything on your mind..."
              onInput={syncEditor}
              onBlur={syncEditor}
            />
          </section>

          <aside className="editor-inspector">
            <section className="inspector-card panel">
              <div className="inspector-card__title">
                <span>Tags</span>
              </div>

              <div className="tag-editor-list">
                {noteTags.map(
                  (tag) => (
                    <span
                      className="tag-pill"
                      key={tag.id}
                    >
                      {tag.name}

                      <button
                        type="button"
                        onClick={() =>
                          removeTag(
                            tag.id,
                          )
                        }
                        aria-label={`Remove ${tag.name}`}
                      >
                        <Icon
                          name="close"
                          size={12}
                        />
                      </button>
                    </span>
                  ),
                )}

                {!noteTags.length && (
                  <small className="muted-copy">
                    No tags added.
                  </small>
                )}
              </div>

              <form
                className="tag-add-form"
                onSubmit={addTag}
              >
                <input
                  list="available-tags"
                  value={tagInput}
                  onChange={(event) =>
                    setTagInput(
                      event.target.value,
                    )
                  }
                  placeholder="Add tag..."
                  maxLength={30}
                />

                <datalist id="available-tags">
                  {availableTags.map(
                    (tag) => (
                      <option
                        value={tag.name}
                        key={tag.id}
                      />
                    ),
                  )}
                </datalist>

                <button type="submit">
                  <Icon
                    name="plus"
                    size={14}
                  />
                </button>
              </form>
            </section>

            <section className="inspector-card panel">
              <div className="inspector-card__title">
                <span>
                  Linking &amp; grouping
                </span>
              </div>

              <label className="inspector-field">
                <span>Collection</span>

                <select
                  value={collectionId}
                  onChange={(event) =>
                    setCollectionId(
                      event.target.value,
                    )
                  }
                >
                  <option value="">
                    Unfiled
                  </option>

                  {collections.map(
                    (collection) => (
                      <option
                        value={
                          collection.id
                        }
                        key={
                          collection.id
                        }
                      >
                        {
                          collection.name
                        }
                      </option>
                    ),
                  )}
                </select>
              </label>

              <div className="inspector-field">
                <span>Related notes</span>

                <div className="related-notes-panel">
                  {relatedLoading && (
                    <div className="related-notes-state">
                      <span className="related-notes-spinner" />

                      <span>
                        Finding related notes…
                      </span>
                    </div>
                  )}

                  {!relatedLoading &&
                    relatedError && (
                      <div className="related-notes-state related-notes-state--error">
                        <span>
                          {relatedError}
                        </span>

                        <button
                          type="button"
                          className="related-notes-retry"
                          onClick={
                            loadRelatedNotes
                          }
                        >
                          Try again
                        </button>
                      </div>
                    )}

                  {!relatedLoading &&
                    !relatedError &&
                    relatedNotes.length ===
                      0 && (
                      <div className="related-notes-state">
                        <Icon
                          name="link"
                          size={18}
                        />

                        <span>
                          No related notes yet.
                        </span>

                        <small>
                          Create another note with a similar topic.
                        </small>
                      </div>
                    )}

                  {!relatedLoading &&
                    !relatedError &&
                    relatedNotes.length >
                      0 && (
                      <div className="related-notes-list">
                        {relatedNotes.map(
                          (
                            relatedNote,
                          ) => (
                            <button
                              type="button"
                              className="related-note-item"
                              key={
                                relatedNote.id
                              }
                              onClick={() =>
                                navigate(
                                  `/notes/${relatedNote.id}`,
                                )
                              }
                            >
                              <span className="related-note-icon">
                                <Icon
                                  name="link"
                                  size={15}
                                />
                              </span>

                              <span className="related-note-copy">
                                <strong>
                                  {
                                    relatedNote.title
                                  }
                                </strong>

                                <small>
                                  {
                                    relatedNote.excerpt
                                  }
                                </small>
                              </span>

                              <span className="related-note-score">
                                {formatSimilarity(
                                  relatedNote.similarity,
                                )}
                              </span>
                            </button>
                          ),
                        )}
                      </div>
                    )}
                </div>
              </div>
            </section>

            <section className="inspector-card panel">
              <div className="inspector-card__title">
                <span>
                  AI-generated Tags
                </span>
              </div>

              <div className="suggested-tags-placeholder">
                <span>
                  AI-generated tags
                </span>

                <span>
                  AI-generated connections
                </span>

                <span>
                  AI-generated topic group
                </span>
              </div>

              <small className="muted-copy">
                Suggestion processing is added on Day 7.
              </small>
            </section>

            <button
              type="button"
              className="danger-button"
              onClick={removeNote}
            >
              <Icon
                name="trash"
                size={15}
              />

              Delete note
            </button>
          </aside>
        </div>
      )}
    </AppShell>
  )
}


export default NoteEditor