# LanGear PRD（应然基线）

> 版本：V0.5（To-Be 规范版）  
> 更新日期：2026-03-22  
> 适用阶段：MVP 到可稳定联调
> 文档维护约束：当项目行为、命令、约束发生变化时，同步更新 `README.md`；当产品流程、契约、状态模型或验收标准变化时，同步更新 `PRD.md` 与 `PRD_BASELINE.md`。`docs/prd_versions/` 当前仅对 `PRD.md` 做版本镜像与归档，更新 `PRD.md` 后需执行 `python3 scripts/prd_version_manager.py sync`。`CLAUDE.md` 为 `AGENTS.md` 的软链接，以 `AGENTS.md` 为准。

---

## 1. 产品目标

LanGear 必须提供“听-说-评-复习”的完整学习闭环，确保用户可以稳定完成：

1. 进入课程并选择卡片；
2. 听音并完成录音；
3. 获得 AI 评测反馈；
4. 基于反馈进行复习和下一轮学习；
5. 在设置与统计页获得一致且可用的数据体验。

---

## 2. 范围与流程

本阶段页面范围固定为：`Dashboard`、`Library`、`Study`、`Summary`、`Settings`。

> 备注：`Queue/Tasks` 为进入 `Study` 学习模式后的全局模块，用于跨卡片查看状态与跳转，不作为独立页面。第一阶段先复用现有顶部任务导航承载该能力，不要求首批改成右上角下拉列表。

### 2.0 术语与状态定义（联调口径）

为避免“课程/lesson/deck”等混用导致的歧义，本 PRD 在接口与埋点口径上统一使用以下术语：

- `deck`：课程/课包单位（本期统一使用 `deck_id`）。
- `card`：卡片单位（本期统一使用 `card_id`）。
- `card_state`：卡片对外学习状态字段，仅表达 FSRS 原生状态：
  - `learning`：FSRS 原生状态，处于学习步骤；`last_review IS NULL` 的初始卡也以该状态持久化
  - `review`：FSRS 原生状态，进入间隔复习阶段
  - `relearning`：FSRS 原生状态，遗忘后进入再学习阶段
- `new card`：业务筛卡桶，不是 `card_state/state` 枚举值；主判定口径为 `last_review IS NULL`
- `realtime_session`：一次学习录音对应的实时转写会话（提交评测时统一使用 `realtime_session_id`）。
  - 只有当 `realtime_session` 已完成且存在最终转写文本时，才允许创建 `submission`。
- `submission`：一次“翻面触发上传”所产生的提交记录（本期统一使用 `submission_id`）。
  - 一张卡片可以有多次 `submission`（历史保留），但学习流程只消费“最后一次有效录音”。
  - 学习页恢复任务状态时，最近 submission 历史以 `review_log` 为真源，按 `created_at desc, id desc` 取最新记录。
- `Queue/Tasks`：学习模式下的跨卡片任务列表视图；展示任务状态并提供跳转，不承载业务逻辑。
- `北京时间时钟`：全站单实例固定使用 `Asia/Shanghai`。
  - 历史数据迁移基准固定为北京时间。
  - 当前不支持每用户独立时区，不在 `users` 表新增 timezone 字段，也不开放运行时改时区。

状态字段建议在接口/模型中以如下枚举表示（字段名可实现调整，但语义与枚举值需保持一致）：

- 卡片状态 `card_state`：`learning` / `review` / `relearning`
- 上传状态 `upload_status`：`uploading` / `succeeded` / `failed`
- AI 处理状态 `review_status`：`processing` / `completed` / `failed`

约束：
- 对外 `card_state` 与数据库 `user_card_srs.state` 一致，只允许 `learning/review/relearning`；“新卡”通过 `is_new_card`、`new_cards`、`last_review_at` 等派生字段表达。
- UI 文案层可将 `review`/`relearning` 统一展示为“复习中”，但接口与存储保持 FSRS 原始枚举。
- `upload_status != succeeded` 时，该卡片不得进入评测/反馈结果阶段；但不应阻塞用户继续切卡练习。
- `upload_status == succeeded` 且 `realtime_session` 已 ready 后，才允许创建 `submission` 并进入 `review_status` 状态流转。

