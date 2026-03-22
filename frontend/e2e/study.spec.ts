import { expect, test, type Page } from '@playwright/test'

const transcript = 'The quick brown fox jumps over the lazy dog.'

async function completeFirstStudyCard(page: Page) {
  await page.goto('/study/l1')

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
  await completeFirstStudyCard(page)

  await expect(page.getByTestId('feedback-panel')).toContainText('发音整体清晰', {
    timeout: 15_000,
  })
  await expect(page.getByTestId('transcription-result')).toContainText(transcript)
  await expect(page.getByTestId('task-nav-status-1')).toContainText('完成')
})

test('已完成任务在切卡后仍然保留状态与反馈内容', async ({ page }) => {
  await completeFirstStudyCard(page)
  await expect(page.getByTestId('feedback-panel')).toContainText('发音整体清晰', {
    timeout: 15_000,
  })

  await page.getByTestId('task-nav-item-2').click()
  await expect(page.getByTestId('task-nav-status-1')).toContainText('完成')
  await expect(page.getByTestId('card-front')).toBeVisible()
  await expect(page.getByTestId('study-lesson-title')).toContainText('2')

  await page.getByTestId('task-nav-item-1').click()
  await expect(page.getByTestId('card-back')).toBeVisible()
  await expect(page.getByTestId('task-nav-status-1')).toContainText('完成')
  await expect(page.getByTestId('feedback-panel')).toContainText('发音整体清晰')
  await expect(page.getByTestId('transcription-result')).toContainText(transcript)
})
