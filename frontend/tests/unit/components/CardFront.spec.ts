import { describe, expect, it } from 'vitest'
import CardFront from '@/components/study/CardFront.vue'
import { mountWithApp } from '../../helpers/mountWithApp'

describe('CardFront', () => {
  it('disables recording while reference audio is playing', async () => {
    const wrapper = mountWithApp(CardFront, {
      props: {
        audioPlaying: true,
        isRecording: false,
        liveTranscript: '',
        userTranscript: '',
        uploadState: 'idle',
        uploadProgress: 0,
      },
    })

    const button = wrapper.get('[data-testid="record-toggle"]')
    expect(button.attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="record-hint"]').text()).toContain(
      '建议完整听完原音频之后再录音',
    )

    await button.trigger('click')
    expect(wrapper.emitted('toggleRecording')).toBeFalsy()
  })

  it('emits recording toggle once playback is idle', async () => {
    const wrapper = mountWithApp(CardFront, {
      props: {
        audioPlaying: false,
        isRecording: false,
        liveTranscript: '',
        userTranscript: '',
        uploadState: 'idle',
        uploadProgress: 0,
      },
    })

    await wrapper.get('[data-testid="record-toggle"]').trigger('click')
    expect(wrapper.emitted('toggleRecording')).toHaveLength(1)
  })
})