### 2.1 目标流程（总览）

```text
[Dashboard/Library]
       ↓ 选择 deck/card
[Study 正面]
  听音 + 录音（本地缓存）+ 实时转写会话
       ↓ 翻面触发上传
[OSS 上传 succeeded + realtime_session ready]
       ↓ 创建 submission
[Gemini 双音频反馈 + 评分解耦的学习调度]
       ↓
[结果获取 completed/failed]
       ↓
[卡片反馈（单句） + 课级总结]
       ↓
[复习与下一次学习]
```

### 2.2 用户流程（按页面规范化）

#### 0) 学习模式全局模块：`Queue/Tasks`（跨卡片状态，不绑定正反面）

0.1 进入 `Study` 学习模式后，右上角提供“队列/任务”入口（下拉列表形式），用于跨卡片查看“上传/AI 处理”状态。
0.2 队列列表至少包含：`deck_id`、`card_id`、`submission_id`（如有）、`upload_status`、`review_status`、更新时间、失败原因（`error_code`/`error_message`）。
0.3 队列列表提供跳转能力：`completed` 可跳转到对应卡片背面；`failed` 可跳转到对应卡片正面重新录制并重走上传流程。上传未成功时：该卡片不得进入评测/反馈结果阶段，但不应阻塞用户继续练习或切换到上一张/下一张。
0.4 队列仅承担“状态查询与导航”，不应与某张卡片的正面/背面强绑定。

#### 1) `Dashboard` / `Library`（选课与进入学习）

1.1 用户在 `Dashboard` 或 `Library` 浏览课程树（`source-unit-deck`）并进入指定 `deck`。
1.2 用户选择卡片并进入 `Study`。

#### 2) `Study`（正面：播放与录音、本地缓存、实时转写、翻面上传）

2.1 用户在 `Study` 正面执行“播放原音 → 跟读录音”，可重复多次。
2.2 录音过程中，前端需维护对应的 `realtime_session_id` 并持续接收实时转写结果；最终展示给用户的转录文本以该实时转写会话的 `final_text` 为准。
2.3 每次录音文件仅保存在浏览器本地缓存中；同一卡片仅保留**最后一次有效录音**（覆盖策略明确且可追踪）。
2.4 用户点击“翻面/查看答案”瞬间，系统读取最后一次有效录音并立即上传到 OSS。
2.4.1 OSS 命名与版本：需要保留有时间戳的历史版本；再次遇到某个卡片，对应录音上传的命名由翻面瞬间的时间戳来命名。
2.4.2 上传状态：上传过程中必须展示状态（上传中/成功/失败）；状态入口统一在右上角 `Queue/Tasks` 中跨卡片查看。未上传成功前：该卡片不得进入评测/反馈结果阶段，但不应阻塞用户继续练习或切换到上一张/下一张。
2.4.3 只有在 `upload_status == succeeded` 且 `realtime_session_id` 对应会话已 ready 时，系统才允许创建 `submission`。若实时转写未完成或失败，应阻断该次评测提交，并提示用户重试或重新录制。
2.4.4 若前置校验失败导致 `submission` 未创建，前端仍需保留当前卡背面，并直接展示后端返回的真实 `error_code` / `error_message`，不能退回统一失败文案，也不能让用户误以为“翻面成功但没保存”。
2.5 卡片导航：卡片区域需提供左右切换按钮（上一张/下一张），并保留“跳过/搁置”等快捷操作；上述导航不应被异步评测阻塞。

#### 3) `Study`（背面：音频 / 文本 / 反馈 / 笔记）

