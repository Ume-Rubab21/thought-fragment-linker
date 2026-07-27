import AppShell from '../components/AppShell'
import Icon from '../components/Icon'

const rows = [
  ['Appearance', 'Light theme', 'sun'],
  ['Editor', 'Rich text editor', 'edit'],
  ['Notifications', 'In-app only', 'bell'],
  ['Language', 'English', 'notes'],
  ['Date and time', Intl.DateTimeFormat().resolvedOptions().timeZone, 'clock'],
]

function SettingsPage() {
  return (
    <AppShell title="Settings" subtitle="Personalize your workspace">
      <section className="settings-panel panel">
        <div className="settings-section-title">General</div>
        {rows.map(([label, value, icon]) => (
          <div className="settings-row" key={label}>
            <span className="settings-row__icon"><Icon name={icon} size={17} /></span>
            <div><strong>{label}</strong><small>{value}</small></div>
            <span className="settings-chevron">›</span>
          </div>
        ))}
      </section>
      <section className="settings-panel panel">
        <div className="settings-section-title">Dangerous zone</div>
        <div className="settings-row danger-row">
          <span className="settings-row__icon"><Icon name="trash" size={17} /></span>
          <div><strong>Delete account</strong><small>Not enabled in the Day 4 build.</small></div>
          <button disabled className="secondary-button">Unavailable</button>
        </div>
      </section>
    </AppShell>
  )
}

export default SettingsPage
