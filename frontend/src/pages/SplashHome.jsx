import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Icon from '../components/Icon'
import { getToken } from '../api'
import './SplashHome.css'

const FEATURES = [
  { title: 'Notes', text: 'Your thoughts, organized and searchable.', icon: 'notes', side: 'left' },
  { title: 'Tags', text: 'Group ideas with meaningful tags.', icon: 'tag', side: 'left' },
  { title: 'Connections', text: 'Discover relationships between ideas.', icon: 'link', side: 'left' },
  { title: 'AI Suggestions', text: 'Smart suggestions that expand your knowledge.', icon: 'sparkles', side: 'right' },
  { title: 'Brain Dumps', text: 'Capture anything. We will make sense of it.', icon: 'brain', side: 'right' },
  { title: 'Knowledge Gaps', text: 'Discover what to explore and learn next.', icon: 'search', side: 'right' },
]

function FeatureCard({ item, index }) {
  return (
    <article className="splash-feature" style={{ '--delay': `${index * 110}ms` }}>
      <span className="splash-feature__icon">
        <Icon name={item.icon} size={28} />
      </span>
      <div>
        <h2>{item.title}</h2>
        <p>{item.text}</p>
      </div>
      <span className="splash-feature__wave" aria-hidden="true" />
    </article>
  )
}

function FloatingParticles() {
  const particles = useMemo(
    () =>
      Array.from({ length: 22 }, (_, i) => ({
        id: i,
        x: (i * 37) % 96,
        y: (i * 53) % 92,
        size: 3 + (i % 4),
        delay: (i % 7) * 0.45,
        duration: 5 + (i % 5),
      })),
    []
  )

  return (
    <div className="splash-particles" aria-hidden="true">
      {particles.map((p) => (
        <i
          key={p.id}
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
          }}
        />
      ))}
    </div>
  )
}

export default function SplashHome() {
  const navigate = useNavigate()
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    // Start fading out during the final 0.6 seconds.
    const fadeTimer = window.setTimeout(() => setLeaving(true), 6400)

    // Leave the splash screen after exactly 7 seconds.
    const routeTimer = window.setTimeout(() => {
      navigate(getToken() ? '/dashboard' : '/login', { replace: true })
    }, 7000)

    return () => {
      window.clearTimeout(fadeTimer)
      window.clearTimeout(routeTimer)
    }
  }, [navigate])

  const left = FEATURES.filter((feature) => feature.side === 'left')
  const right = FEATURES.filter((feature) => feature.side === 'right')

  return (
    <main className={`splash-home${leaving ? ' is-leaving' : ''}`}>
      <FloatingParticles />
      <div className="splash-network splash-network--left" aria-hidden="true" />
      <div className="splash-network splash-network--right" aria-hidden="true" />

      <section className="splash-column splash-column--left">
        {left.map((item, index) => (
          <FeatureCard key={item.title} item={item} index={index} />
        ))}
      </section>

      <section className="splash-center">
        <div className="splash-brandmark" aria-hidden="true">
          <span className="splash-orbit splash-orbit--one" />
          <span className="splash-orbit splash-orbit--two" />
          <Icon name="brain" size={108} />
        </div>

        <div className="splash-title-wrap">
          <h1>
            <span>Thought</span>
            <strong>Linker</strong>
          </h1>
          <p>
            Think <b>•</b> Link <b>•</b> Grow
          </p>
        </div>

        <div className="splash-visual" aria-hidden="true">
          <span className="splash-visual__orbit splash-visual__orbit--a" />
          <span className="splash-visual__orbit splash-visual__orbit--b" />
          <span className="splash-visual__node splash-visual__node--one">
            <Icon name="link" size={22} />
          </span>
          <span className="splash-visual__node splash-visual__node--two">
            <Icon name="tag" size={20} />
          </span>
          <span className="splash-visual__node splash-visual__node--three">
            <Icon name="sparkles" size={20} />
          </span>

          <div className="splash-document">
            <Icon name="notes" size={62} />
          </div>

          <div className="splash-pedestal">
            <i />
            <i />
            <i />
          </div>
        </div>

        <div className="splash-loading" role="status" aria-live="polite">
          <p>Loading your workspace...</p>
          <div className="splash-progress">
            <span />
          </div>
          <div className="splash-dots" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>
      </section>

      <section className="splash-column splash-column--right">
        {right.map((item, index) => (
          <FeatureCard key={item.title} item={item} index={index + 3} />
        ))}
      </section>

      <div className="splash-bottom-wave" aria-hidden="true" />
    </main>
  )
}