3.1 创建 `submission` 后，系统必须**即刻**触发后台 AI 反馈流程，不允许人工二次触发。当前基线口径为：使用卡片原音频 + 用户录音的双音频输入调用 `CardFeedbackAI`；实时转写会话仍作为提交前置条件校验，但展示给用户的转录文本改由 Gemini 直接生成。
3.2 上传状态与 AI 处理状态统一在右上角 `Queue/Tasks` 模块中查看（跨卡片列表，不与某张卡片正反面强绑定）。
3.2.1 进入 lesson、刷新页面、重新进入学习页时，前端必须主动查询最近 submission 历史并回填 `Queue/Tasks`，不得只依赖本轮前端内存态。
3.3 音频区（顶部）：用户可播放原音频与自己上传成功的练习录音，两者在顶部区域左右分居，且播放器控件样式必须统一；原音频只提供正常播放/暂停/拖动，练习录音在“上传成功”后可播放并支持时间戳定位回听。音频资源访问需要使用 STS（或等价的临时授权方案）。
3.4 文本区（中部）：展示单一紧凑文本框，默认同时展示原文与 Gemini 生成的展示转写；译文默认隐藏，用户可在同一文本框内展开/收起。原文与展示转写按词级机械 diff 呈现，明确标出缺失、替换、冗余。
3.5 反馈与笔记区（底部）：展示 AI 反馈内容，并提供用户自定义笔记的输入/保存区域。卡片反馈最小结构至少包含：`pronunciation`、`completeness`、`fluency`、`suggestions[]`、`issues[]`；其中 `suggestions[]`/`issues[]` 的 `timestamp` 语义统一为“问题发生点”，作为唯一有效的跳转时间戳，且仅作用于练习录音。

#### 4) `Summary`（课级总结触发与查看）

4.1 完成 deck 后，系统在“最后一个卡片的卡片反馈（单句）状态为 `completed`”后**自动触发课级总结生成**。
4.2 生成触发后弹出提示框，提示是否进入 `Summary` 查看课级总结并安排后续复习。

---

## 3. 优先级

### P0（必须达成）

- **P0-01** 训练主链路闭环（Study）
- **P0-02** 题库与卡片读取（Library + Study）
- **P0-03** 设置读写一致（Settings）
- **P0-04** Dashboard 数据口径一致（Dashboard）

### P1（应尽快达成）

- **P1-01** 课级总结生成（Summary）
- **P1-02** 卡片反馈历史（CardDetail，与卡片反馈（单句）同结构）
- **P1-03** 错误处理与重试（Study/Network）

### P2（体验增强）

- **P2-01** 排行榜与运营展示（Dashboard）
- **P2-02** 埋点与数据看板补全（全链路）

---

## 4. 功能需求

### 4.1 交互与处理规范

1. 录音仅存于浏览器本地缓存，且同一卡片仅保留最后一次有效录音。
2. 翻面动作是唯一上传触发点：翻面瞬间上传最后一次录音至 OSS。
3. 翻面后只有在 OSS 上传成功且 `realtime_session_id` 对应会话 ready 时，才允许创建 `submission` 并立刻触发 AI 反馈流程。
4. 状态必须分层展示且语义清晰：上传状态（`uploading`/`succeeded`/`failed`）与 AI 处理状态（`processing`/`completed`/`failed`）不可混用；上传成功前不得进入 AI 处理状态；状态入口以 `Queue/Tasks`（学习模式下拉列表）为准。`review_status=failed` 时，前端必须显示真实 `error_code` 与 `error_message`；`processing` 显示“评测中”；`completed` 显示结果可回看。
5. 未录音、无有效录音、上传失败、`realtime_session_id` 缺失、实时转写未完成或失败等前置条件不满足时，系统必须阻断该卡片的评测/反馈关键链路并提示；但不应阻塞用户继续学习与切换卡片；mock 模式可以暂时不阻塞。前置校验失败时不得创建 `review_log`；若 `review_log` 已创建，则后续状态必须可通过历史接口恢复。
6. 反馈结果必须包含可读文本与时间戳，支持按时间点回听；展示用转录文本来自 Gemini，跳转时间戳仅来自 `feedback.suggestions[]` / `feedback.issues[]`。
7. 系统应支持生成课级总结（P1），最小输出结构为 `overall`、`patterns[]`、`prioritized_actions[]`。
8. OSS 上的音频资源访问需使用 STS（或等价的临时授权/签名方案），避免前端长期暴露静态凭证。
9. 每张卡片必须具备 `card_state`（`learning`/`review`/`relearning`），并通过 `is_new_card` / `last_review_at` 表达是否属于 FSRS 初始卡桶；“新卡”主判定口径为 `last_review IS NULL`。
10. 卡片反馈模块需支持可替换 provider；当前基线默认 `AI_FEEDBACK_PROVIDER=gemini`，并通过 `GEMINI_MODEL_ID` 与 `GEMINI_PROMPT_VERSION` 控制模型与 prompt 版本。
11. Prompt 迭代需支持独立于生产提交流程的离线评测模式：可将已完成单句反馈样本导出到本地 dataset 目录，保存样本元数据、固定输入、历史输出与音频归档；不同 prompt 变体的 run 结果需单独落盘，禁止回写业务 `review_log`。
12. 结构化评测结果与 FSRS 状态的真源必须是 `DATABASE_URL` 指向数据库中的 `review_log` / `user_card_srs` / `fsrs_review_log`；OSS 只存原音频与用户录音，`backend/datasets/` 只允许作为离线导出快照。
13. 数据库中的业务时间统一存储为“北京时间本地 naive datetime”；对外接口统一返回带 `+08:00` 偏移的 ISO 8601，不再输出 `Z`。

