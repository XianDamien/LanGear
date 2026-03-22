import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import OSS from 'ali-oss'
import { getSTSToken } from '@/services/api/study'
import { normalizeOssRegion } from '@/services/ossRegion'
import { buildE2EOssAudioPath, isE2EMode } from '@/utils/e2e'

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
  let audioContext: AudioContext | null = null
  let mediaSourceNode: MediaStreamAudioSourceNode | null = null
  let scriptProcessorNode: ScriptProcessorNode | null = null
  let muteGainNode: GainNode | null = null

  async function startRecording(onRealtimePcmChunk?: (pcmBase64: string) => void): Promise<boolean> {
    if (isE2EMode) {
      const blob = new Blob(['langear-e2e-audio'], { type: 'audio/webm' })
      recordingBlob.value = blob
      if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
      audioUrl.value = URL.createObjectURL(blob)
      isRecording.value = true
      uploadState.value = 'idle'
      uploadProgress.value = 0

      if (onRealtimePcmChunk) {
        window.setTimeout(() => {
          if (isRecording.value) onRealtimePcmChunk('ZTItdGVzdC1wY20=')
        }, 50)
      }

      return true
    }

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

        teardownRealtimePipeline()
        mediaStream?.getTracks().forEach((track) => track.stop())
      }

      if (onRealtimePcmChunk) {
        setupRealtimePipeline(stream, onRealtimePcmChunk)
      }

      // Emit chunk every 250ms for realtime streaming.
      mediaRecorder.start(250)
      isRecording.value = true
      return true
    } catch {
      ElMessage.error('麦克风权限被拒绝')
      return false
    }
  }

  function stopRecording() {
    if (isE2EMode) {
      isRecording.value = false
      return
    }

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      isRecording.value = false
    }
    teardownRealtimePipeline()
  }

  function setupRealtimePipeline(
    stream: MediaStream,
    onRealtimePcmChunk: (pcmBase64: string) => void
  ) {
    teardownRealtimePipeline()
    audioContext = new AudioContext()
    mediaSourceNode = audioContext.createMediaStreamSource(stream)
    scriptProcessorNode = audioContext.createScriptProcessor(4096, 1, 1)
    muteGainNode = audioContext.createGain()
    muteGainNode.gain.value = 0

    scriptProcessorNode.onaudioprocess = (event: AudioProcessingEvent) => {
      const inputChannel = event.inputBuffer.getChannelData(0)
      const pcm16 = float32ToPcm16(
        downsampleFloat32(inputChannel, audioContext?.sampleRate || 48000, 16000)
      )
      if (!pcm16.length) return
      onRealtimePcmChunk(pcm16ToBase64(pcm16))
    }

    mediaSourceNode.connect(scriptProcessorNode)
    scriptProcessorNode.connect(muteGainNode)
    muteGainNode.connect(audioContext.destination)
  }

  function teardownRealtimePipeline() {
    if (scriptProcessorNode) {
      scriptProcessorNode.onaudioprocess = null
      scriptProcessorNode.disconnect()
      scriptProcessorNode = null
    }
    if (muteGainNode) {
      muteGainNode.disconnect()
      muteGainNode = null
    }
    if (mediaSourceNode) {
      mediaSourceNode.disconnect()
      mediaSourceNode = null
    }
    if (audioContext) {
      void audioContext.close()
      audioContext = null
    }
  }

  function downsampleFloat32(
    input: Float32Array,
    inputSampleRate: number,
    outputSampleRate: number
  ): Float32Array {
    if (inputSampleRate === outputSampleRate) return input
    if (outputSampleRate > inputSampleRate) return input

    const sampleRateRatio = inputSampleRate / outputSampleRate
    const outputLength = Math.round(input.length / sampleRateRatio)
    const result = new Float32Array(outputLength)

    let outputOffset = 0
    let inputOffset = 0
    while (outputOffset < outputLength) {
      const nextInputOffset = Math.round((outputOffset + 1) * sampleRateRatio)
      let accumulator = 0
      let count = 0
      for (let index = inputOffset; index < nextInputOffset && index < input.length; index += 1) {
        accumulator += input[index] || 0
        count += 1
      }
      result[outputOffset] = count > 0 ? accumulator / count : 0
      outputOffset += 1
      inputOffset = nextInputOffset
    }

    return result
  }

  function float32ToPcm16(input: Float32Array): Int16Array {
    const output = new Int16Array(input.length)
    for (let i = 0; i < input.length; i += 1) {
      const sample = Math.max(-1, Math.min(1, input[i] || 0))
      output[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
    }
    return output
  }

  function pcm16ToBase64(pcm16: Int16Array): string {
    const bytes = new Uint8Array(pcm16.length * 2)
    const view = new DataView(bytes.buffer)
    for (let i = 0; i < pcm16.length; i += 1) {
      view.setInt16(i * 2, pcm16[i] || 0, true)
    }

    let binary = ''
    const CHUNK = 0x8000
    for (let offset = 0; offset < bytes.length; offset += CHUNK) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + CHUNK))
    }
    return btoa(binary)
  }

  /**
   * 上传音频到 OSS
   */
  async function uploadToOSS(cardId: string, blobOverride?: Blob): Promise<string | null> {
    const blobToUpload = blobOverride ?? recordingBlob.value
    if (!blobToUpload) {
      ElMessage.error('没有录音数据')
      return null
    }

    if (isE2EMode) {
      uploadState.value = 'uploading'
      uploadProgress.value = 100
      const path = buildE2EOssAudioPath(cardId)
      ossAudioPath.value = path
      uploadState.value = 'uploaded'
      return path
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

      const result = await client.put(path, blobToUpload, {
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
    teardownRealtimePipeline()
  }

  onUnmounted(() => {
    teardownRealtimePipeline()
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
