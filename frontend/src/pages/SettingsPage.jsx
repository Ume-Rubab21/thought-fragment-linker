import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import {
  getEffectiveTheme,
  getSavedTheme,
  saveTheme,
} from '../utils/theme'
import {
  DEFAULT_PREFERENCES,
  getPreferences,
  savePreferences,
} from '../utils/preferences'
import {
  DEFAULT_NOTIFICATION_SETTINGS,
  getNotificationSettings,
  requestBrowserNotificationPermission,
  saveNotificationSettings,
  sendTestNotification,
} from '../utils/notifications'
import { getLanguageLabel, t } from '../utils/i18n'

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

const TIMEZONES = [
  'Asia/Karachi',
  'Asia/Dubai',
  'UTC',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
]

function Toggle({ checked, onChange, label, description, disabled = false }) {
  return (
    <label className={`settings-toggle-row${disabled ? ' is-disabled' : ''}`}>
      <span>
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        disabled={disabled}
      />
      <i aria-hidden="true" />
    </label>
  )
}

function SettingsModal({ title, description, onClose, children, wide = false }) {
  return (
    <div
      className="settings-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className={`settings-modal panel${wide ? ' settings-modal--wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="settings-modal__header">
          <div>
            <h2>{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Close"
          >
            <Icon name="close" size={18} />
          </button>
        </header>
        {children}
      </section>
    </div>
  )
}

function SettingsPage() {
  const [theme, setTheme] = useState(getSavedTheme)
  const [preferences, setPreferences] = useState(getPreferences)
  const [notificationSettings, setNotificationSettings] = useState(
    getNotificationSettings,
  )
  const [openPanel, setOpenPanel] = useState(null)
  const [status, setStatus] = useState('')

  useEffect(() => {
    const syncTheme = (event) => {
      setTheme(event.detail?.theme || getSavedTheme())
    }

    const syncPreferences = (event) => {
      setPreferences(event.detail || getPreferences())
    }

    window.addEventListener('thoughtlinker-theme-change', syncTheme)
    window.addEventListener('thoughtlinker-preferences-change', syncPreferences)

    return () => {
      window.removeEventListener('thoughtlinker-theme-change', syncTheme)
      window.removeEventListener(
        'thoughtlinker-preferences-change',
        syncPreferences,
      )
    }
  }, [])

  const copy = useMemo(
    () => ({
      settings: t('settings', preferences.language),
      subtitle: t('settingsSubtitle', preferences.language),
      general: t('general', preferences.language),
      appearance: t('appearance', preferences.language),
      notifications: t('notifications', preferences.language),
      language: t('language', preferences.language),
      dateTime: t('dateTime', preferences.language),
      dangerousZone: t('dangerousZone', preferences.language),
      deleteAccount: t('deleteAccount', preferences.language),
      unavailable: t('unavailable', preferences.language),
    }),
    [preferences.language],
  )

  function chooseTheme(nextTheme) {
    saveTheme(nextTheme)
    setTheme(nextTheme)
    setOpenPanel(null)
  }

  function updatePreference(patch) {
    const next = savePreferences({ ...preferences, ...patch })
    setPreferences(next)
  }

  function updateNotifications(patch) {
    const next = saveNotificationSettings({
      ...notificationSettings,
      ...patch,
    })
    setNotificationSettings(next)
  }

  async function enableBrowserNotifications(enabled) {
    setStatus('')

    if (!enabled) {
      updateNotifications({ browser: false })
      return
    }

    const granted = await requestBrowserNotificationPermission()

    if (!granted) {
      setStatus(
        'Browser notifications were not allowed. In-app notifications can still be used.',
      )
      updateNotifications({ browser: false })
      return
    }

    updateNotifications({ browser: true })
    setStatus('Browser notifications are enabled.')
  }

  function handleTestNotification() {
    const created = sendTestNotification()

    setStatus(
      created
        ? 'A test notification was added. Open the bell icon to view it.'
        : 'Enable in-app or browser notifications first.',
    )
  }

  const activeThemeLabel =
    theme === 'system'
      ? `System (${getEffectiveTheme(theme)})`
      : `${theme[0].toUpperCase()}${theme.slice(1)} theme`

  const notificationSummary = notificationSettings.inApp
    ? 'In-app notifications enabled'
    : notificationSettings.browser
      ? 'Browser notifications enabled'
      : 'Notifications disabled'

  const dateTimeSummary = `${preferences.timeZone} · ${
    preferences.hourCycle === '24' ? '24-hour' : '12-hour'
  } · ${preferences.dateFormat}`

  return (
    <AppShell title={copy.settings} subtitle={copy.subtitle}>
      <section className="settings-panel panel">
        <div className="settings-section-title">{copy.general}</div>

        <button
          type="button"
          className="settings-row settings-row--button"
          onClick={() => setOpenPanel('appearance')}
        >
          <span className="settings-row__icon">
            <Icon name={theme === 'dark' ? 'moon' : 'sun'} size={17} />
          </span>
          <span className="settings-row__copy">
            <strong>{copy.appearance}</strong>
            <small>{activeThemeLabel}</small>
          </span>
          <span className="settings-chevron">›</span>
        </button>

        <button
          type="button"
          className="settings-row settings-row--button"
          onClick={() => {
            setStatus('')
            setOpenPanel('notifications')
          }}
        >
          <span className="settings-row__icon">
            <Icon name="bell" size={17} />
          </span>
          <span className="settings-row__copy">
            <strong>{copy.notifications}</strong>
            <small>{notificationSummary}</small>
          </span>
          <span className="settings-chevron">›</span>
        </button>

        <button
          type="button"
          className="settings-row settings-row--button"
          onClick={() => setOpenPanel('language')}
        >
          <span className="settings-row__icon">
            <Icon name="notes" size={17} />
          </span>
          <span className="settings-row__copy">
            <strong>{copy.language}</strong>
            <small>{getLanguageLabel(preferences.language)}</small>
          </span>
          <span className="settings-chevron">›</span>
        </button>

        <button
          type="button"
          className="settings-row settings-row--button"
          onClick={() => setOpenPanel('date-time')}
        >
          <span className="settings-row__icon">
            <Icon name="clock" size={17} />
          </span>
          <span className="settings-row__copy">
            <strong>{copy.dateTime}</strong>
            <small>{dateTimeSummary}</small>
          </span>
          <span className="settings-chevron">›</span>
        </button>
      </section>

      <section className="settings-panel panel">
        <div className="settings-section-title">{copy.dangerousZone}</div>
        <div className="settings-row danger-row">
          <span className="settings-row__icon">
            <Icon name="trash" size={17} />
          </span>
          <div>
            <strong>{copy.deleteAccount}</strong>
            <small>Account deletion is not enabled yet.</small>
          </div>
          <button disabled className="secondary-button">
            {copy.unavailable}
          </button>
        </div>
      </section>

      {openPanel === 'appearance' && (
        <SettingsModal
          title="Choose appearance"
          description="Your selection is saved on this device."
          onClose={() => setOpenPanel(null)}
          wide
        >
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
        </SettingsModal>
      )}

      {openPanel === 'notifications' && (
        <SettingsModal
          title="Notification preferences"
          description="Choose which ThoughtLinker updates should appear."
          onClose={() => setOpenPanel(null)}
        >
          <div className="settings-modal__body">
            <Toggle
              checked={notificationSettings.inApp}
              onChange={(checked) =>
                updateNotifications({ inApp: checked })
              }
              label="In-app notification center"
              description="Show updates under the bell icon."
            />
            <Toggle
              checked={notificationSettings.browser}
              onChange={enableBrowserNotifications}
              label="Browser notifications"
              description="Show desktop notifications when permission is allowed."
            />

            <div className="settings-subsection-title">Notification types</div>

            <Toggle
              checked={notificationSettings.aiSuggestions}
              onChange={(checked) =>
                updateNotifications({ aiSuggestions: checked })
              }
              label="AI suggestions ready"
              description="When new AI-generated suggestions are available."
            />
            <Toggle
              checked={notificationSettings.brainDump}
              onChange={(checked) =>
                updateNotifications({ brainDump: checked })
              }
              label="Brain Dump completed"
              description="When processing finishes or needs attention."
            />
            <Toggle
              checked={notificationSettings.connections}
              onChange={(checked) =>
                updateNotifications({ connections: checked })
              }
              label="New connections discovered"
              description="When related notes or knowledge links are found."
            />
            <Toggle
              checked={notificationSettings.reminders}
              onChange={(checked) =>
                updateNotifications({ reminders: checked })
              }
              label="Note review reminders"
              description="Optional reminders to revisit saved notes."
            />

            {status && <div className="settings-status">{status}</div>}

            <div className="settings-modal__footer">
              <button
                type="button"
                className="secondary-button"
                onClick={handleTestNotification}
              >
                Send test notification
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => setOpenPanel(null)}
              >
                Done
              </button>
            </div>
          </div>
        </SettingsModal>
      )}

      {openPanel === 'language' && (
        <SettingsModal
          title="Language"
          description="Changes shared navigation and settings labels."
          onClose={() => setOpenPanel(null)}
        >
          <div className="settings-modal__body">
            <div className="settings-choice-list">
              {[
                ['en', 'English', 'English interface labels'],
                ['ur', 'اردو', 'Urdu shared navigation and settings labels'],
              ].map(([id, label, description]) => (
                <button
                  type="button"
                  key={id}
                  className={`settings-choice ${
                    preferences.language === id ? 'is-selected' : ''
                  }`}
                  onClick={() => updatePreference({ language: id })}
                >
                  <span>
                    <strong>{label}</strong>
                    <small>{description}</small>
                  </span>
                  {preferences.language === id && (
                    <Icon name="check" size={18} />
                  )}
                </button>
              ))}
            </div>

            <div className="settings-note">
              Existing note content is not translated. This setting changes
              ThoughtLinker interface labels only.
            </div>

            <div className="settings-modal__footer">
              <button
                type="button"
                className="primary-button"
                onClick={() => setOpenPanel(null)}
              >
                Done
              </button>
            </div>
          </div>
        </SettingsModal>
      )}

      {openPanel === 'date-time' && (
        <SettingsModal
          title="Date and time"
          description="Control how dates and times appear in ThoughtLinker."
          onClose={() => setOpenPanel(null)}
        >
          <div className="settings-modal__body settings-form-grid">
            <label>
              <span>Time zone</span>
              <select
                value={preferences.timeZone}
                onChange={(event) =>
                  updatePreference({ timeZone: event.target.value })
                }
              >
                {TIMEZONES.map((zone) => (
                  <option key={zone} value={zone}>
                    {zone}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Clock format</span>
              <select
                value={preferences.hourCycle}
                onChange={(event) =>
                  updatePreference({ hourCycle: event.target.value })
                }
              >
                <option value="12">12-hour clock</option>
                <option value="24">24-hour clock</option>
              </select>
            </label>

            <label>
              <span>Date format</span>
              <select
                value={preferences.dateFormat}
                onChange={(event) =>
                  updatePreference({ dateFormat: event.target.value })
                }
              >
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              </select>
            </label>

            <div className="settings-date-preview">
              <span>Preview</span>
              <strong>
                {new Intl.DateTimeFormat(
                  preferences.language === 'ur' ? 'ur-PK' : 'en-GB',
                  {
                    timeZone: preferences.timeZone,
                    dateStyle: 'medium',
                    timeStyle: 'short',
                    hour12: preferences.hourCycle === '12',
                  },
                ).format(new Date())}
              </strong>
            </div>

            <div className="settings-modal__footer settings-modal__footer--full">
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  const next = savePreferences(DEFAULT_PREFERENCES)
                  setPreferences(next)
                }}
              >
                Reset defaults
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => setOpenPanel(null)}
              >
                Done
              </button>
            </div>
          </div>
        </SettingsModal>
      )}
    </AppShell>
  )
}

export default SettingsPage