### 4.2 页面级需求

| 页面模块 | 功能要求 | 优先级 |
|---|---|---|
| Dashboard | 展示学习目标、完成进度、连续学习、热力图、最近课程入口，且前后端口径一致 | P0-04 |
| Library | 提供 source-unit-deck 树结构浏览，并可进入学习流程 | P0-02 |
| Study-正面 | 支持播放原音、录音、本地缓存覆盖策略、实时转写会话、上一张/下一张切换、跳过/搁置、翻面触发上传与提交校验（状态入口为 `Queue/Tasks`） | P0-01 / P1-03 |
| Study-背面 | 顶部原音/练习录音左右对照播放器（统一控件样式；上传成功后可播练习录音，使用 STS；时间戳仅跳练习录音）、中部单框原文/译文/ Gemini 展示转写机械 diff、底部 AI 反馈（含 `suggestions[]` / `issues[]` 问题点时间戳）+ 笔记 | P0-01 |
| Queue/Tasks（学习模式模块） | 右上角下拉列表跨卡片查看上传/AI 处理状态与失败原因，并提供跳转（completed→背面，failed→正面重录）；可见实时转写/提交前置条件失败的阻断信息 | P0-01 / P1-03 |
| Summary | 提供课级总结结果展示（`overall`、`patterns[]`、`prioritized_actions[]`） | P1-01 |
| Settings | 提供学习配置读取、保存、回显一致性 | P0-03 |
| CardDetail | 提供按 `card_id` 查询并展示历史卡片反馈记录（与卡片反馈（单句）同结构，按时间倒序） | P1-02 |

### 4.3 API 能力要求

