import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import OSS from 'ali-oss'
import { getSTSToken } from '@/services/api/study'
import { normalizeOssRegion } from '@/services/ossRegion'

export function useRecorder() {
  const isRecording = ref(false)
  const recordingBlob = ref<Blob | null>(null)
  const audioUrl = ref<string | null>(null)
  const audioBase64 = ref<string | null>(null)

  const uploadState = ref<'idle' | 'uploading' | 'uploaded' | 'failed'>('idle')
  const ossAudioPath = ref<string | null>(null)
  const uploadProgress = ref(0)

  let mediaRecorder: MediaRecorder | null = null
  let mediaStream: MediaStream | null = null
  let chunks: BlobPart[] = []

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStream = stream
      mediaRecorder = new MediaRecorder(stream)
      chunks = []

      mediaRecorder.ondataavailable = (e) => {
        chunks.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        recordingBlob.value = blob

        // Create local playback URL
        if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
        audioUrl.value = URL.createObjectURL(blob)

        mediaStream?.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      isRecording.value = true
    } catch {
      ElMessage.error('麦克风权限被拒绝')
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      isRecording.value = false
    }
  }

  /**
   * 上传音频到 OSS
   */
  async function uploadToOSS(cardId: string): Promise<string | null> {
    if (!recordingBlob.value) {
      ElMessage.error('没有录音数据')
      return null
    }

    uploadState.value = 'uploading'
    uploadProgress.value = 0

    try {
      const { data: stsToken } = await getSTSToken()

      const client = new OSS({
        region: normalizeOssRegion(stsToken.region),
        accessKeyId: stsToken.access_key_id,
        accessKeySecret: stsToken.access_key_secret,
        stsToken: stsToken.security_token,
        bucket: stsToken.bucket,
        secure: true,
        refreshSTSToken: async () => {
          const { data: newToken } = await getSTSToken()
          return {
            accessKeyId: newToken.access_key_id,
            accessKeySecret: newToken.access_key_secret,
            stsToken: newToken.security_token
          }
        }
      })

      const timestamp = Date.now()
      const dateStr = new Date().toISOString().split('T')[0]?.replace(/-/g, '') ?? ''
      const filename = `${cardId}_${timestamp}.webm`
      const path = `recordings/${dateStr}/${filename}`

      const result = await client.put(path, recordingBlob.value, {
        progress: (p: number) => {
          uploadProgress.value = Math.round(p * 100)
        }
      } as any) // ali-oss types 可能不完整，使用 any

      if (result?.res?.status === 200) {
        ossAudioPath.value = path
        uploadState.value = 'uploaded'
        return path
      } else {
        throw new Error(`Upload failed with status ${result?.res?.status ?? 'unknown'}`)
      }
    } catch (error) {
      console.error('OSS upload failed:', error)
      uploadState.value = 'failed'

      const origin = typeof window !== 'undefined' ? window.location.origin : ''
      const rawMessage = error instanceof Error ? error.message : String(error)
      const isLikelyCors = /CORS|Access-Control-Allow-Origin|preflight|ERR_FAILED/i.test(rawMessage)
      if (isLikelyCors && origin) {
        ElMessage.error(`音频上传失败：OSS CORS 未放行（请在 OSS 控制台允许 ${origin}）`)
      } else {
        ElMessage.error('音频上传失败，请重试')
      }
      return null
    }
  }

  function reset() {
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
      audioUrl.value = null
    }
    recordingBlob.value = null
    audioBase64.value = null
    isRecording.value = false

    uploadState.value = 'idle'
    ossAudioPath.value = null
    uploadProgress.value = 0
  }

  onUnmounted(() => {
    if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
    mediaStream?.getTracks().forEach((track) => track.stop())
  })

  return {
    isRecording,
    recordingBlob,
    audioUrl,
    audioBase64,
    startRecording,
    stopRecording,
    reset,
    uploadState,
    ossAudioPath,
    uploadProgress,
    uploadToOSS
  }
}
