export const THEME_STORAGE_KEY = 'thoughtlinker-theme'
export const THEMES = ['light', 'dark', 'system']

let systemThemeCleanup = null

function normalizeTheme(theme) {
  return THEMES.includes(theme) ? theme : 'light'
}

export function getSavedTheme() {
  if (typeof window === 'undefined') {
    return 'light'
  }

  return normalizeTheme(
    window.localStorage.getItem(THEME_STORAGE_KEY) || 'light',
  )
}

export function getEffectiveTheme(theme = getSavedTheme()) {
  const normalizedTheme = normalizeTheme(theme)

  if (normalizedTheme !== 'system') {
    return normalizedTheme
  }

  if (typeof window === 'undefined') {
    return 'light'
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

export function applyTheme(theme) {
  const preference = normalizeTheme(theme)
  const effectiveTheme = getEffectiveTheme(preference)
  const root = document.documentElement

  root.setAttribute('data-theme', effectiveTheme)
  root.setAttribute('data-theme-preference', preference)
  root.classList.toggle('theme-dark', effectiveTheme === 'dark')
  root.classList.toggle('theme-light', effectiveTheme === 'light')
  root.style.colorScheme = effectiveTheme

  return {
    theme: preference,
    effectiveTheme,
  }
}

function emitThemeChange(theme, effectiveTheme) {
  window.dispatchEvent(
    new CustomEvent('thoughtlinker-theme-change', {
      detail: {
        theme,
        effectiveTheme,
      },
    }),
  )
}

export function saveTheme(theme) {
  const preference = normalizeTheme(theme)

  window.localStorage.setItem(THEME_STORAGE_KEY, preference)

  const result = applyTheme(preference)
  emitThemeChange(result.theme, result.effectiveTheme)

  return result.theme
}

export function initializeTheme() {
  if (typeof window === 'undefined') {
    return
  }

  const savedTheme = getSavedTheme()
  applyTheme(savedTheme)

  if (systemThemeCleanup) {
    systemThemeCleanup()
  }

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handleSystemThemeChange = () => {
    if (getSavedTheme() !== 'system') {
      return
    }

    const result = applyTheme('system')
    emitThemeChange(result.theme, result.effectiveTheme)
  }

  if (typeof mediaQuery.addEventListener === 'function') {
    mediaQuery.addEventListener('change', handleSystemThemeChange)
    systemThemeCleanup = () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange)
    }
  } else {
    mediaQuery.addListener(handleSystemThemeChange)
    systemThemeCleanup = () => {
      mediaQuery.removeListener(handleSystemThemeChange)
    }
  }
}