1. Study 必须提供提交、结果查询与历史查询能力，支持完整状态流转；提交请求最小集需包含 `lesson_id`、`card_id`、`oss_audio_path`、`realtime_session_id`。历史查询接口为 `GET /api/v1/study/submissions?lesson_id=...&card_id=...`，返回最近 submission 列表，至少包含 `submission_id`、`card_id`、`lesson_id`、`status`、`error_code`、`error_message`、`created_at`、`oss_audio_path`、`transcription`、`feedback`。
1.1 Study 还必须提供 `GET /api/v1/study/session` 以返回当前 session 的 `scope`、`quota`、`summary` 与 `cards[]`，并优先返回 `learning/relearning`、`review` 卡，再补充 FSRS 初始卡桶。每张卡必须返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`；其中 `card_state` 仅允许 `learning/review/relearning`，初始卡的 `due_at` 使用服务端当前时间，`last_review_at` 为 `null`。
1.2 `GET /health`、`GET /api/v1/study/session`、`GET /api/v1/decks/{lesson_id}/cards`、`GET /api/v1/study/submissions*` 与 Dashboard 相关接口中的时间字段统一按北京时间序列化，并输出带 `+08:00` 偏移的 ISO 8601。
2. Summary 必须提供课级汇总接口：`/api/v1/decks/{deck_id}/summary`。
3. Dashboard 与 Settings 的字段命名和类型必须与前端模型一致。
4. 失败结果必须返回可消费的 `error_code` 与 `error_message`；至少覆盖 `REALTIME_SESSION_NOT_FOUND`、`REALTIME_TRANSCRIPT_NOT_READY`、`REALTIME_SESSION_FAILED`、`REFERENCE_AUDIO_NOT_FOUND`、`USER_AUDIO_ACCESS_FAILED`、`AI_FEEDBACK_FAILED`。
5. `Queue/Tasks` 需要支持批量查询任务状态（按 `deck_id` 获取 submissions 列表及其 `upload_status`/`review_status`），用于跨卡片状态列表展示。历史查询结果必须覆盖 `processing` / `failed` / `completed` 三类状态，且以 `review_log` 为真源，不依赖卡片接口里的聚合字段推断。
6. 音频访问需要 STS（或等价的临时授权/签名方案）发放能力（接口形式不限）；后台在 AI 处理阶段需能将用户录音与参考原音频解析为可访问 URL。
7. Deck/卡片读取接口需要返回 `card_state`（`learning`/`review`/`relearning`）、`is_new_card`、`last_review_at`；`GET /api/v1/decks/tree` 的 lesson 节点至少返回 `total_cards`、`completed_cards`、`due_cards`、`new_cards`，且 `completed_cards`= `last_review IS NOT NULL`、`due_cards`= `last_review IS NOT NULL AND due <= now`、`new_cards`= `total_cards - completed_cards`。
7.1 `GET /api/v1/decks/{lesson_id}/cards` 的每张卡必须返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`；不返回原生 `step/stability/difficulty`。
7.2 评分提交接口需接受前端 FSRS 数值评分 `1|2|3|4` 或兼容标签 `again/hard/good/easy`，并统一返回可直接渲染的原生 FSRS 结果；若返回 `srs.state`，仅允许 `learning/review/relearning`，不再返回 `new`。
8. 反馈结果查询接口在 `completed` 时需至少返回：`transcription.text`、`transcription.timestamps`、`feedback.pronunciation`、`feedback.completeness`、`feedback.fluency`、`feedback.suggestions[]`、`feedback.issues[]`、`oss_audio_path`；其中 `transcription.timestamps` 仅为兼容保留空数组，前端有效跳转时间戳来自 `feedback.suggestions[]` 与 `feedback.issues[]`。

### 4.4 AI 模块划分（独立、可替换）

本期将“卡片反馈（单句）/ 课级总结”拆分为独立 AI 模块（可替换实现，避免绑定某一家模型/Prompt）。

#### 4.4.1 模块 A：CardFeedbackAI（卡片反馈（单句），Study 背面 & CardDetail 消费）

- **触发**：`submission` 创建后自动触发（不允许人工二次触发）。
- **输入（当前基线）**：`front_text`、用户录音可访问 URL、卡片原音频可访问 URL；`realtime_session_id` 对应会话的 ready + `final_text` 非空仅作为提交前置条件。
- **输出（最小集）**：卡片反馈结构（每个 card 基本对应一个单句；至少包含 Gemini 生成的 `transcription.text`、兼容字段 `transcription.timestamps`、`pronunciation`、`completeness`、`fluency`、`suggestions[]`、`issues[]`，支持按问题点时间戳回听）。
- **状态机**：`processing` → `completed | failed`。

> `CardDetail` 仅作为“历史记录查询与展示”页面，复用 `CardFeedbackAI` 的产物，不再单独拆分生成型 AI 模块。

#### 4.4.2 模块 B：DeckSummaryAI（课级总结，Summary 页面消费）

- **触发（本期默认）**：完成 deck 后，在“最后一个卡片的卡片反馈（单句）状态为 `completed`”之后自动触发。
- **输出（最小集）**：`overall`（整体总结）、`patterns[]`（重复性问题）、`prioritized_actions[]`（优先改进动作）。
- **状态机**：`processing` → `completed | failed`。

> 当前默认 provider 为 `gemini`，并通过版本化 prompt 目录进行管理；prompt 激活版本由 `GEMINI_PROMPT_VERSION` 控制。

