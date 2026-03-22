const DEFAULT_APP_TIMEZONE = 'Asia/Shanghai'

const formatterCache = new Map<string, Intl.DateTimeFormat>()

function getFormatter(timeZone: string): Intl.DateTimeFormat {
  const cached = formatterCache.get(timeZone)
  if (cached) return cached

  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZoneName: 'shortOffset',
  })
  formatterCache.set(timeZone, formatter)
  return formatter
}

function getParts(date: Date, timeZone: string): Record<string, string> {
  const parts = getFormatter(timeZone).formatToParts(date)
  return Object.fromEntries(parts.map((part) => [part.type, part.value]))
}

function normalizeOffset(rawOffset: string | undefined): string {
  if (!rawOffset || rawOffset === 'GMT') return '+00:00'

  const trimmed = rawOffset.replace('GMT', '')
  const sign = trimmed.startsWith('-') ? '-' : '+'
  const body = trimmed.replace(/^[-+]/, '')

  if (!body) return '+00:00'
  if (body.includes(':')) return `${sign}${body}`
  if (body.length <= 2) return `${sign}${body.padStart(2, '0')}:00`
  return `${sign}${body.slice(0, 2)}:${body.slice(2, 4)}`
}

export function getBusinessTimezone(): string {
  return DEFAULT_APP_TIMEZONE
}

export function formatBusinessIso(date: Date, timeZone = getBusinessTimezone()): string {
  const parts = getParts(date, timeZone)
  const offset = normalizeOffset(parts.timeZoneName)
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}${offset}`
}

export function formatBusinessDate(date: Date, timeZone = getBusinessTimezone()): string {
  const parts = getParts(date, timeZone)
  return `${parts.year}-${parts.month}-${parts.day}`
}

export function formatBusinessDateStamp(date: Date, timeZone = getBusinessTimezone()): string {
  const parts = getParts(date, timeZone)
  return `${parts.year}${parts.month}${parts.day}`
}
