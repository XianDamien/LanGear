import type { Component } from 'vue'
import { createTestingPinia, type TestingOptions } from '@pinia/testing'
import { mount, type MountingOptions } from '@vue/test-utils'
import { vi } from 'vitest'

interface MountWithAppOptions<T> extends MountingOptions<T> {
  pinia?: TestingOptions
}

export function mountWithApp<T = unknown>(component: Component, options: MountWithAppOptions<T> = {}) {
  const { pinia, global, ...rest } = options
  const testingPinia = createTestingPinia({
    createSpy: vi.fn,
    ...pinia,
  })

  return mount(component, {
    ...rest,
    global: {
      ...global,
      plugins: [testingPinia, ...(global?.plugins ?? [])],
    },
  })
}
