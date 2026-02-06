# Langear MVP 前端实施文档（Vue 版本）

## 0. 文档定位
- 本文档定义 Langear MVP 前端实现规格，可直接用于 AI 生成代码。
- 本文档是 `PRD_MVP.md` 的前端落地子文档。
- 版本：v1.0（2026-02-06）。
- 适用范围：`frontend/` 目录重构迁移（从历史 React 实现迁移到 Vue 3）。

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
- `@ffmpeg/ffmpeg` + `@ffmpeg/core`
- `@vueuse/core`
- `axios`
- `crypto-js`

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

背面区域：
- 原文文本（支持词块高亮）。
- 译文文本。
- 用户录音播放。
- 用户转写文本。
- AI 单句反馈摘要。

评分区：
- 四个评分按钮：`again | hard | good | easy`。

关键交互顺序：
1. 加载当前卡片。
2. 用户录音结束。
3. 提交录音和评分到后端。
4. 收到单句反馈后才允许进入下一张卡片。
5. 课文最后一张卡提交成功后跳转 Summary。

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
- `submitState`（idle/submitting/success/failed）
- `lastFeedback`

动作：
- `loadLessonCards(lessonId)`
- `startRecording()`
- `stopRecording()`
- `submitReview(payload)`
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

### 6.2 关键接口映射
- `GET /dashboard` -> Dashboard 数据。
- `GET /decks/tree` -> 教材树。
- `GET /decks/{lessonId}/cards` -> 课文卡片列表。
- `POST /study/submissions` -> 提交单卡评分与音频，返回单句反馈。
- `GET /decks/{lessonId}/summary` -> 课级总结。
- `PUT /settings` -> 保存配置。
- `GET /settings` -> 读取配置。

## 7. 音频处理规范

### 7.1 录音
- 使用浏览器 `MediaRecorder` 采集音频。
- 推荐上传前统一编码为 `wav` 或 `webm`（由后端统一解析）。

### 7.2 音频预处理
- 使用 `@ffmpeg/ffmpeg` 与 `@ffmpeg/core` 执行前端必要预处理（可选）。
- 处理失败时禁止提交评分并提示“音频处理失败”。

### 7.3 播放
- 原音频、用户录音均支持播放与暂停。
- 播放失败时展示错误提示，不影响已完成记录读取。

## 8. 错误处理与无降级规则
- 音频上传失败：禁止完成卡片，停留当前卡并提示重试。
- AI 单句反馈失败：禁止进入下一卡，提示“反馈生成失败，请重试”。
- 课级总结加载失败：禁止标记课文完成，提供“重试生成”按钮。
- 设置保存失败：保持表单原值并提示失败原因。

## 9. 类型定义（最低要求）

### 9.1 评分枚举
`type Rating = 'again' | 'hard' | 'good' | 'easy'`

### 9.2 Review 提交请求
```ts
interface SubmitReviewRequest {
  lessonId: number
  cardId: number
  rating: Rating
  userAudio: string
  audioFormat: 'wav' | 'webm' | 'mp3'
}
```

### 9.3 Review 提交响应
```ts
interface SubmitReviewResponse {
  reviewLogId: number
  resultType: 'single'
  feedback: {
    pronunciation: string
    completeness: string
    fluency: string
    suggestions: string[]
  }
}
```

## 10. MVP 验收测试（前端）
1. 可从 Library 进入 lesson 并完成全部卡片。
2. 每张卡提交后都能看到单句反馈并成功进入下一张。
3. 任意关键失败（上传/反馈/总结）都会阻断流程且提示明确。
4. 完成最后一张卡后自动跳转并展示 Summary。
5. Settings 修改后 Dashboard 统计口径实时生效。

## 11. 实施顺序建议
1. 初始化 Vue + TypeScript + Vite 工程骨架。
2. 完成 Router 与基础 Layout。
3. 完成 `decks/tree` 与 `lesson/cards` 页面流。
4. 实现录音与 `study/submissions` 提交流。
5. 实现 Summary 页与 Settings 页。
6. 完成错误路径联调与验收。
