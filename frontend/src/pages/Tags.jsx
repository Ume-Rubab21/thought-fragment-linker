import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listTags } from '../api'

const TAG_COLORS = [
  'bg-tag-blue-bg text-tag-blue-text',
  'bg-tag-purple-bg text-tag-purple-text',
  'bg-tag-orange-bg text-tag-orange-text',
  'bg-tag-pink-bg text-tag-pink-text',
]

function Tags() {
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listTags()
      .then(setTags)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-gray-500">Loading...</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-4 lg:px-6 py-6 lg:py-8">
      <h1 className="font-bold text-lg text-gray-900 mb-1">Tags</h1>
      <p className="text-sm text-gray-400 mb-6">
        Click a tag to see all notes with that tag.
      </p>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {tags.length === 0 && (
        <p className="text-gray-400 text-sm">
          No tags yet. Add tags to notes from the note editor.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {tags.map((tag, i) => (
          <Link
            key={tag.id}
            to={`/dashboard?tag=${encodeURIComponent(tag.name)}`}
            className={`text-sm px-3 py-1.5 rounded-lg font-medium hover:opacity-80 transition-opacity ${TAG_COLORS[i % TAG_COLORS.length]}`}
          >
            {tag.name}
            <span className="ml-1.5 opacity-60">({tag.note_count})</span>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Tags
