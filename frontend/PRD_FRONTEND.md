# LanGear 前端实施文档（Vue 版本）

## 0. 文档定位
- 本文档定义 LanGear 前端实现规格，可直接用于 AI 生成代码。
- 本文档是 `PRD.md` 的前端落地子文档。
- 版本：v2.0（异步架构版本，2026-02-08）。
- 适用范围：`frontend/` 目录全新 Vue 3 实现。历史 React 代码已归档到 `archive/frontend-react/`。
- 设计原则：保留历史 React 版本的 UI 风格与交互流程，仅切换技术栈。

## 1. 目标与约束

### 1.1 目标
实现“听、复述、AI 反馈、复盘、复习”闭环的前端交互，覆盖：
1. Dashboard
2. Library
3. Study Session
4. Card Detail
5. Summary
6. Settings

### 1.2 约束
- 必须遵循无降级原则：关键失败必须阻断流程，不能伪成功。
- 仅支持管理员单用户模型，不实现注册登录流程。
- 仅支持内置教材，不实现自定义上传切分流程。

## 2. 技术栈（固定版本）
- Vue `3.5.25`（Composition API）
- TypeScript `5.9.3`
- Vite `7.2.6`
- Element Plus `2.12.0`
- Pinia `3.0.4`
- Vue Router `4.6.3`
- `lucide-vue-next`
- `ali-oss`（阿里云 OSS SDK，用于前端直接上传音频）
- `@vueuse/core`
- `axios`

**音频处理说明**：
- **MVP 阶段前端直接上传录音到 OSS**（webm/ogg 格式），后端负责格式转换。
- 移除或标注为"后续迭代"：`@ffmpeg/ffmpeg` + `@ffmpeg/core`（保留用于未来视频切分功能）。

注意事项：
- 前端**不直接调用** Gemini 或阿里云 ASR API。所有 AI 评测与语音转写均通过后端异步处理完成。
- **前端职责**：录音 -> 获取 STS 凭证 -> 直接上传音频到 OSS -> 翻面后提交训练请求（oss_audio_path，不带 rating）-> 轮询获取 AI 评测结果 -> 展示反馈与时间戳 -> 用户评分时单独提交 rating（仅用于 FSRS）。
- 原音频播放直接使用 `cards` 返回的 OSS URL（阿里云 OSS 公读地址）。

## 3. 项目结构规范
建议目录结构如下：

```text
frontend/
  src/
    main.ts
    App.vue
    router/
      index.ts
    stores/
      dashboard.ts
      deck.ts
      study.ts
      summary.ts
      settings.ts
    services/
      http.ts
      api/
        dashboard.ts
        decks.ts
        study.ts
        summary.ts
        settings.ts
    views/
      DashboardView.vue
      LibraryView.vue
      StudySessionView.vue
      CardDetailView.vue
      SummaryView.vue
      SettingsView.vue
    components/
      layout/
      dashboard/
      library/
      study/
      summary/
    composables/
      useRecorder.ts
      useAudioPlayer.ts
      useErrorToast.ts
      useHeatmap.ts
    types/
      api.ts
      domain.ts
```

## 4. 路由与页面规格

### 4.1 路由定义
- `/dashboard`：学习概览与任务配置。
- `/library`：教材树浏览与课文入口。
- `/study/:lessonId`：课文训练主流程。
- `/cards/:cardId`：单句反馈详情。
- `/summary/:lessonId`：课级总结。
- `/settings`：系统配置。
- `/` 默认重定向到 `/dashboard`。

### 4.2 页面详细要求

#### DashboardView
展示内容：
- 今日新学数量、今日复习数量、今日完成数量。
- 连续学习天数。
- 学习热力图（近 90 天）。
- “继续上次练习”“继续指定课文”快捷入口。

交互行为：
- 可配置 `daily_new_limit`、`daily_review_limit`。
- 可配置默认教材来源范围（`default_source_scope`）。
- 配置保存成功后，刷新 dashboard 数据。

#### LibraryView
展示内容：
- `source -> unit -> lesson` 树形结构。
- 每个 `lesson` 显示总卡数、已完成数、待复习数。

交互行为：
- 展开/折叠教材树。
- 点击 lesson 进入 `/study/:lessonId`。

#### StudySessionView
正面区域：
- 原音频播放（可重复播放）。
- 录音按钮（开始、暂停、结束）。
- **显示"上传中"加载状态**（录音结束后上传 OSS 时）。

