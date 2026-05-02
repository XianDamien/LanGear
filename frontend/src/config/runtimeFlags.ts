const MOCK_STORAGE_KEY = 'langear-use-mock'

interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

export function resolveUseMockMode(
  envUseMock: string | undefined,
  locationSearch: string,
  storage?: StorageLike,
): boolean {
  if (envUseMock === 'true') {
    return true
  }

  if (!storage) {
    return false
  }

  const searchParams = new URLSearchParams(locationSearch)
  const searchValue = searchParams.get('mock')

  if (searchValue === 'true') {
    storage.setItem(MOCK_STORAGE_KEY, 'true')
    return true
  }

  if (searchValue === 'false') {
    storage.removeItem(MOCK_STORAGE_KEY)
    return false
  }

  return storage.getItem(MOCK_STORAGE_KEY) === 'true'
}

export function getUseMockMode(): boolean {
  if (typeof window === 'undefined') {
    return resolveUseMockMode(import.meta.env.VITE_USE_MOCK, '', undefined)
  }

  return resolveUseMockMode(
    import.meta.env.VITE_USE_MOCK,
    window.location.search,
    window.localStorage,
  )
}
