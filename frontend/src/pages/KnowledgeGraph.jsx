import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  getKnowledgeGraph,
  listCollections,
  listTags,
} from '../api'
import AppShell from '../components/AppShell'
import './KnowledgeGraph.css'


const WIDTH = 1040
const HEIGHT = 610
const CENTER_X = 500
const CENTER_Y = 300


function shorten(value, maxLength = 34) {
  const text = String(value || '').trim()
  return text.length > maxLength
    ? `${text.slice(0, maxLength - 1)}…`
    : text
}


function buildLayout(nodes, focusId = null) {
  const positions = new Map()
  const notes = nodes.filter((node) => node.kind === 'note')
  const tags = nodes.filter((node) => node.kind === 'tag')

  if (focusId) {
    const focus = notes.find((node) => node.entity_id === focusId)

    if (focus) {
      positions.set(focus.id, {
        x: CENTER_X,
        y: CENTER_Y,
      })
    }

    notes
      .filter((node) => node !== focus)
      .forEach((node, index, values) => {
        const angle =
          (Math.PI * 2 * index) / Math.max(values.length, 1) -
          Math.PI / 2

        positions.set(node.id, {
          x: CENTER_X + Math.cos(angle) * 235,
          y: CENTER_Y + Math.sin(angle) * 195,
        })
      })

    tags.forEach((node, index) => {
      const angle =
        (Math.PI * 2 * index) / Math.max(tags.length, 1) -
        Math.PI / 2

      positions.set(node.id, {
        x: CENTER_X + Math.cos(angle) * 395,
        y: CENTER_Y + Math.sin(angle) * 250,
      })
    })

    return positions
  }

  const goldenAngle = Math.PI * (3 - Math.sqrt(5))

  notes.forEach((node, index) => {
    const progress =
      notes.length <= 1 ? 0 : index / (notes.length - 1)
    const angle = index * goldenAngle
    const radius = 40 + Math.sqrt(progress) * 220

    positions.set(node.id, {
      x: CENTER_X + Math.cos(angle) * radius * 1.18,
      y: CENTER_Y + Math.sin(angle) * radius * 0.88,
    })
  })

  tags.forEach((node, index) => {
    const angle =
      (Math.PI * 2 * index) / Math.max(tags.length, 1) -
      Math.PI / 2

    positions.set(node.id, {
      x: CENTER_X + Math.cos(angle) * 405,
      y: CENTER_Y + Math.sin(angle) * 255,
    })
  })

  return positions
}


