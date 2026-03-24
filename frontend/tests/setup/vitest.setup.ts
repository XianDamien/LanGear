import { afterEach, beforeEach, vi } from 'vitest'
import { installBrowserMocks } from './browserMocks'

installBrowserMocks()

beforeEach(() => {
  vi.clearAllMocks()
  window.sessionStorage.clear()
  window.localStorage.clear()
})

afterEach(() => {
  document.body.innerHTML = ''
})
