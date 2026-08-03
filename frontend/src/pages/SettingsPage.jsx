import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import {
  getEffectiveTheme,
  getSavedTheme,
  saveTheme,
} from '../utils/theme'

const themeOptions = [
  {
    id: 'light',
    title: 'Light',
    description: 'Use the current bright cream and green design.',
    icon: 'sun',
  },
  {
    id: 'dark',
    title: 'Dark',
    description: 'Use a darker workspace that is easier on the eyes.',
    icon: 'moon',
  },
  {
    id: 'system',
    title: 'System',
    description: 'Match your computer or browser appearance setting.',
    icon: 'monitor',
  },
]

const informationalRows = [
  ['Notifications', 'In-app only', 'bell'],
  ['Language', 'English', 'notes'],
  [
    'Date and time',
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    'clock',
  ],
]

function SettingsPage() {
  const [theme, setTheme] = useState(getSavedTheme)
  const [appearanceOpen, setAppearanceOpen] = useState(false)

  useEffect(() => {
    const syncTheme = (event) => {
      setTheme(event.detail?.theme || getSavedTheme())
    }

    window.addEventListener('thoughtlinker-theme-change', syncTheme)
    return () => {
      window.removeEventListener('thoughtlinker-theme-change', syncTheme)
    }
  }, [])

  function chooseTheme(nextTheme) {
    saveTheme(nextTheme)
    setTheme(nextTheme)
    setAppearanceOpen(false)
  }

  const activeThemeLabel =
    theme === 'system'
      ? `System (${getEffectiveTheme(theme)})`
      : `${theme[0].toUpperCase()}${theme.slice(1)} theme`

  return (
    <AppShell title="Settings" subtitle="Personalize your workspace">
      <section className="settings-panel panel">
        <div className="settings-section-title">General</div>

        <button
          type="button"
          className="settings-row settings-row--button"
          onClick={() => setAppearanceOpen(true)}
          aria-haspopup="dialog"
        >
          <span className="settings-row__icon">
            <Icon name={theme === 'dark' ? 'moon' : 'sun'} size={17} />
          </span>
          <span className="settings-row__copy">
            <strong>Appearance</strong>
            <small>{activeThemeLabel}</small>
          </span>
          <span className="settings-chevron">›</span>
        </button>

        {informationalRows.map(([label, value, icon]) => (
          <div className="settings-row" key={label}>
            <span className="settings-row__icon">
              <Icon name={icon} size={17} />
            </span>
            <div>
              <strong>{label}</strong>
              <small>{value}</small>
            </div>
            <span className="settings-coming-soon">Coming soon</span>
          </div>
        ))}
      </section>

      <section className="settings-panel panel">
        <div className="settings-section-title">Dangerous zone</div>
        <div className="settings-row danger-row">
          <span className="settings-row__icon">
            <Icon name="trash" size={17} />
          </span>
          <div>
            <strong>Delete account</strong>
            <small>Account deletion is not enabled yet.</small>
          </div>
          <button disabled className="secondary-button">
            Unavailable
          </button>
        </div>
      </section>

      {appearanceOpen && (
        <div
          className="settings-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setAppearanceOpen(false)
            }
          }}
        >
          <section
            className="settings-modal panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="appearance-dialog-title"
          >
            <header className="settings-modal__header">
              <div>
                <h2 id="appearance-dialog-title">Choose appearance</h2>
                <p>Your selection is saved on this device.</p>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setAppearanceOpen(false)}
                aria-label="Close appearance settings"
              >
                <Icon name="close" size={18} />
              </button>
            </header>

            <div className="theme-choice-grid">
              {themeOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`theme-choice ${
                    theme === option.id ? 'is-selected' : ''
                  }`}
                  onClick={() => chooseTheme(option.id)}
                >
                  <span className="theme-choice__preview">
                    <span className="theme-choice__sidebar" />
                    <span className="theme-choice__content">
                      <i />
                      <i />
                      <i />
                    </span>
                    <Icon name={option.icon} size={18} />
                  </span>
                  <span className="theme-choice__text">
                    <strong>{option.title}</strong>
                    <small>{option.description}</small>
                  </span>
                  <span
                    className={`theme-choice__check ${
                      theme === option.id ? 'is-visible' : ''
                    }`}
                  >
                    <Icon name="check" size={15} />
                  </span>
                </button>
              ))}
            </div>
          </section>
        </div>
      )}
    </AppShell>
  )
}

export default SettingsPage
