export function parseNumericIdOrThrow(
  rawValue: string | number | null | undefined,
  label: string,
): number {
  const numeric = Number(String(rawValue ?? '').replace(/\D/g, ''))

  if (!Number.isInteger(numeric) || numeric <= 0) {
    throw new Error(`无效的${label}`)
  }

  return numeric
}
