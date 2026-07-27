import { useState } from 'react'
import Icon from './Icon'

function ToolButton({ label, title, onClick, children }) {
  return (
    <button
      type="button"
      className="editor-tool"
      title={title}
      aria-label={title}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      {children || label}
    </button>
  )
}

export default function RichTextToolbar({ onCommand }) {
  const [block, setBlock] = useState('p')

  function addLink() {
    const url = window.prompt('Paste a URL (https://...)')
    if (url) onCommand('createLink', url)
  }

  return (
    <div className="rich-toolbar" role="toolbar" aria-label="Rich text formatting">
      <select
        value={block}
        className="editor-block-select"
        onChange={(event) => {
          setBlock(event.target.value)
          onCommand('formatBlock', event.target.value)
        }}
        aria-label="Text style"
      >
        <option value="p">Paragraph</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
        <option value="blockquote">Quote</option>
      </select>
      <span className="toolbar-divider" />
      <ToolButton title="Bold" onClick={() => onCommand('bold')}><strong>B</strong></ToolButton>
      <ToolButton title="Italic" onClick={() => onCommand('italic')}><em>I</em></ToolButton>
      <ToolButton title="Underline" onClick={() => onCommand('underline')}><u>U</u></ToolButton>
      <ToolButton title="Strike through" onClick={() => onCommand('strikeThrough')}><s>S</s></ToolButton>
      <span className="toolbar-divider" />
      <ToolButton title="Bulleted list" onClick={() => onCommand('insertUnorderedList')}>•≡</ToolButton>
      <ToolButton title="Numbered list" onClick={() => onCommand('insertOrderedList')}>1≡</ToolButton>
      <ToolButton title="Add link" onClick={addLink}><Icon name="link" size={16} /></ToolButton>
      <ToolButton title="Remove formatting" onClick={() => onCommand('removeFormat')}>Tx</ToolButton>
    </div>
  )
}
