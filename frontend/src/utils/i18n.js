const translations = {
  en: {
    dashboard: 'Dashboard',
    newNote: 'New note',
    creating: 'Creating…',
    brainDump: 'Brain Dump',
    allNotes: 'All Notes',
    search: 'Search',
    tags: 'Tags',
    collections: 'Collections',
    aiSuggestions: 'AI Suggestions',
    modelRouting: 'Model Routing',
    knowledgeGraph: 'Knowledge Graph',
    settings: 'Settings',
    settingsSubtitle: 'Personalize your workspace',
    general: 'General',
    appearance: 'Appearance',
    notifications: 'Notifications',
    language: 'Language',
    dateTime: 'Date and time',
    dangerousZone: 'Dangerous zone',
    deleteAccount: 'Delete account',
    unavailable: 'Unavailable',
    quickCapture: 'Quick capture',
    quickCaptureText: 'Thoughts do not need to be perfect.',
    logOut: 'Log out',
    dashboardSubtitle: 'Your knowledge, organized and connected.',
  },
  ur: {
    dashboard: 'ڈیش بورڈ',
    newNote: 'نیا نوٹ',
    creating: 'بن رہا ہے…',
    brainDump: 'برین ڈمپ',
    allNotes: 'تمام نوٹس',
    search: 'تلاش',
    tags: 'ٹیگز',
    collections: 'کلیکشنز',
    aiSuggestions: 'اے آئی تجاویز',
    modelRouting: 'ماڈل روٹنگ',
    knowledgeGraph: 'نالج گراف',
    settings: 'ترتیبات',
    settingsSubtitle: 'اپنی ورک اسپیس کو ذاتی بنائیں',
    general: 'عمومی',
    appearance: 'ظاہری شکل',
    notifications: 'اطلاعات',
    language: 'زبان',
    dateTime: 'تاریخ اور وقت',
    dangerousZone: 'خطرناک زون',
    deleteAccount: 'اکاؤنٹ حذف کریں',
    unavailable: 'دستیاب نہیں',
    quickCapture: 'فوری تحریر',
    quickCaptureText: 'خیالات کا مکمل ہونا ضروری نہیں۔',
    logOut: 'لاگ آؤٹ',
    dashboardSubtitle: 'آپ کا علم، منظم اور مربوط۔',
  },
}

export function t(key, language = 'en') {
  return translations[language]?.[key] || translations.en[key] || key
}

export function getLanguageLabel(language) {
  return language === 'ur' ? 'اردو' : 'English'
}
