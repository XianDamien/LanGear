import { describe, expect, it } from 'vitest'
import { resolveUseMockMode } from '@/config/runtimeFlags'

function createStorage(initialValue: string | null = null) {
  let value = initialValue
  return {
    getItem() {
      return value
    },
    setItem(_key: string, nextValue: string) {
      value = nextValue
    },
    removeItem() {
      value = null
    },
  }
}

describe('resolveUseMockMode', () => {
  it('prefers env flag when explicitly enabled', () => {
    const storage = createStorage(null)
    expect(resolveUseMockMode('true', '', storage)).toBe(true)
  })

  it('persists querystring override to storage', () => {
    const storage = createStorage(null)
    expect(resolveUseMockMode('false', '?mock=true', storage)).toBe(true)
    expect(resolveUseMockMode('false', '', storage)).toBe(true)
  })

  it('clears persisted mock mode when querystring disables it', () => {
    const storage = createStorage('true')
    expect(resolveUseMockMode('false', '?mock=false', storage)).toBe(false)
    expect(resolveUseMockMode('false', '', storage)).toBe(false)
  })
})
