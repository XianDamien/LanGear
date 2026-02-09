# LanGear PRD（沟通简版基线）

> 版本：V0.1（对外沟通基线）  
> 更新日期：2026-02-09  
> 适用阶段：当前迭代（MVP 到可稳定联调）

---

## 1. 需求背景

1. **闭环先跑**：当前项目核心价值是“听-说-评-复习”闭环，先把主链路稳定跑通，优先于功能扩展。  
2. **统一口径**：前后端已有能力存在字段和流程不一致，需先统一业务口径，降低联调和沟通成本。  
3. **便于协作**：需要一份轻量、可快速对齐的文档，方便与产品/设计/开发同步当前阶段目标与边界。

---

## 2. 需求概述

当前阶段聚焦 5 个页面模块：`Dashboard`、`Library`、`Study`、`Summary`、`Settings`。  
目标是完成“可选课-可训练-可拿到 AI 反馈-可保存设置-可看基础统计”的最小可用版本，并明确哪些功能已落地、哪些为下一阶段。

### 当前阶段流程图（基线）

```text
[Dashboard/Library]
       ↓ 选择 lesson
[Study 正面]
  播放原音 + 录音
       ↓（当前实现：停止录音即上传 OSS）
[OSS 上传]
   ├─ 失败 → 提示重试
   └─ 成功 → 翻面
       ↓
[Study 背面评分]
  POST /study/submissions
       ↓
[后端异步处理]
  OSS签名URL → ASR → Gemini → FSRS
       ↓
[前端轮询结果]
  GET /study/submissions/{id}
       ↓
[单句反馈展示]
       ↓
[课级总结]
  当前：前端占位/Mock（后端真实接口待补）
```

---

## 3. 优先级划分（可索引到实现模块）

### P0（必须做，联调可用）

- **P0-01 训练主链路闭环**（Study）
- **P0-02 题库与卡片读取**（Library + Study）
- **P0-03 设置读写打通**（Settings）
- **P0-04 Dashboard 口径统一**（Dashboard）

### P1（重要，提升可用性）

- **P1-01 课级总结真实化**（Summary）
- **P1-02 卡片详情接真实数据**（CardDetail）
- **P1-03 错误处理与重试完善**（Study/Network）

### P2（可选，体验增强）

- **P2-01 排行榜等运营展示真实化**（Dashboard）
- **P2-02 埋点与数据看板补全**（全链路）

### 优先级索引表（模块定位）

| 优先级ID | 需求项 | 页面模块 | 前端实现模块 | 后端实现模块 |
|---|---|---|---|---|
| P0-01 | 训练主链路闭环 | Study | `frontend/src/views/StudySessionView.vue`、`frontend/src/composables/useRecorder.ts`、`frontend/src/stores/study.ts` | `backend/app/routers/study.py`、`backend/app/services/review_service.py`、`backend/app/tasks/review_task.py` |
| P0-02 | 题库与卡片读取 | Library/Study | `frontend/src/views/LibraryView.vue`、`frontend/src/stores/deck.ts` | `backend/app/routers/decks.py`、`backend/app/services/content_service.py` |
| P0-03 | 设置读写打通 | Settings | `frontend/src/views/SettingsView.vue`、`frontend/src/stores/settings.ts` | `backend/app/routers/settings.py`、`backend/app/services/settings_service.py` |
| P0-04 | Dashboard 口径统一 | Dashboard | `frontend/src/views/DashboardView.vue`、`frontend/src/stores/dashboard.ts` | `backend/app/routers/dashboard.py`、`backend/app/services/dashboard_service.py` |
| P1-01 | 课级总结真实化 | Summary | `frontend/src/views/SummaryView.vue`、`frontend/src/stores/summary.ts`、`frontend/src/services/api/summary.ts` | （待新增）`/api/v1/decks/{lesson_id}/summary` 对应 router/service |
| P1-02 | 卡片详情真实化 | CardDetail | `frontend/src/views/CardDetailView.vue` | （待新增）按 `card_id` 查询反馈详情接口 |
| P1-03 | 错误与重试完善 | Study | `frontend/src/components/study/CardFront.vue`、`frontend/src/views/StudySessionView.vue` | `backend/app/routers/study.py`（错误码）、`backend/app/tasks/review_task.py`（失败回写） |
| P2-01 | 排行榜真实化 | Dashboard | `frontend/src/components/dashboard/Leaderboard.vue` | （待评估）新增统计接口 |
| P2-02 | 埋点补全 | 全模块 | `frontend/src/views/*`、`frontend/src/stores/*` | （待评估）埋点采集/日志侧模块 |

---

## 4. 需求详情

### 4.1 交互逻辑 / AI 需求

#### 4.1.1 当前实现口径（As-Is）

