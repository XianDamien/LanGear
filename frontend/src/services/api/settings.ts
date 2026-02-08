import http from '../http'
import type { SettingsData } from '@/types/api'

export function fetchSettings() {
  return http.get<SettingsData>('/settings')
}

export function saveSettings(data: SettingsData) {
  return http.put<SettingsData>('/settings', data)
}
