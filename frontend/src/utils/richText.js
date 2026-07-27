const allowedTags = new Set([
  'P', 'BR', 'DIV', 'STRONG', 'B', 'EM', 'I', 'U', 'S', 'STRIKE',
  'H1', 'H2', 'H3', 'UL', 'OL', 'LI', 'BLOCKQUOTE', 'A', 'SPAN',
])

export function sanitizeRichText(html = '') {
  if (typeof window === 'undefined') return html
  const documentNode = new DOMParser().parseFromString(`<div>${html}</div>`, 'text/html')
  const root = documentNode.body.firstElementChild

  root.querySelectorAll('*').forEach((node) => {
    if (!allowedTags.has(node.tagName)) {
      node.replaceWith(...node.childNodes)
      return
    }

    Array.from(node.attributes).forEach((attribute) => {
      const name = attribute.name.toLowerCase()
      const keepHref = node.tagName === 'A' && name === 'href'
      if (!keepHref) node.removeAttribute(attribute.name)
    })

    if (node.tagName === 'A') {
      const href = node.getAttribute('href') || ''
      if (!/^(https?:\/\/|mailto:)/i.test(href)) {
        node.removeAttribute('href')
      } else {
        node.setAttribute('target', '_blank')
        node.setAttribute('rel', 'noreferrer noopener')
      }
    }
  })

  return root.innerHTML
}

export function htmlToPlainText(html = '') {
  if (!html) return ''
  if (typeof window === 'undefined') return html.replace(/<[^>]*>/g, ' ')
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return (doc.body.textContent || '').replace(/\s+/g, ' ').trim()
}

export function shortText(html, maxLength = 150) {
  const text = htmlToPlainText(html)
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength).trim()}…`
}
