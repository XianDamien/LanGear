export interface PlaybackCallbacks {
  onStart?: () => void
  onEnd?: () => void
  onError?: () => void
}

export interface AudioPlaybackHandle {
  play: () => Promise<void>
  stop: () => void
}

function resolveSpeechSynthesis(): SpeechSynthesis | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return null
  }

  return window.speechSynthesis
}

export function createAudioPlayback(
  src: string,
  callbacks: PlaybackCallbacks = {},
): AudioPlaybackHandle {
  const audio = new Audio(src)

  audio.onplay = () => callbacks.onStart?.()
  audio.onended = () => callbacks.onEnd?.()
  audio.onerror = () => callbacks.onError?.()

  return {
    async play() {
      await audio.play()
    },
    stop() {
      audio.pause()
      audio.currentTime = 0
    },
  }
}

export function createSpeechPlayback(
  text: string,
  options: PlaybackCallbacks & { lang?: string; rate?: number } = {},
): AudioPlaybackHandle {
  const speechSynthesis = resolveSpeechSynthesis()
  const utterance = new SpeechSynthesisUtterance(text)

  utterance.lang = options.lang ?? 'en-US'
  utterance.rate = options.rate ?? 0.9
  utterance.onstart = () => options.onStart?.()
  utterance.onend = () => options.onEnd?.()
  utterance.onerror = () => options.onError?.()

  return {
    async play() {
      if (!speechSynthesis) {
        options.onError?.()
        return
      }

      speechSynthesis.cancel()
      speechSynthesis.speak(utterance)
    },
    stop() {
      speechSynthesis?.cancel()
    },
  }
}

export function cancelSpeechPlayback() {
  resolveSpeechSynthesis()?.cancel()
}
