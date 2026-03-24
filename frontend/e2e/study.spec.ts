import { expect, test, type Page } from '@playwright/test'

const transcript = 'The quick brown fox jumps over the lazy dog.'

async function installSpeechSynthesisMock(page: Page) {
  await page.addInitScript(() => {
    let activeUtterance: SpeechSynthesisUtterance | null = null

    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: {
        speak(utterance: SpeechSynthesisUtterance) {
          activeUtterance = utterance
          window.setTimeout(() => {
            utterance.onstart?.(new Event('start') as SpeechSynthesisEvent)
          }, 0)
        },
        cancel() {
          if (!activeUtterance) return
          const utterance = activeUtterance
          activeUtterance = null
          utterance.onend?.(new Event('end') as SpeechSynthesisEvent)
        },
        pause() {},
        resume() {},
        speaking: false,
        pending: false,
        paused: false,
        getVoices() {
          return []
        },
        addEventListener() {},
        removeEventListener() {},
        dispatchEvent() {
          return true
        },
        onvoiceschanged: null,
      } satisfies Partial<SpeechSynthesis>,
    })
  })
}

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

test('原音频播放时不能开始录音，播放结束后才能录音', async ({ page }) => {
  await installSpeechSynthesisMock(page)
  await page.goto('/study/l1')

  const playReferenceAudio = page.getByTestId('play-reference-audio')
  const recordToggle = page.getByTestId('record-toggle')

  await expect(page.getByTestId('card-front')).toBeVisible()

  await playReferenceAudio.click()

  await recordToggle.click()
  await expect(recordToggle).toContainText('录音')
  await expect(page.getByText('建议完整听完原音频之后再录音')).toBeVisible()

  await page.evaluate(() => {
    window.speechSynthesis.cancel()
  })

  await recordToggle.click()
  await expect(recordToggle).toContainText('停止')
})

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
