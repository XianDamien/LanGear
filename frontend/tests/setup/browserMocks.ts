import { vi } from 'vitest'
import { browserMockContract } from './browserMockContract'

let installed = false

export function installBrowserMocks() {
  if (installed) {
    return
  }

  installed = true

  class MockSpeechSynthesisUtterance {
    text: string
    lang = 'en-US'
    rate = 1
    onstart: ((event: SpeechSynthesisEvent) => void) | null = null
    onend: ((event: SpeechSynthesisEvent) => void) | null = null
    onerror: ((event: SpeechSynthesisErrorEvent) => void) | null = null

    constructor(text: string) {
      this.text = text
    }
  }

  class MockAudio {
    src: string
    currentTime = 0
    onplay: ((event: Event) => void) | null = null
    onended: ((event: Event) => void) | null = null
    onerror: ((event: Event) => void) | null = null
    private isPlaying = false

    constructor(src = '') {
      this.src = src
    }

    play = vi.fn(async () => {
      this.isPlaying = true
      this.onplay?.(new Event('play'))
    })

    pause = vi.fn(() => {
      if (!this.isPlaying) {
        return undefined
      }

      this.isPlaying = false
      this.onended?.(new Event('ended'))
      return undefined
    })
  }

  class MockMediaRecorder {
    static readonly isTypeSupported = vi.fn(() => true)

    state: RecordingState = 'inactive'
    ondataavailable: ((event: BlobEvent) => void) | null = null
    onstop: ((event: Event) => void) | null = null
    private chunkEmitted = false

    constructor(stream: MediaStream) {
      void stream
    }

    start(timeslice = 0) {
      this.state = 'recording'
      window.setTimeout(() => {
        if (this.state !== 'recording' || this.chunkEmitted) {
          return
        }

        this.chunkEmitted = true
        this.ondataavailable?.({
          data: new Blob([browserMockContract.audioBlobText], {
            type: browserMockContract.audioMimeType,
          }),
        } as BlobEvent)
      }, timeslice)
    }

    stop() {
      if (this.state === 'inactive') {
        return
      }

      this.state = 'inactive'
      if (!this.chunkEmitted) {
        this.chunkEmitted = true
        this.ondataavailable?.({
          data: new Blob([browserMockContract.audioBlobText], {
            type: browserMockContract.audioMimeType,
          }),
        } as BlobEvent)
      }

      this.onstop?.(new Event('stop'))
    }
  }

  class MockAudioContext {
    sampleRate = 48000
    destination = {} as AudioDestinationNode

    createMediaStreamSource() {
      return {
        connect() {
          return undefined
        },
        disconnect() {
          return undefined
        },
      } as MediaStreamAudioSourceNode
    }

    createScriptProcessor() {
      const processor = {
        onaudioprocess: null as ((event: AudioProcessingEvent) => void) | null,
        connect() {
          window.setTimeout(() => {
            processor.onaudioprocess?.({
              inputBuffer: {
                getChannelData: () => new Float32Array(browserMockContract.pcmFrame),
              },
            } as AudioProcessingEvent)
          }, 0)
          return undefined
        },
        disconnect() {
          return undefined
        },
      }

      return processor as unknown as ScriptProcessorNode
    }

    createGain() {
      return {
        gain: { value: 1 },
        connect() {
          return undefined
        },
        disconnect() {
          return undefined
        },
      } as GainNode
    }

    close = vi.fn(async () => undefined)
  }

  let activeUtterance: MockSpeechSynthesisUtterance | null = null
  const speechSynthesis = {
    speak: vi.fn((utterance: MockSpeechSynthesisUtterance) => {
      activeUtterance = utterance
      window.setTimeout(() => {
        utterance.onstart?.(new Event('start') as SpeechSynthesisEvent)
      }, 0)
    }),
    cancel: vi.fn(() => {
      if (!activeUtterance) {
        return
      }

      const utterance = activeUtterance
      activeUtterance = null
      utterance.onend?.(new Event('end') as SpeechSynthesisEvent)
    }),
    pause: vi.fn(() => undefined),
    resume: vi.fn(() => undefined),
    speaking: false,
    pending: false,
    paused: false,
    getVoices: vi.fn(() => []),
    addEventListener: vi.fn(() => undefined),
    removeEventListener: vi.fn(() => undefined),
    dispatchEvent: vi.fn(() => true),
    onvoiceschanged: null,
  } satisfies Partial<SpeechSynthesis>

  vi.stubGlobal('SpeechSynthesisUtterance', MockSpeechSynthesisUtterance)
  vi.stubGlobal('Audio', MockAudio)
  vi.stubGlobal('MediaRecorder', MockMediaRecorder)
  vi.stubGlobal('AudioContext', MockAudioContext)

  Object.defineProperty(window, 'speechSynthesis', {
    configurable: true,
    value: speechSynthesis,
  })

  Object.defineProperty(window, 'webkitAudioContext', {
    configurable: true,
    value: MockAudioContext,
  })

  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: {
      getUserMedia: vi.fn(async () => ({
        getTracks: () => [
          {
            stop: vi.fn(() => undefined),
          },
        ],
      })),
    },
  })
}
