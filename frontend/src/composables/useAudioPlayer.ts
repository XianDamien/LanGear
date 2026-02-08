import { ref } from 'vue'

export function useAudioPlayer() {
  const isPlaying = ref(false)
  let currentAudio: HTMLAudioElement | null = null

  function play(src: string) {
    stop()

    if (src) {
      currentAudio = new Audio(src)
      currentAudio.onplay = () => (isPlaying.value = true)
      currentAudio.onended = () => (isPlaying.value = false)
      currentAudio.onerror = () => (isPlaying.value = false)
      currentAudio.play().catch(() => {
        // Fallback to SpeechSynthesis if audio URL fails
        isPlaying.value = false
      })
    }
  }

  function speakText(text: string, lang = 'en-US') {
    stop()
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    utterance.rate = 0.9
    utterance.onstart = () => (isPlaying.value = true)
    utterance.onend = () => (isPlaying.value = false)
    utterance.onerror = () => (isPlaying.value = false)
    window.speechSynthesis.speak(utterance)
  }

  function stop() {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    window.speechSynthesis.cancel()
    isPlaying.value = false
  }

  return { isPlaying, play, speakText, stop }
}
