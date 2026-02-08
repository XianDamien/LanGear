import http from '../http'
import type {
  SubmitReviewRequest,
  SubmitReviewResponseAsync,
  PollingResponse,
  STSToken,
  SubmitReviewRequestV1,
  SubmitReviewResponse
} from '@/types/api'

export function getSTSToken() {
  return http.get<STSToken>('/oss/sts-token')
}

export function submitReviewAsync(payload: SubmitReviewRequest) {
  return http.post<SubmitReviewResponseAsync>('/study/submissions', payload)
}

export function pollSubmissionResult(submissionId: number) {
  return http.get<PollingResponse>(`/study/submissions/${submissionId}`)
}

/** @deprecated Use submitReviewAsync instead */
export function submitReview(payload: SubmitReviewRequestV1) {
  return http.post<SubmitReviewResponse>('/study/submissions', payload)
}
