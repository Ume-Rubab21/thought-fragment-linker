import Icon from './Icon'

export default function Brand({ compact = false, showTagline = true, className = '' }) {
  return (
    <div className={`brand ${compact ? 'brand--compact' : ''} ${className}`.trim()}>
      <span className="brand__mark"><Icon name="brain" size={24} /></span>
      {!compact && (
        <span className="brand__copy">
          <strong>ThoughtLinker</strong>
          {showTagline && <small>Think. Link. Grow.</small>}
        </span>
      )}
    </div>
  )
}