背面区域：
- 原文文本（支持**词级时间戳高亮**和**点击跳转**功能）。
- 译文文本。
- 用户录音播放。
- 用户转写文本（含词级时间戳，点击词可跳转到对应音频位置）。
- AI 单句反馈摘要（**仅文字描述，不包含数值评分**）：
  - 发音评估
  - 完整度评估
  - 流畅度评估
  - 改进建议（**支持关联时间戳**，点击跳转到对应音频位置）

评分区：
- 四个评分按钮：`again | hard | good | easy`。
- **评分在翻面后选择，提交后触发异步处理**。

关键交互顺序（v2.0 异步架构）：
1. 加载当前卡片。
2. 用户录音结束。
3. **前端获取 STS 凭证并直接上传到 OSS**（显示"上传中"状态）。
4. **用户点击翻面后提交训练请求（oss_audio_path），立即返回 submission_id**（不带 rating，尽快产出 AI 反馈）。
5. **前端轮询获取结果（每 1-2 秒）**，显示处理状态（processing/asr_completed/ai_processing）。
6. **收到 completed 状态后展示转写文本、时间戳、AI 反馈**。
7. 用户选择 again/hard/good/easy：**单独提交评分**（评分不影响 AI 反馈，仅用于 FSRS 调度与统计）。
8. 提交评分成功后进入下一张卡片。
9. 课文最后一张卡评分提交成功后跳转 Summary。

#### CardDetailView
展示单句 AI 反馈详情：
- 发音准确度。
- 内容完整度。
- 流畅度。
- 建议改进点。

#### SummaryView
展示课级总结：
- 本课表现总评。
- 高频问题模式。
- 优先改进建议（Top N）。
- “返回课文”“继续下一课”入口。

#### SettingsView
提供系统配置：
- 每日新学数量。
- 每日复习数量。
- 默认教材来源范围。

## 5. Pinia Store 设计

### 5.1 `dashboard` store
状态：
- `stats`
- `streakDays`
- `heatmap`
- `loading`

动作：
- `fetchDashboard()`
- `refreshAfterSettingChange()`

### 5.2 `deck` store
状态：
- `deckTree`
- `selectedSourceId`
- `selectedLessonId`

动作：
- `fetchDeckTree()`
- `selectLesson(lessonId)`

### 5.3 `study` store
状态：
- `lessonId`
- `cards`
- `currentIndex`
- `currentCard`
- `recordingState`（idle/recording/stopped）
- `uploadState`（idle/uploading/uploaded/failed） - **新增**
- `submitState`（idle/submitting/processing/completed/failed） - **扩展**
- `submissionId`（提交后获得的异步任务 ID） - **新增**
- `pollingInterval`（轮询定时器 ID） - **新增**
- `transcriptionTimestamps`（词级时间戳数组） - **新增**
- `lastFeedback`

动作：
- `loadLessonCards(lessonId)`
- `startRecording()`
- `stopRecording()`
- `uploadToOSS()` - **新增**：获取 STS 凭证并上传音频到 OSS
- `submitReview(payload)` - **更新**：提交训练请求，立即返回 submission_id
- `pollResult(submissionId)` - **新增**：轮询获取处理结果
- `stopPolling()` - **新增**：停止轮询
- `jumpToTimestamp(timestamp)` - **新增**：音频跳转到指定时间戳
- `goNextCard()`

### 5.4 `summary` store
状态：
- `summaryData`
- `loading`

动作：
- `fetchSummary(lessonId)`

### 5.5 `settings` store
状态：
- `dailyNewLimit`
- `dailyReviewLimit`
- `defaultSourceScope`
- `saving`

动作：
- `fetchSettings()`
- `saveSettings()`

## 6. API 对接契约（前端视角）

### 6.1 通用规范
- Base URL：`/api/v1`
- Header：`Content-Type: application/json`
- 所有错误统一解析为：
  - `error.code`（机器可读）
  - `error.message`（用户可读）
  - `error.request_id`（追踪）

### 6.2 关键接口映射（v2.0 异步架构）

#### **新增** `GET /oss/sts-token`
**用途**：获取 STS 临时凭证用于前端直接上传音频到 OSS。

**响应**：
```ts
{
  access_key_id: string       // STS.xxx
  access_key_secret: string
  security_token: string
  expiration: string          // ISO 8601 格式
  bucket: string              // langear
  region: string              // oss-cn-shanghai
}
```

