import OSS from 'ali-oss'
import http from '../http'
import type {
  SubmitReviewRequest,
  SubmitReviewResponseAsync,
  PollingResponse,
  STSToken,
  SubmitRatingRequest,
  SubmitRatingResponse,
  SubmitReviewRequestV1,
  SubmitReviewResponse
} from '@/types/api'

export function getSTSToken() {
  return http.get<STSToken>('/oss/sts-token')
}

/**
 * Generate a signed URL for an OSS audio path via STS credentials.
 * Used for user recordings playback when blob URL is unavailable.
 */
export async function getOSSSignedUrl(ossPath: string): Promise<string> {
  const { data: sts } = await getSTSToken()
  const client = new OSS({
    region: sts.region,
    accessKeyId: sts.access_key_id,
    accessKeySecret: sts.access_key_secret,
    stsToken: sts.security_token,
    bucket: sts.bucket,
  })
  return client.signatureUrl(ossPath, { expires: 3600 })
}

export function submitReviewAsync(payload: SubmitReviewRequest) {
  return http.post<SubmitReviewResponseAsync>('/study/submissions', payload)
}

export function submitRating(submissionId: number, payload: SubmitRatingRequest) {
  return http.post<SubmitRatingResponse>(`/study/submissions/${submissionId}/rating`, payload)
}

export function pollSubmissionResult(submissionId: number) {
  return http.get<PollingResponse>(`/study/submissions/${submissionId}`)
}

/** @deprecated Use submitReviewAsync instead */
export function submitReview(payload: SubmitReviewRequestV1) {
  return http.post<SubmitReviewResponse>('/study/submissions', payload)
}