> Prompt 调优默认采用“双模式”工作流：生产模式继续走 submission 异步链路；离线评测模式从本地 dataset 读取固定样本，对比不同 prompt 目录，并把 run 元数据、prompt 快照与输出结果归档到独立目录。

> 本期不包含 AI 解释（Explanation/Why）与 AI 字典能力，见第 6 章。

### 4.5 埋点最小集

| 埋点位置 | 事件名称 | 触发时机 | 参数 |
|---|---|---|---|
| Study 正面 | `record_start` | 点击开始录音 | `deck_id`, `card_id` |
| Study 正面 | `record_overwrite` | 新录音覆盖旧录音 | `deck_id`, `card_id` |
| Study 正面 | `flip_upload_start` | 翻面瞬间触发上传 | `deck_id`, `card_id` |
| Study 正面 | `upload_result` | 上传成功/失败 | `deck_id`, `card_id`, `upload_status`, `cost_ms` |
| Study 背面 | `review_pipeline_start` | `submission` 创建后即刻触发双音频 AI 反馈 | `submission_id`, `deck_id`, `card_id`, `realtime_session_id` |
| Study 背面 | `review_result` | 获取到处理结果 | `submission_id`, `review_status`, `error_code` |
| Summary | `summary_view` | 进入课级总结页 | `deck_id`, `has_data` |
| Settings | `settings_save` | 点击保存设置 | `daily_new_limit`, `daily_review_limit`, `scope_type` |

---

## 5. 验收标准（按 worktree 工作区模块）

本章以 worktree 工作区模块为单位组织验收项，后续可直接替代按“页面模块/优先级”拆分的验收方式。

### 5.1 `wt-contracts`（接口契约与口径）

- [ ] 全链路核心标识统一：`deck_id`、`card_id`、`submission_id`（接口与埋点口径一致）。
- [ ] 评测提交契约统一：创建 `submission` 时必须传递 `realtime_session_id`，且该会话已 ready。
- [ ] 状态字段与枚举统一：`upload_status`（`uploading/succeeded/failed`）、`review_status`（`processing/completed/failed`）。
- [ ] 卡片学习状态字段统一：`card_state` 仅允许 `learning/review/relearning`；“新卡”通过 `is_new_card` / `last_review_at` 派生，并可选返回 `due_at`。
- [ ] `GET /api/v1/study/session` / `GET /api/v1/decks/{lesson_id}/cards` 同步返回 `is_new_card`，且由 `last_review IS NULL` 推导。
- [ ] 失败结果返回可消费的 `error_code` 与 `error_message`。
- [ ] 时间字段契约统一：数据库按北京时间本地 naive 落库；接口统一返回带 `+08:00` 偏移的 ISO 8601。

### 5.2 `wt-fsrs-scheduler`（学习调度 + 派生新卡桶）

- [ ] Deck/卡片读取接口返回原生 `card_state`（`learning/review/relearning`），并额外返回 `is_new_card`；FSRS 初始卡桶由 `last_review IS NULL` 推导，并在前后端口径一致。
- [ ] `GET /api/v1/decks/tree` 的 lesson 统计返回 `new_cards`，且与 `completed_cards` / `due_cards` 口径一致。
- [ ] 若存在复习调度，接口可返回 `due_at`，用于看板/筛选/复习入口展示。
- [ ] FSRS 调度比较、跨日窗口与 `due` 判定必须基于北京时间，而不是 UTC-naive 口径。

### 5.3 `wt-submission-pipeline`（提交与状态机：upload + review）

- [ ] `Study` 完成“录音（本地缓存）+ 实时转写 → 翻面上传 → 提交 `submission` → 双音频 AI 反馈结果展示”闭环。
- [ ] 同一卡片反复录音时，始终只使用最后一次有效录音并覆盖前一次。
- [ ] 翻面后若上传失败：该卡片不可进入结果阶段，但不阻塞继续切卡练习，并提供重试路径。
- [ ] 翻面后若实时转写会话未 ready / 已 failed：阻断 `submission` 创建并提供明确错误提示。
- [ ] 若前置校验失败导致未创建 `submission`，当前卡背面仍能直接展示真实 `error_code/error_message`，不退回统一失败文案。
- [ ] 音频访问通过 STS（或等价临时授权/签名方案），避免前端长期暴露静态凭证。
- [ ] 评分成功后返回 FSRS 结果（兼容前端 `1|2|3|4` 评分提交口径），并允许用户进入下一张卡片或完成本课流程。

