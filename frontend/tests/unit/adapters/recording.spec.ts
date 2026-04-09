import { describe, expect, it, vi } from 'vitest'
import {
  createRecordingSession,
  RecordingStartError,
} from '@/adapters/browser/recording'

describe('createRecordingSession', () => {
  it('streams realtime PCM through AudioWorkletNode', async () => {
    const onRealtimePcmChunk = vi.fn()
    const onDataAvailable = vi.fn()
    const onStop = vi.fn()

    const session = await createRecordingSession({ onRealtimePcmChunk })
    session.setOnDataAvailable(onDataAvailable)
    session.setOnStop(onStop)

    session.start(0)

    await vi.waitFor(() => {
      expect(onRealtimePcmChunk).toHaveBeenCalledWith(expect.any(String))
    })

    session.stop()

    await vi.waitFor(() => {
      expect(onDataAvailable).toHaveBeenCalled()
      expect(onStop).toHaveBeenCalled()
    })
  })

  it('fails when AudioWorkletNode is unavailable', async () => {
    const originalAudioWorkletNode = window.AudioWorkletNode
    vi.stubGlobal('AudioWorkletNode', undefined)
    Object.defineProperty(window, 'AudioWorkletNode', {
      configurable: true,
      value: undefined,
    })

    try {
      await expect(
        createRecordingSession({ onRealtimePcmChunk: vi.fn() }),
      ).rejects.toMatchObject<Partial<RecordingStartError>>({
        code: 'unsupported',
      })
    } finally {
      vi.stubGlobal('AudioWorkletNode', originalAudioWorkletNode)
      Object.defineProperty(window, 'AudioWorkletNode', {
        configurable: true,
        value: originalAudioWorkletNode,
      })
    }
  })
})
