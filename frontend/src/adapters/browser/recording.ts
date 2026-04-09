export type RecordingStartErrorCode = 'permission-denied' | 'unsupported' | 'start-failed'
export type RecordingSessionState = 'inactive' | 'recording' | 'paused'

export class RecordingStartError extends Error {
  code: RecordingStartErrorCode

  constructor(code: RecordingStartErrorCode, message: string) {
    super(message)
    this.name = 'RecordingStartError'
    this.code = code
  }
}

export interface RecordingSession {
  getState: () => RecordingSessionState
  setOnDataAvailable: (handler: (chunk: BlobPart) => void) => void
  setOnStop: (handler: () => void) => void
  start: (timeslice?: number) => void
  stop: () => void
  dispose: () => void
}

interface CreateRecordingSessionOptions {
  onRealtimePcmChunk?: (pcmBase64: string) => void
}

interface RealtimePipeline {
  teardown: () => void
}

type AudioContextConstructor = typeof AudioContext
type AudioWorkletNodeConstructor = typeof AudioWorkletNode
type AudioWorkletMessagePayload = Float32Array | number[]

const PCM_WORKLET_PROCESSOR_NAME = 'langear-pcm-processor'
const PCM_WORKLET_PROCESSOR_SOURCE = `
class LangearPcmProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0]
    const output = outputs[0]
    const inputChannel = input && input[0]

    if (inputChannel && inputChannel.length) {
      this.port.postMessage(new Float32Array(inputChannel))
      if (output && output[0]) {
        output[0].set(inputChannel)
      }
    }

    return true
  }
}

registerProcessor('${PCM_WORKLET_PROCESSOR_NAME}', LangearPcmProcessor)
`

function stopTracks(stream: MediaStream) {
  stream.getTracks().forEach((track) => track.stop())
}

function resolveAudioContextConstructor(): AudioContextConstructor | null {
  if (typeof window === 'undefined' || typeof window.AudioContext === 'undefined') {
    return null
  }

  return window.AudioContext
}

function resolveAudioWorkletNodeConstructor(): AudioWorkletNodeConstructor | null {
  if (typeof window === 'undefined' || typeof window.AudioWorkletNode === 'undefined') {
    return null
  }

  return window.AudioWorkletNode
}

function isPermissionDeniedError(error: unknown): boolean {
  if (!error || typeof error !== 'object') {
    return false
  }

  const name = 'name' in error && typeof error.name === 'string' ? error.name : ''
  return (
    name === 'NotAllowedError' ||
    name === 'PermissionDeniedError' ||
    name === 'SecurityError'
  )
}

function downsampleFloat32(
  input: Float32Array,
  inputSampleRate: number,
  outputSampleRate: number,
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

  for (let index = 0; index < input.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, input[index] || 0))
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }

  return output
}

function pcm16ToBase64(pcm16: Int16Array): string {
  const bytes = new Uint8Array(pcm16.length * 2)
  const view = new DataView(bytes.buffer)

  for (let index = 0; index < pcm16.length; index += 1) {
    view.setInt16(index * 2, pcm16[index] || 0, true)
  }

  let binary = ''
  const chunkSize = 0x8000

  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))
  }

  return btoa(binary)
}

function normalizeWorkletPcmFrame(payload: unknown): Float32Array {
  if (payload instanceof Float32Array) {
    return payload
  }

  if (Array.isArray(payload)) {
    return new Float32Array(payload)
  }

  return new Float32Array()
}

function createPcmWorkletModuleUrl(): string {
  return URL.createObjectURL(
    new Blob([PCM_WORKLET_PROCESSOR_SOURCE], {
      type: 'application/javascript',
    }),
  )
}