### 5.4 `wt-queue-tasks`（学习模式 `Queue/Tasks` 跨卡片任务列表）

- [ ] 进入 `Study` 后可在 `Queue/Tasks` 查看跨卡片任务列表（包含 `upload_status`/`review_status` 与失败原因）。
- [ ] 刷新页面、重进 lesson、切卡后，`Queue/Tasks` 状态可从 `GET /api/v1/study/submissions` 恢复，不依赖前端内存态。
- [ ] 队列支持跳转：`completed` → 对应卡片背面；`failed` → 对应卡片正面重录。
- [ ] 队列或等价错误入口可展示实时转写前置条件失败信息，不要求用户从日志中排查。

### 5.5 `wt-card-feedback`（卡片反馈（单句）+ 历史）

- [ ] `Study` 背面按 PRD 的“音频/文本/反馈/笔记”布局可用，顶部为左右对照双播放器且控件样式统一。
- [ ] 卡片反馈（单句）展示转写来自 Gemini；`transcription.timestamps` 固定为空数组但字段仍保留。
- [ ] 文本区使用单框原文/展示转写对照，并按词级机械 diff 展示缺失/替换/冗余；译文默认隐藏并在同框展开。
- [ ] 卡片反馈（单句）包含 `feedback.suggestions[]` 与 `feedback.issues[]`，且两者的 `timestamp` 都按“问题发生点”支持跳转回听；跳转只作用于练习录音。
- [ ] `CardDetail` 可按 `card_id` 查询并展示历史卡片反馈记录（与卡片反馈（单句）同结构，按时间倒序）。

### 5.6 `wt-deck-summary`（课级总结 DeckSummaryAI）

- [ ] 完成 deck 后，在“最后一个卡片的卡片反馈（单句）状态为 `completed`”后自动触发课级总结生成。
- [ ] `Summary` 可展示课级总结（`overall` / `patterns[]` / `prioritized_actions[]`）；失败时可展示 `error_code/error_message`。

### 5.7 `wt-dashboard-library-filters`（看板/题库筛选与口径）

- [ ] `Dashboard` 的接口结构与前端渲染结构一致，且统计口径与 `card_state`/调度一致。
- [ ] `Library` 可加载课程树并进入 `Study`，并能基于 `card_state` 提供一致的筛选/展示能力。
- [ ] `Settings` 的字段命名、类型、保存、回显一致。

### 5.8 跨模块（异常、边界、性能与稳定性）

- [ ] 无录音或录音无效时，翻面后给出明确提示并阻断该卡片评测流程（但不阻塞继续切卡）。
- [ ] 上传超时或失败时，不阻塞用户继续操作，并提供重试入口。
- [ ] `realtime_session_id` 缺失、session 不匹配、实时转写未完成或失败时，提交被阻断并返回明确错误码。
- [ ] 处理结果为 `failed` 时，前端展示 `error_code`/`error_message`。
- [ ] 空数据场景（无课程/无统计）具备可用兜底展示。
- [ ] 非 AI 场景接口（decks/settings/dashboard）响应目标 < 500ms。
- [ ] 实时转写与 AI 反馈流程均不阻塞页面主交互。
- [ ] 连续多卡提交时，submission 状态追踪稳定可靠。

---

## 6. 非目标（本阶段不纳入）

1. 超出学习闭环的复杂社交玩法与重运营系统。
2. 与核心学习路径无关的高成本可视化扩展。
3. 非关键路径的深度个性化推荐优化。
4. AI 解释（Explanation/Why）生成：下一版本再做（本期以可读反馈文本为准）。
5. AI 字典/术语表/可替换知识库能力：下一版本再做（可替代性较高）。
