import http from '../http'
import type { SettingsData } from '@/types/api'

interface BackendSettingsData {
  daily_new_limit?: number
  daily_review_limit?: number
  default_source_scope?: unknown
}

function parseDefaultSourceScope(value: string): number[] {
  const normalized = value.trim()
  if (!normalized) return []

  return normalized
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0)
}

function toFrontendSettings(data: BackendSettingsData): SettingsData {
  return {
    dailyNewLimit: typeof data.daily_new_limit === 'number' ? data.daily_new_limit : 10,
    dailyReviewLimit: typeof data.daily_review_limit === 'number' ? data.daily_review_limit : 30,
    defaultSourceScope: Array.isArray(data.default_source_scope)
      ? data.default_source_scope.join(',')
      : '',
  }
}

function toBackendSettings(data: SettingsData): BackendSettingsData {
  return {
    daily_new_limit: data.dailyNewLimit,
    daily_review_limit: data.dailyReviewLimit,
    default_source_scope: parseDefaultSourceScope(data.defaultSourceScope),
  }
}

export async function fetchSettings() {
  const response = await http.get<BackendSettingsData>('/settings')
  return {
    ...response,
    data: toFrontendSettings(response.data),
  }
}

export async function saveSettings(data: SettingsData) {
  const response = await http.put<BackendSettingsData>('/settings', toBackendSettings(data))
  return {
    ...response,
    data: toFrontendSettings(response.data),
  }
}
