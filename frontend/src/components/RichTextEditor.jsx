import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { marked } from 'marked'
import TurndownService from 'turndown'
import { useEffect, useRef } from 'react'

const turndown = new TurndownService({ headingStyle: 'atx', bulletListMarker: '-' })

const TOOLBAR_ITEMS = [
  { label: 'B', title: 'Bold', action: (editor) => editor.chain().focus().toggleBold().run(), active: (editor) => editor.isActive('bold') },
  { label: 'I', title: 'Italic', action: (editor) => editor.chain().focus().toggleItalic().run(), active: (editor) => editor.isActive('italic') },
  { label: 'H', title: 'Heading', action: (editor) => editor.chain().focus().toggleHeading({ level: 2 }).run(), active: (editor) => editor.isActive('heading') },
  { label: '•', title: 'Bullet list', action: (editor) => editor.chain().focus().toggleBulletList().run(), active: (editor) => editor.isActive('bulletList') },
  { label: '1.', title: 'Numbered list', action: (editor) => editor.chain().focus().toggleOrderedList().run(), active: (editor) => editor.isActive('orderedList') },
]

function RichTextEditor({ content, onChange, placeholder = 'Write anything you\'re thinking...' }) {
  const isInitialMount = useRef(true)

  const editor = useEditor({
    extensions: [StarterKit],
    content: content ? marked.parse(content) : '',
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none flex-1 px-6 py-4 focus:outline-none min-h-[300px] leading-relaxed',
      },
    },
    onUpdate: ({ editor: ed }) => {
      const html = ed.getHTML()
      const md = html === '<p></p>' ? '' : turndown.turndown(html)
      onChange(md)
    },
  })

  useEffect(() => {
    if (!editor) return
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }
    const html = editor.getHTML()
    const currentMd = html === '<p></p>' ? '' : turndown.turndown(html)
    if (currentMd !== content) {
      editor.commands.setContent(content ? marked.parse(content) : '')
    }
  }, [content, editor])

  if (!editor) return null

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center gap-1 px-6 py-2 border-y border-card-border bg-white shrink-0">
        {TOOLBAR_ITEMS.map((item) => (
          <button
            key={item.label}
            type="button"
            title={item.title}
            onClick={() => item.action(editor)}
            className={`w-8 h-8 flex items-center justify-center rounded text-sm font-medium ${
              item.active(editor)
                ? 'bg-accent/10 text-accent'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto bg-white relative">
        {!content && editor.isEmpty && (
          <p className="absolute top-4 left-6 text-sm text-gray-400 pointer-events-none">
            {placeholder}
          </p>
        )}
        <EditorContent editor={editor} className="h-full" />
      </div>
    </div>
  )
}

export default RichTextEditor
