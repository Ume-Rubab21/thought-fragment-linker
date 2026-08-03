import Brand from './Brand'

function KnowledgeGraphPreview() {
  return (
    <aside className="auth-graph-card" aria-label="Knowledge graph preview">
      <div className="auth-graph-card__preview">
        <strong>Knowledge Graph</strong>
        <svg viewBox="0 0 150 76" role="img" aria-label="Example linked knowledge graph">
          <g className="auth-graph-lines">
            <path d="M74 39 37 20" />
            <path d="M74 39 47 53" />
            <path d="M74 39 76 12" />
            <path d="M74 39 111 20" />
            <path d="M74 39 116 42" />
            <path d="M74 39 101 61" />
            <path d="M37 20 20 28" />
            <path d="M37 20 30 9" />
            <path d="M111 20 132 14" />
            <path d="M116 42 137 47" />
            <path d="M47 53 24 63" />
          </g>
          <g className="auth-graph-node auth-graph-node--small">
            <circle cx="20" cy="28" r="4" /><circle cx="30" cy="9" r="4" />
            <circle cx="132" cy="14" r="4" /><circle cx="137" cy="47" r="4" />
            <circle cx="24" cy="63" r="4" /><circle cx="101" cy="61" r="5" />
            <circle cx="76" cy="12" r="5" />
          </g>
          <g className="auth-graph-node auth-graph-node--medium">
            <circle cx="37" cy="20" r="6" /><circle cx="47" cy="53" r="6" />
            <circle cx="111" cy="20" r="6" /><circle cx="116" cy="42" r="6" />
          </g>
          <circle className="auth-graph-node--main" cx="74" cy="39" r="9" />
        </svg>
      </div>
      <p>Discover new insights<br />upon login.</p>
      <a href="#auth-form" onClick={(event) => event.preventDefault()}>View knowledge graph<br />example.</a>
    </aside>
  )
}

export default function AuthShowcase({ title, screenLabel, children, graph = true, register = false }) {
  return (
    <main className={`auth-page ${register ? 'auth-page--register' : ''}`}>
      <span className="auth-sparkle auth-sparkle--large" aria-hidden="true" />
      <span className="auth-sparkle auth-sparkle--small" aria-hidden="true" />
      <div className="auth-side auth-side--left" aria-hidden="true"><span>Tags</span><span>Notes</span><span>Connections</span><p>Capture ideas.<br/>Connect knowledge.<br/><strong>Grow smarter.</strong></p></div>
      <div className="auth-side auth-side--right" aria-hidden="true"><span>AI Suggestions</span><span>Insights</span><span>Knowledge</span></div>

      <section className="auth-browser" aria-label="ThoughtLinker authentication">
        <div className="auth-browser__bar" aria-hidden="true">
          <span className="auth-browser__dot auth-browser__dot--red" />
          <span className="auth-browser__dot auth-browser__dot--yellow" />
          <span className="auth-browser__dot auth-browser__dot--green" />
        </div>

        <div className="auth-browser__content">
          <div className="auth-brand-lockup"><Brand showTagline={false} /></div>
          <h1 className="auth-welcome-title">{title}</h1>

          <section id="auth-form" className={`auth-card ${register ? 'auth-card--register' : ''}`}>
            <span className="auth-card__label">{screenLabel}</span>
            <div className="auth-card__form">{children}</div>
            {graph && <KnowledgeGraphPreview />}
          </section>
        </div>
      </section>
    </main>
  )
}
