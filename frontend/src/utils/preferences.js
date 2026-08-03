export const PREFERENCES_STORAGE_KEY = 'thoughtlinker-preferences'

export const DEFAULT_PREFERENCES = {
  language: 'en',
  timeZone:
    typeof Intl !== 'undefined'
      ? Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Karachi'
      : 'Asia/Karachi',
  hourCycle: '12',
  dateFormat: 'DD/MM/YYYY',
}

export function getPreferences() {
  if (typeof window === 'undefined') return DEFAULT_PREFERENCES

  try {
    const saved = JSON.parse(
      window.localStorage.getItem(PREFERENCES_STORAGE_KEY) || '{}',
    )

    return {
      ...DEFAULT_PREFERENCES,
      ...saved,
    }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

export function savePreferences(nextPreferences) {
  const next = {
    ...DEFAULT_PREFERENCES,
    ...nextPreferences,
  }

  window.localStorage.setItem(
    PREFERENCES_STORAGE_KEY,
    JSON.stringify(next),
  )

  document.documentElement.lang = next.language
  document.documentElement.dataset.language = next.language

  window.dispatchEvent(
    new CustomEvent('thoughtlinker-preferences-change', {
      detail: next,
    }),
  )

  return next
}

export function initializePreferences() {
  if (typeof document === 'undefined') return
  const preferences = getPreferences()
  document.documentElement.lang = preferences.language
  document.documentElement.dataset.language = preferences.language
}

export function formatDate(value, preferences = getPreferences()) {
  const date = value instanceof Date ? value : new Date(value)

  if (Number.isNaN(date.getTime())) return ''

  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: preferences.timeZone,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
    .formatToParts(date)
    .reduce((result, part) => {
      if (part.type !== 'literal') result[part.type] = part.value
      return result
    }, {})

  if (preferences.dateFormat === 'MM/DD/YYYY') {
    return `${parts.month}/${parts.day}/${parts.year}`
  }

  if (preferences.dateFormat === 'YYYY-MM-DD') {
    return `${parts.year}-${parts.month}-${parts.day}`
  }

  return `${parts.day}/${parts.month}/${parts.year}`
}