- 录音上传触发点在“停止录音”阶段（不是翻面触发）。
- 提交评测后采用轮询获取结果，后端异步执行 ASR + Gemini + FSRS。
- 单句反馈已具备词级时间戳，支持回听跳转。
- 课级总结页存在，但后端真实 summary API 尚未接入。

#### 4.1.2 目标口径（To-Be，按优先级推进）

- P0：先保证“录音上传成功 → 可提交 → 可轮询完成/失败 → 可展示反馈”。
- P1：补齐课级总结真实生成与失败重试机制。
- P1：收紧前端守卫（未录音/未上传不得进入后续流程）。

> 评审建议：本节配一张飞书画板流程图 + 1 张竞品截图（或 1 张低保真原型）作为沟通附件。

### 4.2 功能详情（按页面模块）

| 页面模块 | 功能 | 具体内容（当前阶段） | 状态 | 对应优先级 |
|---|---|---|---|---|
| Dashboard | 学习统计展示 | 展示今日目标/完成、连续天数、热力图、最近课程入口 | ⚠️ 前后端字段口径待统一 | P0-04 |
| Library | 题库树浏览 | 按 source-unit-lesson 展示，支持进入学习页 | ✅ 已接真实接口 | P0-02 |
| Study-正面 | 听音+录音+上传 | 播放原音，录音后上传 OSS，展示上传进度 | ✅ 主流程可用（触发点待收敛） | P0-01 / P1-03 |
| Study-背面 | 评分+轮询反馈 | 提交 `submission`，轮询 completed/failed，展示 AI 反馈与时间戳 | ✅ 已接真实接口 | P0-01 |
| Summary | 课级总结 | 当前有页面与 store，但依赖的 summary API 未落地 | ❌ 待开发 | P1-01 |
| Settings | 配置管理 | 每日新学/复习数量、默认范围配置 | ⚠️ 字段命名与类型映射待统一 | P0-03 |
| CardDetail | 反馈详情 | 当前为前端静态示例数据展示 | ❌ 待开发 | P1-02 |

### 4.3 埋点需求（建议最小集）

| 埋点位置 | 事件名称 | 触发时机 | 参数 |
|---|---|---|---|
| Study 正面 | `record_start` | 点击开始录音 | `lesson_id`, `card_id` |
| Study 正面 | `upload_result` | OSS 上传成功/失败 | `lesson_id`, `card_id`, `status`, `cost_ms` |
| Study 背面 | `review_submit` | 点击评分提交 | `lesson_id`, `card_id`, `rating` |
| Study 背面 | `review_result` | 轮询拿到 completed/failed | `submission_id`, `status`, `error_code` |
| Summary | `summary_view` | 进入课级总结页 | `lesson_id`, `has_data` |
| Settings | `settings_save` | 点击保存设置 | `daily_new_limit`, `daily_review_limit`, `scope_type` |

---

## 5. 关键验收点

✅ **核心功能验收（P0）**

- [ ] Library 可加载课程树并进入 Study。
- [ ] Study 可完成“录音上传 → 提交评测 → 轮询结果 → 展示反馈”。
- [ ] 单句反馈展示包含 `transcription.timestamps` 并可点击跳转音频。
- [ ] Settings 的前后端字段命名、类型、保存回显一致。
- [ ] Dashboard 的接口返回结构与前端渲染结构一致。

✅ **边界情况验收**

- [ ] OSS 上传失败时有明确提示，且允许重试。
- [ ] 轮询超时时不阻塞用户并给出可理解提示。
- [ ] 后端返回 `failed` 时，前端展示 `error_code`/`error_message`。
- [ ] 空数据（无课程/无统计）时页面可正常兜底展示。

✅ **性能与稳定性验收（基线）**

- [ ] 非 AI 场景接口（decks/settings/dashboard）响应通常 < 500ms（本地联调口径）。
- [ ] 评测链路支持异步，不阻塞页面主线程交互。
- [ ] 连续提交多张卡片时，submission 状态可稳定追踪。

---

## 附：当前阶段已知差距（用于沟通对齐）

1. `Summary` 页依赖接口 `/decks/{lesson_id}/summary` 尚未在后端开放。  
2. `Dashboard` 前端期望字段与后端当前返回结构存在差异。  
3. `Settings` 前端使用 camelCase + 字符串 scope，后端当前是 snake_case + 列表 scope。  
4. Study 页部分守卫为临时放开状态（TODO 注释），需在联调稳定后收紧。  

---

## 附：本次最小重构说明（2026-02-09）

- 重构范围：`Study` 前端链路（store/view/component）+ 后端 `ContentService` 结构整理 + `Deck` 语义增强。  
- 变更原则：不改接口，不改流程，不改数据库，仅做类型收敛与函数拆分。  
- 预期收益：降低 `any` 和嵌套复杂度，便于后续在不破坏行为的前提下继续迭代。  
