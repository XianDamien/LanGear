import { describe, expect, it, vi } from 'vitest'
import RetroButton from '@/components/ui/RetroButton.vue'
import { mountWithApp } from '../../helpers/mountWithApp'

describe('RetroButton', () => {
  it('forwards disabled state and keeps native button behavior', async () => {
    const onClick = vi.fn()
    const wrapper = mountWithApp(RetroButton, {
      slots: {
        default: 'Record',
      },
      attrs: {
        disabled: true,
        class: 'custom-class',
        'data-testid': 'retro-button',
        onClick,
      },
    })

    const button = wrapper.get('[data-testid="retro-button"]')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.classes()).toContain('disabled:cursor-not-allowed')
    expect(button.classes()).toContain('disabled:opacity-60')
    expect(button.classes()).toContain('disabled:shadow-none')
    expect(button.classes()).toContain('custom-class')

    await button.trigger('click')
    expect(onClick).not.toHaveBeenCalled()
  })
})
