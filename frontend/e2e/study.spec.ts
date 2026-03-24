import { expect, test } from '@playwright/test'
import { installBrowserMocks } from './helpers/installBrowserMocks'

const transcript = 'The quick brown fox jumps over the lazy dog.'
const transcriptPattern = /The\s*quick\s*brown\s*fox\s*jumps\s*over\s*the\s*lazy\s*dog\./

async function completeFirstStudyCard(page: import('@playwright/test').Page) {
  await page.goto('/study/1001')

  await expect(page.getByTestId('study-session-view')).toBeVisible()
  await expect(page.getByTestId('study-lesson-title')).toContainText('Lesson 1')
  await expect(page.getByTestId('task-nav-item-1')).toBeVisible()
  await expect(page.getByTestId('card-front')).toBeVisible()

  await page.getByTestId('record-toggle').click()
  await expect(page.getByTestId('record-toggle')).toContainText('停止')
  await expect(page.getByTestId('live-transcript')).toContainText(transcript)

  await page.getByTestId('record-toggle').click()
  await expect(page.getByTestId('record-toggle')).toContainText('录音')

  await page.getByTestId('flip-button').click()

  await expect(page.getByTestId('card-back')).toBeVisible()
  await expect(page.getByTestId('task-nav-status-1')).toContainText(/评测中|完成/)
  await expect(page.getByTestId('feedback-panel')).toContainText('AI 评测反馈')
}

test('核心学习链路可以在 Mock E2E 模式下完成评测并展示反馈', async ({ page }) => {
  await installBrowserMocks(page)
  await completeFirstStudyCard(page)

  await expect(page.getByTestId('feedback-panel')).toContainText('发音整体清晰', {
    timeout: 15_000,
  })
  await expect(page.getByTestId('transcription-result')).toContainText(transcriptPattern)
  await expect(page.getByTestId('task-nav-status-1')).toContainText('完成')
})
