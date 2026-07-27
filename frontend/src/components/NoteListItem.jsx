import { Link } from 'react-router-dom'

const TAG_COLORS = [
  'bg-tag-blue-bg text-tag-blue-text',
  'bg-tag-purple-bg text-tag-purple-text',
  'bg-tag-orange-bg text-tag-orange-text',
  'bg-tag-pink-bg text-tag-pink-text',
]

function NoteListItem({ note, onDelete, showTags = true, showDelete = true }) {
  const preview = note.body_md
    ? note.body_md.replace(/[#*_`>\[\]()!-]/g, '').slice(0, 120)
    : ''

  return (
    <li className="bg-white border border-card-border rounded-lg px-4 py-3 hover:shadow-sm transition-shadow">
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0 flex-1">
          <Link
            to={`/notes/${note.id}`}
            className="font-semibold text-gray-900 hover:text-accent block truncate"
          >
            {note.title}
          </Link>
          {preview && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{preview}</p>
          )}
          {showTags && note.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {note.tags.map((tag, i) => (
                <span
                  key={tag.id}
                  className={`text-xs px-2 py-0.5 rounded-md font-medium ${TAG_COLORS[i % TAG_COLORS.length]}`}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
        </div>
        {showDelete && (
          <button
            onClick={() => onDelete(note.id)}
            className="text-red-400 text-xs hover:text-red-600 shrink-0 mt-0.5"
          >
            Delete
          </button>
        )}
      </div>
    </li>
  )
}

export default NoteListItem
