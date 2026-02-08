import http from '../http'
import type { SubmitReviewRequest, SubmitReviewResponse } from '@/types/api'

export function submitReview(payload: SubmitReviewRequest) {
  return http.post<SubmitReviewResponse>('/study/submissions', payload)
}