#### **更新** `POST /study/submissions`
**用途**：提交训练请求（异步），立即返回 submission_id。

**请求体**：
```ts
{
  lesson_id: number
  card_id: number
  rating: Rating              // 'again' | 'hard' | 'good' | 'easy'
  oss_audio_path: string      // 例如 "recordings/20260208/1001_xxx.wav"
}
```

**响应**（立即返回）：
```ts
{
  submission_id: number
  status: "processing"
}
```

#### **新增** `GET /study/submissions/{id}`
**用途**：轮询获取训练结果。

**响应（processing）**：
```ts
{
  submission_id: number
  status: "processing"
  progress?: "asr_completed" | "ai_processing" | ...
}
```

**响应（completed）**：
```ts
{
  submission_id: number
  status: "completed"
  result_type: "single"
  transcription: {
    text: string
    timestamps: Array<{
      word: string
      start: number
      end: number
    }>
  }
  feedback: {
    pronunciation: string
    completeness: string
    fluency: string
    suggestions: Array<{
      text: string
      target_word?: string
      timestamp?: number
    }>
  }
  srs: {
    state: string
    difficulty: number
    stability: number
    due: string
  }
}
```

**响应（failed）**：
```ts
{
  submission_id: number
  status: "failed"
  error_code: string          // "ASR_TRANSCRIPTION_FAILED" | "AI_FEEDBACK_FAILED"
  error_message: string
}
```

#### 其他接口
- `GET /dashboard` -> Dashboard 数据。
- `GET /decks/tree` -> 教材树。
- `GET /decks/{lessonId}/cards` -> 课文卡片列表。
- `GET /decks/{lessonId}/summary` -> 课级总结。
- `PUT /settings` -> 保存配置。
- `GET /settings` -> 读取配置。

## 7. 音频处理规范（v2.0 异步架构）

### 7.1 录音
- 使用浏览器 `MediaRecorder` 采集音频（默认输出 webm 或 ogg 格式）。
- **MVP 阶段直接上传原始格式到 OSS**，后端负责格式转换。
- 不使用 `@ffmpeg/ffmpeg` 进行前端转码。

### 7.2 OSS 上传流程
1. 录音结束后获取 webm/ogg Blob。
2. 调用 `GET /api/v1/oss/sts-token` 获取 STS 临时凭证。
3. 使用 `ali-oss` SDK + STS 凭证直接上传到 OSS。
4. 生成 OSS 路径（格式：`recordings/{date}/{card_id}_{timestamp}.webm`）。
5. 上传失败时禁止提交训练请求并提示"音频上传失败，请重试"。

**示例代码**：
```ts
const client = new OSS({
  region: stsToken.region,
  accessKeyId: stsToken.access_key_id,
  accessKeySecret: stsToken.access_key_secret,
  stsToken: stsToken.security_token,
  bucket: stsToken.bucket
})

const fileName = `recordings/${date}/${cardId}_${timestamp}.webm`
await client.put(fileName, audioBlob)
```

### 7.3 提交与轮询流程
1. 上传成功后调用 `POST /api/v1/study/submissions` 提交训练请求。
2. 立即收到 `{submission_id, status: "processing"}`。
3. 启动轮询：每 1-2 秒调用 `GET /api/v1/study/submissions/{id}`。
4. 根据 status 处理：
   - `processing` → 显示加载动画（可选：显示 progress 进度）
   - `completed` → 展示转写文本、时间戳、AI 反馈，停止轮询
   - `failed` → 显示错误提示，停止轮询
5. 轮询超时策略：30 秒后停止轮询，显示"处理中，请稍后查看"。

### 7.4 时间戳跳转功能
- 转写文本中的每个词支持点击跳转。
- AI 建议中关联的 `target_word` 支持点击跳转。
- 跳转时调用 `<audio>.currentTime = timestamp`。

**示例代码**：
```ts
const jumpToTimestamp = (timestamp: number) => {
  const audioElement = audioRef.value
  if (audioElement) {
    audioElement.currentTime = timestamp
    audioElement.play()
  }
}
```

### 7.5 播放
- **原音频**：直接使用 `<audio>` 标签播放卡片的 OSS URL（`audio_path` 字段）。
- **用户录音**：使用 OSS 签名 URL 播放（从 STS 凭证生成）或播放本地 Blob URL。
- 播放失败时展示错误提示，不影响已完成记录读取。