export default function KnowledgeGraph() {
  const navigate = useNavigate()

  const [graph, setGraph] = useState({
    nodes: [],
    edges: [],
    total_note_count: 0,
    filtered_note_count: 0,
    visible_note_count: 0,
    tag_count: 0,
    connection_count: 0,
  })
  const [tags, setTags] = useState([])
  const [collections, setCollections] = useState([])
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [tagId, setTagId] = useState('')
  const [collectionId, setCollectionId] = useState('')
  const [sort, setSort] = useState('connected')
  const [limit, setLimit] = useState(20)
  const [focusNoteId, setFocusNoteId] = useState('')
  const [selectedId, setSelectedId] = useState('')
  const [hoveredId, setHoveredId] = useState('')
  const [showTags, setShowTags] = useState(true)
  const [showTagLines, setShowTagLines] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      listTags(),
      listCollections(),
    ])
      .then(([tagData, collectionData]) => {
        setTags(tagData || [])
        setCollections(collectionData || [])
      })
      .catch(() => {
        // Graph still works if filter options fail.
      })
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim())
      setFocusNoteId('')
      setSelectedId('')
    }, 350)

    return () => window.clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    let cancelled = false

    setLoading(true)
    setError('')

    getKnowledgeGraph({
      search,
      tag_id: tagId,
      collection_id: collectionId,
      sort,
      limit,
      focus_note_id: focusNoteId,
    })
      .then((data) => {
        if (!cancelled) {
          setGraph(data)
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(
            requestError.message ||
              'Unable to load the knowledge graph.',
          )
          setGraph((current) => ({
            ...current,
            nodes: [],
            edges: [],
          }))
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [
    search,
    tagId,
    collectionId,
    sort,
    limit,
    focusNoteId,
  ])

  const visible = useMemo(() => {
    const nodes = showTags
      ? graph.nodes || []
      : (graph.nodes || []).filter(
          (node) => node.kind !== 'tag',
        )

    const ids = new Set(nodes.map((node) => node.id))

    const edges = (graph.edges || []).filter((edge) => {
      if (!ids.has(edge.source) || !ids.has(edge.target)) {
        return false
      }

      if (edge.kind === 'tagged') {
        return showTags && showTagLines
      }

      return true
    })

    return {
      nodes,
      edges,
      positions: buildLayout(nodes, focusNoteId || null),
    }
  }, [graph, showTags, showTagLines, focusNoteId])

  const selectedNode =
    (graph.nodes || []).find((node) => node.id === selectedId) ||
    (focusNoteId
      ? (graph.nodes || []).find(
          (node) =>
            node.kind === 'note' &&
            node.entity_id === focusNoteId,
        )
      : null)

  const activeId = hoveredId || selectedNode?.id || ''

  const connectedIds = useMemo(() => {
    const values = new Set()

    if (!activeId) return values

    values.add(activeId)

    visible.edges.forEach((edge) => {
      if (edge.source === activeId) values.add(edge.target)
      if (edge.target === activeId) values.add(edge.source)
    })

    return values
  }, [activeId, visible.edges])

  const connectedItems = useMemo(() => {
    if (!selectedNode) return []

    return (graph.edges || [])
      .filter(
        (edge) =>
          edge.source === selectedNode.id ||
          edge.target === selectedNode.id,
      )
      .map((edge) => {
        const otherId =
          edge.source === selectedNode.id
            ? edge.target
            : edge.source

        return {
          edge,
          node: (graph.nodes || []).find(
            (node) => node.id === otherId,
          ),
        }
      })
      .filter((item) => item.node)
      .slice(0, 12)
  }, [graph, selectedNode])

  function resetFilters() {
    setSearchInput('')
    setSearch('')
    setTagId('')
    setCollectionId('')
    setSort('connected')
    setLimit(20)
    setFocusNoteId('')
    setSelectedId('')
  }

  function selectNode(node) {
    setSelectedId(node.id)

    if (node.kind === 'note') {
      setFocusNoteId(node.entity_id)
    } else if (node.kind === 'tag') {
      setTagId(node.entity_id)
      setFocusNoteId('')
    }
  }

  function returnToOverview() {
    setFocusNoteId('')
    setSelectedId('')
  }

  return (
    <AppShell
      title="Knowledge Graph"
      subtitle="Filter your knowledge base and explore only the relationships that matter."
    >
      {error && (
        <div className="knowledge-graph-alert">
          {error}
        </div>
      )}

      <section className="graph-stats">
        <article>
          <span>Total notes</span>
          <strong>{graph.total_note_count || 0}</strong>
          <small>stored in your account</small>
        </article>
        <article>
          <span>Matching notes</span>
          <strong>{graph.filtered_note_count || 0}</strong>
          <small>after current filters</small>
        </article>
        <article>
          <span>Visible notes</span>
          <strong>{graph.visible_note_count || 0}</strong>
          <small>rendered in the graph</small>
        </article>
        <article>
          <span>View mode</span>
          <strong>{focusNoteId ? 'Focused' : 'Overview'}</strong>
          <small>
            {focusNoteId
              ? 'selected note and neighbours'
              : `${sort.replace('_', ' ')} sorting`}
          </small>
        </article>
      </section>

      <section className="knowledge-graph-toolbar">
        <label className="knowledge-graph-search">
          <span>Search</span>
          <input
            value={searchInput}
            placeholder="Search notes…"
            maxLength={200}
            onChange={(event) =>
              setSearchInput(event.target.value)
            }
          />
        </label>

        <label>
          <span>Tag</span>
          <select
            value={tagId}
            onChange={(event) => {
              setTagId(event.target.value)
              setFocusNoteId('')
              setSelectedId('')
            }}
          >
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Collection</span>
          <select
            value={collectionId}
            onChange={(event) => {
              setCollectionId(event.target.value)
              setFocusNoteId('')
              setSelectedId('')
            }}
          >
            <option value="">All collections</option>
            {collections.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Sort</span>
          <select
            value={sort}
            disabled={Boolean(focusNoteId)}
            onChange={(event) => setSort(event.target.value)}
          >
            <option value="connected">Most connected</option>
            <option value="updated">Recently updated</option>
            <option value="created">Recently created</option>
            <option value="title">A–Z</option>
          </select>
        </label>

        <label>
          <span>Graph size</span>
          <select
            value={limit}
            disabled={Boolean(focusNoteId)}
            onChange={(event) =>
              setLimit(Number(event.target.value))
            }
          >
            <option value={10}>10 notes</option>
            <option value={20}>20 notes</option>
            <option value={30}>30 notes</option>
            <option value={50}>50 notes</option>
          </select>
        </label>

        <button
          type="button"
          className="knowledge-graph-reset"
          onClick={resetFilters}
        >
          Reset
        </button>
      </section>

      <section className="knowledge-graph-subbar">
        <span>
          {focusNoteId
            ? 'Focused view: showing only direct relationships.'
            : `Showing ${graph.visible_note_count || 0} of ${graph.filtered_note_count || 0} matching notes.`}
        </span>

        <div>
          <label>
            <input
              type="checkbox"
              checked={showTags}
              onChange={(event) =>
                setShowTags(event.target.checked)
              }
            />
            Tags
          </label>
          <label>
            <input
              type="checkbox"
              checked={showTagLines}
              disabled={!showTags}
              onChange={(event) =>
                setShowTagLines(event.target.checked)
              }
            />
            Tag lines
          </label>

          {focusNoteId && (
            <button type="button" onClick={returnToOverview}>
              Back to overview
            </button>
          )}
        </div>
      </section>

      <section className="knowledge-graph-shell">
        <div className="knowledge-graph-card">
          {loading ? (
            <div className="knowledge-graph-empty">
              Loading filtered graph…
            </div>
          ) : visible.nodes.length ? (
            <svg
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              role="img"
              aria-label="Filtered knowledge graph"
            >
              <g className="knowledge-graph-edges">
                {visible.edges.map((edge) => {
                  const source = visible.positions.get(edge.source)
                  const target = visible.positions.get(edge.target)

                  if (!source || !target) return null

                  const highlighted =
                    activeId &&
                    (edge.source === activeId ||
                      edge.target === activeId)

                  return (
                    <line
                      key={edge.id}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      className={[
                        `is-${edge.kind}`,
                        highlighted ? 'is-highlighted' : '',
                        activeId && !highlighted ? 'is-muted' : '',
                      ].join(' ')}
                    />
                  )
                })}
              </g>

              <g className="knowledge-graph-nodes">
                {visible.nodes.map((node) => {
                  const point = visible.positions.get(node.id)
                  if (!point) return null

                  const isActive = activeId === node.id
                  const isConnected = connectedIds.has(node.id)
                  const isMuted = activeId && !isConnected
                  const isFocus =
                    node.kind === 'note' &&
                    node.entity_id === focusNoteId

                  const radius = isFocus
                    ? 38
                    : node.kind === 'note'
                      ? Math.min(22, 12 + Math.sqrt(node.weight || 1) * 2)
                      : 9

                  const showLabel =
                    isFocus ||
                    isActive ||
                    (focusNoteId && node.kind === 'note')

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${point.x} ${point.y})`}
                      className={[
                        'knowledge-node',
                        `is-${node.kind}`,
                        isActive ? 'is-active' : '',
                        isConnected ? 'is-connected' : '',
                        isMuted ? 'is-muted' : '',
                        isFocus ? 'is-focus' : '',
                      ].join(' ')}
                      role="button"
                      tabIndex="0"
                      onClick={() => selectNode(node)}
                      onMouseEnter={() => setHoveredId(node.id)}
                      onMouseLeave={() => setHoveredId('')}
                      onKeyDown={(event) => {
                        if (
                          event.key === 'Enter' ||
                          event.key === ' '
                        ) {
                          event.preventDefault()
                          selectNode(node)
                        }
                      }}
                    >
                      <circle r={radius} />
                      {showLabel && (
                        <text
                          y={radius + 18}
                          textAnchor="middle"
                          className="knowledge-node__label"
                        >
                          {shorten(node.label, isFocus ? 44 : 30)}
                        </text>
                      )}
                    </g>
                  )
                })}
              </g>
            </svg>
          ) : (
            <div className="knowledge-graph-empty">
              No notes match the selected filters.
            </div>
          )}
        </div>

        <aside className="knowledge-graph-details">
          {selectedNode ? (
            <>
              <div className="knowledge-graph-details__head">
                <span>
                  {selectedNode.kind === 'note'
                    ? 'Selected note'
                    : 'Selected tag'}
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedId('')}
                  aria-label="Close details"
                >
                  ×
                </button>
              </div>

              <h2>{selectedNode.label}</h2>

              {selectedNode.preview && (
                <p className="knowledge-graph-preview">
                  {selectedNode.preview}
                </p>
              )}

              {selectedNode.collection_name && (
                <div className="knowledge-graph-collection">
                  Collection: {selectedNode.collection_name}
                </div>
              )}

              {selectedNode.tags?.length > 0 && (
                <div className="knowledge-graph-tags">
                  {selectedNode.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              )}

              <div className="knowledge-graph-neighbours">
                <strong>Connected items</strong>
                {connectedItems.length ? (
                  connectedItems.map(({ edge, node }) => (
                    <button
                      type="button"
                      key={`${edge.id}-${node.id}`}
                      onClick={() => selectNode(node)}
                    >
                      <span className={`is-${node.kind}`} />
                      <b>{shorten(node.label, 40)}</b>
                      <small>
                        {node.kind === 'note'
                          ? 'Related note'
                          : 'Tag'}
                      </small>
                    </button>
                  ))
                ) : (
                  <p>No visible relationships for this item.</p>
                )}
              </div>

              {selectedNode.kind === 'note' && (
                <button
                  type="button"
                  className="knowledge-graph-open-note"
                  onClick={() =>
                    navigate(`/notes/${selectedNode.entity_id}`)
                  }
                >
                  Open note
                </button>
              )}
            </>
          ) : (
            <div className="knowledge-graph-details__placeholder">
              <span>Explore</span>
              <h2>Select a node</h2>
              <p>
                Click a note to load a clean focused graph containing
                only its direct relationships.
              </p>
              <p>
                Filters keep the graph readable even when thousands
                of notes are stored.
              </p>
            </div>
          )}
        </aside>
      </section>

      <section className="graph-legend">
        <span><i className="is-note" /> Note</span>
        <span><i className="is-tag" /> Tag</span>
        <span><b className="is-related" /> Approved note link</span>
        <span><b className="is-tagged" /> Tag relationship</span>
        <small>
          The backend searches at most 200 candidates and the graph
          renders at most 50 notes.
        </small>
      </section>
    </AppShell>
  )
}
