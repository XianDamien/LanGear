export function normalizeOssRegion(region: string): string {
  const trimmed = region.trim()

  // ali-oss expects regions like `oss-cn-shanghai`.
  if (trimmed.startsWith('oss-')) return trimmed

  // Some backends mistakenly return Aliyun region id like `cn-shanghai`.
  // Convert that to the OSS form.
  if (trimmed.startsWith('cn-')) return `oss-${trimmed}`

  return trimmed
}

