export const NOTIFICATION_SETTINGS_KEY =
  'thoughtlinker-notification-settings'
export const NOTIFICATIONS_KEY = 'thoughtlinker-notifications'

export const DEFAULT_NOTIFICATION_SETTINGS = {
  inApp: true,
  browser: false,
  aiSuggestions: true,
  brainDump: true,
  connections: true,
  reminders: false,
}

export function getNotificationSettings() {
  if (typeof window === 'undefined') {
    return DEFAULT_NOTIFICATION_SETTINGS
  }

  try {
    return {
      ...DEFAULT_NOTIFICATION_SETTINGS,
      ...JSON.parse(
        window.localStorage.getItem(NOTIFICATION_SETTINGS_KEY) || '{}',
      ),
    }
  } catch {
    return DEFAULT_NOTIFICATION_SETTINGS
  }
}

export function saveNotificationSettings(settings) {
  const next = {
    ...DEFAULT_NOTIFICATION_SETTINGS,
    ...settings,
  }

  window.localStorage.setItem(
    NOTIFICATION_SETTINGS_KEY,
    JSON.stringify(next),
  )

  window.dispatchEvent(
    new CustomEvent('thoughtlinker-notification-settings-change', {
      detail: next,
    }),
  )

  return next
}

export function getNotifications() {
  if (typeof window === 'undefined') return []

  try {
    return JSON.parse(
      window.localStorage.getItem(NOTIFICATIONS_KEY) || '[]',
    )
  } catch {
    return []
  }
}

function writeNotifications(items) {
  window.localStorage.setItem(
    NOTIFICATIONS_KEY,
    JSON.stringify(items.slice(0, 20)),
  )

  window.dispatchEvent(
    new CustomEvent('thoughtlinker-notifications-change', {
      detail: items.slice(0, 20),
    }),
  )
}

export function addNotification({
  type = 'general',
  title,
  message,
  href = '',
}) {
  const settings = getNotificationSettings()

  if (!settings.inApp && !settings.browser) return null
  if (type === 'ai' && !settings.aiSuggestions) return null
  if (type === 'brainDump' && !settings.brainDump) return null
  if (type === 'connection' && !settings.connections) return null
  if (type === 'reminder' && !settings.reminders) return null

  const item = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    title,
    message,
    href,
    createdAt: new Date().toISOString(),
    read: false,
  }

  if (settings.inApp) {
    writeNotifications([item, ...getNotifications()])
  }

  if (
    settings.browser &&
    typeof Notification !== 'undefined' &&
    Notification.permission === 'granted'
  ) {
    new Notification(title, {
      body: message,
    })
  }

  return item
}

export function markAllNotificationsRead() {
  const next = getNotifications().map((item) => ({
    ...item,
    read: true,
  }))
  writeNotifications(next)
  return next
}

export function clearNotifications() {
  writeNotifications([])
}

export async function requestBrowserNotificationPermission() {
  if (typeof Notification === 'undefined') return false
  if (Notification.permission === 'granted') return true
  if (Notification.permission === 'denied') return false

  return (await Notification.requestPermission()) === 'granted'
}

export function sendTestNotification() {
  return addNotification({
    type: 'general',
    title: 'ThoughtLinker notifications are ready',
    message:
      'You will see AI suggestions, Brain Dump updates, connections, and enabled reminders here.',
  })
}
