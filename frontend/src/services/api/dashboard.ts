import http from '../http'
import type { DashboardData } from '@/types/api'

export function fetchDashboard() {
  return http.get<DashboardData>('/dashboard')
}
