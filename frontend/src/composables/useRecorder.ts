import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export function useRecorder() {
  const isRecording = ref(false)
  const recordingBlob = ref<Blob | null>(null)
  const audioUrl = ref<string | null>(null)
  const audioBase64 = ref<string | null>(null)

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

        // Convert to base64 for submission
        await convertToBase64(blob)

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

  async function convertToBase64(blob: Blob) {
    try {
      // For MVP, we submit the webm directly as base64
      // Full implementation would use @ffmpeg/ffmpeg for wav conversion
      const reader = new FileReader()
      const result = await new Promise<string>((resolve, reject) => {
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1]
          if (base64) resolve(base64)
          else reject(new Error('base64 conversion failed'))
        }
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
      audioBase64.value = result
    } catch {
      ElMessage.error('音频处理失败，请重试')
      audioBase64.value = null
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
  }
}