async function createRealtimePipeline(
  stream: MediaStream,
  onRealtimePcmChunk: (pcmBase64: string) => void,
): Promise<RealtimePipeline> {
  const AudioContextCtor = resolveAudioContextConstructor()
  const AudioWorkletNodeCtor = resolveAudioWorkletNodeConstructor()

  if (!AudioContextCtor || !AudioWorkletNodeCtor) {
    throw new RecordingStartError('unsupported', 'AudioContext is not available')
  }

  const audioContext = new AudioContextCtor()
  if (!audioContext.audioWorklet) {
    void audioContext.close()
    throw new RecordingStartError('unsupported', 'AudioWorklet is not available')
  }

  const moduleUrl = createPcmWorkletModuleUrl()
  try {
    await audioContext.audioWorklet.addModule(moduleUrl)
  } finally {
    URL.revokeObjectURL(moduleUrl)
  }

  if (audioContext.state === 'suspended') {
    await audioContext.resume()
  }

  const mediaSourceNode = audioContext.createMediaStreamSource(stream)
  const audioWorkletNode = new AudioWorkletNodeCtor(audioContext, PCM_WORKLET_PROCESSOR_NAME, {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [1],
  })
  const muteGainNode = audioContext.createGain()

  muteGainNode.gain.value = 0
  audioWorkletNode.port.onmessage = (event: MessageEvent<AudioWorkletMessagePayload>) => {
    const inputChannel = normalizeWorkletPcmFrame(event.data)
    const pcm16 = float32ToPcm16(
      downsampleFloat32(inputChannel, audioContext.sampleRate || 48000, 16000),
    )

    if (!pcm16.length) return
    onRealtimePcmChunk(pcm16ToBase64(pcm16))
  }

  mediaSourceNode.connect(audioWorkletNode)
  audioWorkletNode.connect(muteGainNode)
  muteGainNode.connect(audioContext.destination)

  return {
    teardown() {
      audioWorkletNode.port.onmessage = null
      audioWorkletNode.port.close()
      audioWorkletNode.disconnect()
      muteGainNode.disconnect()
      mediaSourceNode.disconnect()
      void audioContext.close()
    },
  }
}

export async function createRecordingSession(
  options: CreateRecordingSessionOptions = {},
): Promise<RecordingSession> {
  if (
    typeof navigator === 'undefined' ||
    !navigator.mediaDevices?.getUserMedia ||
    typeof MediaRecorder === 'undefined'
  ) {
    throw new RecordingStartError('unsupported', 'Recording is not supported')
  }

  let stream: MediaStream

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch (error) {
    if (isPermissionDeniedError(error)) {
      throw new RecordingStartError('permission-denied', 'Microphone permission denied')
    }

    throw new RecordingStartError('start-failed', 'Failed to access microphone')
  }

  const mediaRecorder = new MediaRecorder(stream)
  let realtimePipeline: RealtimePipeline | null = null
  let onDataAvailable: (chunk: BlobPart) => void = () => {}
  let onStop = () => {}
  let disposed = false

  const cleanup = () => {
    realtimePipeline?.teardown()
    realtimePipeline = null
    stopTracks(stream)
  }

  if (options.onRealtimePcmChunk) {
    try {
      realtimePipeline = await createRealtimePipeline(stream, options.onRealtimePcmChunk)
    } catch (error) {
      cleanup()
      if (error instanceof RecordingStartError) {
        throw error
      }
      throw new RecordingStartError('start-failed', 'Failed to initialize recording pipeline')
    }
  }

  mediaRecorder.ondataavailable = (event: BlobEvent) => {
    onDataAvailable(event.data)
  }

  mediaRecorder.onstop = () => {
    cleanup()
    onStop()
  }

  return {
    getState() {
      return mediaRecorder.state
    },
    setOnDataAvailable(handler) {
      onDataAvailable = handler
    },
    setOnStop(handler) {
      onStop = handler
    },
    start(timeslice = 250) {
      try {
        mediaRecorder.start(timeslice)
      } catch {
        cleanup()
        throw new RecordingStartError('start-failed', 'Failed to start recording')
      }
    },
    stop() {
      if (mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }
    },
    dispose() {
      if (disposed) return
      disposed = true

      onDataAvailable = () => {}
      onStop = () => {}

      if (mediaRecorder.state !== 'inactive') {
        mediaRecorder.onstop = () => {
          cleanup()
        }
        mediaRecorder.stop()
        return
      }

      cleanup()
    },
  }
}