## 8. 错误处理与无降级规则（v2.0 异步架构）

### 8.1 OSS 上传失败
- 禁止提交训练请求，停留当前卡并提示"音频上传失败，请重试"。

### 8.2 训练提交失败（非 200）
- 禁止开始轮询，提示错误信息。

### 8.3 轮询获取到 `status=failed`
- 显示 `error_code` 和 `error_message`，禁止进入下一卡。
- 示例提示："ASR 转写失败：超时，请重试"。

### 8.4 轮询超时（30 秒）
- 停止轮询但不阻塞，显示"处理中，请稍后在历史记录中查看"。
- 允许用户继续下一张卡片（可选行为）。

### 8.5 课级总结加载失败
- 禁止标记课文完成，提供"重试生成"按钮。

### 8.6 设置保存失败
- 保持表单原值并提示失败原因。

## 9. 类型定义（最低要求 - v2.0 异步架构）

### 9.1 评分枚举
`type Rating = 'again' | 'hard' | 'good' | 'easy'`

### 9.2 STS Token（新增）
```ts
interface STSToken {
  access_key_id: string
  access_key_secret: string
  security_token: string
  expiration: string
  bucket: string
  region: string
}
```

### 9.3 Review 提交请求（更新）
```ts
interface SubmitReviewRequest {
  lesson_id: number
  card_id: number
  rating: Rating
  oss_audio_path: string      // 例如 "recordings/20260208/1001_xxx.wav"
}
```

### 9.4 Review 提交响应（更新 - 立即返回）
```ts
interface SubmitReviewResponse {
  submission_id: number
  status: 'processing'
}
```

### 9.5 Submission 结果（新增 - 轮询获取）
```ts
interface SubmissionResponse {
  submission_id: number
  status: 'processing' | 'completed' | 'failed'
  progress?: string           // "asr_completed" | "ai_processing" | ...
  result_type?: 'single'
  transcription?: {
    text: string
    timestamps: Array<{
      word: string
      start: number
      end: number
    }>
  }
  feedback?: {
    pronunciation: string
    completeness: string
    fluency: string
    suggestions: Array<{
      text: string
      target_word?: string
      timestamp?: number
    }>
  }
  srs?: {
    state: string
    difficulty: number
    stability: number
    due: string
  }
  error_code?: string         // "ASR_TRANSCRIPTION_FAILED" | "AI_FEEDBACK_FAILED"
  error_message?: string
}
```

**重要变更**：
- 移除 `feedback.overallScore` 字段（不再包含数值评分）。
- 新增 `transcription.timestamps` 数组（词级时间戳）。
- 新增 `suggestions[].target_word` 和 `suggestions[].timestamp`（支持跳转）。

## 10. MVP 验收测试（前端 - v2.0 异步架构）
1. 可从 Library 进入 lesson 并完成全部卡片。
2. **可成功获取 STS 凭证并上传音频到 OSS**。
3. **训练提交后立即返回 submission_id，轮询能正常工作**。
4. **能看到 processing → completed 的状态变化过程**（可选：显示 progress）。
5. **转写文本包含词级时间戳，点击可跳转音频位置**。
6. **AI 建议关联时间戳，点击可跳转到对应位置**。
7. **AI 反馈不包含数值评分，仅展示文字描述**（pronunciation/completeness/fluency/suggestions）。
8. **ASR 或 AI 失败时能看到明确的 error_code 和 error_message**。
9. 任意关键失败（上传/反馈/总结）都会阻断流程且提示明确。
10. 完成最后一张卡后自动跳转并展示 Summary。
11. Settings 修改后 Dashboard 统计口径实时生效。

## 11. 实施顺序建议（v2.0 异步架构）
1. 初始化 Vue + TypeScript + Vite 工程骨架。
2. 完成 Router 与基础 Layout。
3. 完成 `decks/tree` 与 `lesson/cards` 页面流。
4. **实现录音与异步训练流程**：
   - 4.1 实现 OSS STS 凭证获取与音频上传
   - 4.2 实现训练提交与轮询机制
   - 4.3 实现转写文本与时间戳展示
   - 4.4 实现音频跳转功能
   - 4.5 实现 AI 反馈展示（无数值评分）
5. 实现 Summary 页与 Settings 页。
6. 完成错误路径联调与验收。
