# PRD（V1）：复述训练与 AI 反馈闭环

> 快速沟通与阶段基准版本请优先查看：`PRD_BASELINE.md`（更新日期：2026-03-22）。
> 本文档保留为详细实现总纲（含完整约束与技术细节）。
> 文档维护约束：当项目行为、命令、约束发生变化时，同步更新 `README.md`；当产品流程、契约、状态模型或验收标准变化时，同步更新 `PRD.md` 与 `PRD_BASELINE.md`。`docs/prd_versions/` 当前仅对 `PRD.md` 做版本镜像与归档，更新 `PRD.md` 后需执行 `python3 scripts/prd_version_manager.py sync`。`CLAUDE.md` 为 `AGENTS.md` 的软链接，以 `AGENTS.md` 为准。

## 0. 文档定位（最新权威入口）
- 本文档是 LanGear **V1/当前版本** 的唯一最新产品总纲。
- 版本：v2.2（基于代码实际实现同步更新）
- 最后更新：2026-03-22。
- 实施文档拆分为：
  - 前端：`frontend/PRD_FRONTEND.md`
  - 后端：`backend/PRD_BACKEND.md`
- 版本追踪目录：`docs/prd_versions/`
- 旧版 PRD 类文档已归档到 `archive/docs/`。

## 1. 产品目标与范围（V1/当前版本）

### 1.1 产品目标
本产品面向口语复述训练场景，目标是建立"听、复述、AI 反馈、复盘、复习"的完整闭环，并让学习者能：
- 在卡片级别获得稳定、可回放对照的 AI 反馈（包含 Gemini 展示转写与问题点时间戳）。
- 在课文级别获得总结性复盘与下一步建议。
- 通过 FSRS 调度形成长期复习节奏。

### 1.2 V1 范围（In-scope / Out-of-scope）

**In-scope（V1 必须支持）**
- 内置教材训练闭环：教材（source）→ 单元（unit）→ 课文（lesson）→ 卡片（card）。
- 管理员单用户模式（ID=1），不做注册登录。
- 录音上传到 OSS（前端 STS 直传），后端完成 ASR + AI 评测，前端轮询结果。
- 单句反馈与课级总结持久化到 `review_log`。
- FSRS 调度生效，且可**按教材来源（source deck）维度选择范围**进行学习。
- Dashboard：任务配置、连续学习天数、热力图（口径见第 4 节与第 9 节）。

**Out-of-scope（V1 明确不做）**
- 自定义上传与字幕切分（视频/音频切分、对齐、人工校对等）。
- 词典/词汇导入体系、复杂查词系统。
- 多用户/班级/教师权限体系。
- 排行榜、积分体系（可占位展示但不做核心逻辑）。
- 离线/PWA 能力。

### 1.3 V1 必须达成的结果（验收层）
1. 管理员可以选择教材与课文并完成卡片训练闭环。
2. 每张卡片都能生成 AI 单句反馈并持久化记录（`review_log.result_type=single`）。
3. 当课文全部卡片完成后，自动生成课级总结并持久化记录（`review_log.result_type=summary`）。
4. FSRS 调度必须生效；用户可按教材来源（source deck）维度独立筛选 due/new 卡片进行学习。

## 2. 目标技术栈（重构迁移口径）
### 2.1 前端技术栈
- Vue 3.5.25（Composition API）
- TypeScript 5.9.3
- Vite 7.2.6
- Element Plus 2.12.0
- Pinia 3.0.4
- Vue Router 4.6.3
- lucide-vue-next
- ali-oss 6.23.0（阿里云 OSS 前端直传）
- echarts 5.6.0 + vue-echarts 7.0.3（图表与热力图）
- @vueuse/core
- axios
- Tailwind CSS 3.4.0（原子化 CSS 框架）
- @ffmpeg/ffmpeg + @ffmpeg/core（保留，用于未来视频切分功能）

### 2.2 后端技术栈
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x（ORM）
- Alembic（数据库迁移）
- SQLite（单库）
- Pydantic 2.x + pydantic-settings（请求校验与配置管理）
- uv（唯一包管理与运行入口）
- fsrs（`>=6.3.0`，通过 uv 安装，不使用源码内嵌）
- google-generativeai（Google Gemini API SDK）
- dashscope（阿里云 DashScope SDK，用于 qwen3-asr-flash ASR）
- oss2（阿里云 OSS SDK）
- aliyun-python-sdk-core + aliyun-python-sdk-sts（STS AssumeRole 凭证）
- 后台任务：`threading.Thread`（后台线程处理异步 AI 评测）

### 2.3 AI 与云服务
- **ASR（语音转文本）**：阿里云 DashScope `qwen3-asr-flash` / realtime 变体，用于提交流程中的实时转写会话与就绪校验；当前单句反馈展示不再依赖 ASR 词级时间戳。
- **AI 多模态评测**：Google Gemini，用于单句反馈与课级总结生成。Gemini 直接基于原文、参考音频和学生音频输出展示转写、中文反馈文本，以及问题点时间戳；不输出字级时间戳。
- **Prompt 离线评测**：后端提供独立于生产提交流程的本地 dataset/export/run 归档能力，用于固定样本、模型与 generation config 后对比不同 prompt 变体。
- **对象存储**：阿里云 OSS，用于存储教材原音频与用户录音。采用 **OSS STS 临时凭证机制**：前端获取临时凭证后直接上传音频到 OSS，后端通过 OSS 签名 URL 处理音频。
- **运行时真源**：结构化评测结果与 FSRS 状态始终保存在 `DATABASE_URL` 指向的业务数据库中；默认本地值 `sqlite:///data/langear.db` 归一后落到 `backend/data/langear.db`。`backend/datasets/` 仅用于离线评测导出，OSS 仅保存音频对象。

### 2.4 数据导入
- 内置教材（新概念英语、剑桥雅思听力）通过 Python 种子脚本导入。
- 种子脚本读取结构化 JSON 文件，写入 `decks` 与 `cards` 表。
- 教材音频文件预上传至阿里云 OSS，`cards.audio_path` 存储 OSS URL。
- 种子脚本位于 `backend/scripts/seed_data.py`，数据文件位于 `backend/data/seeds/`。

## 3. 用户与权限
V1 采用管理员单用户模式。系统仅维护一个管理员账号（ID=1），所有数据归属于该账号。当前阶段不提供访客模式与登录注册流程。

## 4. 核心用户流程（V1/当前版本）

V1 只要求把学习闭环与关键约束梳理清楚（不写实现细节）。

### 4.1 选择范围与目标
- 学习范围按**教材来源（source deck）多选**。
- 今日目标分为两项：**复习目标数**与**新学目标数**（分别配置）。
- 默认值来自 Settings；学习页允许只对本次 session 临时调整。

### 4.2 生成今日卡片队列
- 在所选 source 范围内，系统生成两类卡片：
  - **待复习（due）**：到期需要复习的卡。
  - **新学（new）**：未学过的新卡。
- 默认学习顺序：先 due 后 new。
- **不足不补齐**：due 不够不拿 new 补；new 不够不拿 due 补。

### 4.3 单卡训练闭环（核心）
1) **正面练习**：播放原音频 → 用户复述录音（可多次尝试，始终覆盖浏览器缓存录音）。
2) **上传（停止录音后触发）**：
   - 用户停止录音后，前端获取 STS 凭证并将录音上传到 OSS（显示上传进度）。
   - 若上传失败：不允许翻面，必须提示重试。
3) **翻面触发排队（强制）**：
   - 用户点击翻面时，才创建训练 submission（ASR → AI 评测），并开始轮询处理结果。
4) **背面复盘**：展示原音频 vs 用户音频、原文 vs Gemini 展示转写、AI 单句反馈与可跳转建议；回听定位仅来自问题点时间戳。
   - 若提交前置校验失败，背面必须直接展示后端返回的真实 `error_code` / `error_message`，不能退化为统一“提交失败，请重试”。
5) **评分（与 AI 反馈解耦）**：
   - 用户在前端选择 FSRS 整数评分 `1/2/3/4`，后端统一映射为 `again/hard/good/easy`。
   - **评分不会影响 AI 反馈生成结果**；评分仅用于 FSRS 调度与学习统计。
   - 评分作为单独步骤提交；提交成功后返回 FSRS 更新结果（至少包含原生 `state`=`learning/review/relearning`、`difficulty`、`stability`、`due_at`），并进入下一张。
6) **下一张/课级总结**：卡片完成后进入下一张；完成整课后生成课级总结。

### 4.4 异步与轮询
- submission 创建后，前端轮询结果（processing/completed/failed）。
- 轮询超时 30 秒：提示“处理中，稍后在历史记录查看”，不阻塞继续学习。
- 进入 lesson、刷新页面、重新进入学习页时，前端必须先调用 `GET /api/v1/study/submissions?lesson_id=...` 恢复最近 submission 状态，再按需继续轮询 `GET /api/v1/study/submissions/{id}`。
- 历史恢复口径必须覆盖 `processing`、`failed`、`completed`，并以 `review_log` 为真源；不得退回到仅依赖前端 store 或“卡片最新 completed oss path”的弱口径。
- 如果前置校验失败导致 submission 根本未创建，后端必须返回明确错误码，且不创建 `review_log`；前端仍需保留当前卡背面的失败信息，避免误判为“没保存”。

### 4.5 Dashboard 统计口径（按评分）
- 连续学习天数：当天只要发生 ≥1 次“评分提交”，即算学习日。
- 热力图：统计每天的评分提交次数。

### 4.6 失败阻断
关键失败必须阻断并提示：OSS 上传失败、ASR/AI 失败、课级总结生成失败等。

## 5. 模块边界总览
### 5.1 前端模块（详见 `frontend/PRD_FRONTEND.md`）
- Dashboard：学习概览、每周趋势图、最近课程、连续学习热力图、继续练习入口。
- Library：教材来源/单元/课文树形浏览与进入训练。
- Study Session：正反面训练流程、录音、OSS 上传、异步提交、轮询结果、评分。
- Card Detail：单句反馈细节展示。
- Summary：课级总结展示与复盘建议。
- Settings：管理员系统配置（每日任务、默认来源范围（source deck 多选））。

### 5.2 后端模块（详见 `backend/PRD_BACKEND.md`）
- Content Service：教材层级与卡片内容管理。
- Review Service：训练记录写入、`submission_trace` 可观测性与历史查询（异步处理）。
- AI Evaluation Service：调用 Gemini 生成单句反馈与课级总结（仅返回文字反馈，不包含数值评分）。
- Gemini Prompt Eval Workflow：导出已完成单句反馈样本到本地 dataset，保存样本元数据、音频归档、run 输入输出与 prompt 快照，供 prompt A/B 对比使用，不回写业务 `review_log`。
- ASR Service：调用阿里云 DashScope qwen3-asr-flash 模型维护实时转写会话与提交前置校验，不再作为单句反馈展示转写的真相源。
- OSS Service：管理音频文件上传与 URL 签名。**STS AssumeRole 临时凭证生成**（前端直接上传），后端生成签名 URL 用于 ASR。
- FSRS Service：卡片调度状态计算与更新。
- Settings Service：系统配置项读写。

### 5.3 关键 API 概览（v2.0 异步架构）

本总纲只描述关键链路，具体字段与响应结构以 `backend/PRD_BACKEND.md` 为准。

- `GET /api/v1/oss/sts-token`：获取 STS 临时凭证（用于上传录音到 OSS）。
- `GET /api/v1/study/session`：获取当前学习 session；返回 `server_time`、`session_date`、`scope`、`quota`、`summary` 与按“FSRS 学习中/复习中卡片优先，再补充初始卡桶”的顺序返回的 `cards[]`；每张卡返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`，其中 `card_state` 只允许 `learning/review/relearning`。
- `GET /api/v1/decks/tree`：获取 source-unit-lesson 树；lesson 节点至少返回 `total_cards`、`completed_cards`、`due_cards`、`new_cards`。
- `GET /api/v1/decks/{lesson_id}/cards`：获取 lesson 内卡片；每张卡至少返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`，其中 `card_state` 只允许 `learning/review/relearning`。
- `POST /api/v1/study/submissions`：翻面后提交训练（携带 `oss_audio_path` 与 `realtime_session_id`），返回 `submission_id` 并进入异步处理队列。
- `GET /api/v1/study/submissions?lesson_id=...&card_id=...`：学习页恢复最近 submission 历史，返回 `processing` / `failed` / `completed` 三类状态，以及 `submission_id`、`card_id`、`lesson_id`、`status`、`error_code`、`error_message`、`created_at`、`oss_audio_path`、`transcription`、`feedback`。
- `GET /api/v1/study/submissions/{id}`：轮询获取处理结果（processing/completed/failed）；完成态至少返回 `transcription.text`、兼容字段 `transcription.timestamps`、`feedback.suggestions[]`、`feedback.issues[]`、`oss_audio_path`；若返回 `srs`，其中 `state` 仅允许 `learning/review/relearning`。
- `POST /api/v1/study/submissions/{id}/rating`：提交评分，用于 FSRS 更新与学习统计；前端可提交 `1|2|3|4`，后端按 `again/hard/good/easy` 口径落库，并返回原生 FSRS 更新结果（`state` 仅允许 `learning/review/relearning`）。

## 6. 数据库设计（6 张表）
数据库采用 SQLite 单库。教材层级使用单表树形表达，卡片作为最小训练单元。字段定义如下。

### 6.1 users
用于存储管理员账号信息，仅维护一个账号（ID=1）。
- id：主键，自增整数。
- username：用户名，唯一索引，不为空。
- email：邮箱地址，唯一索引，可为空。
- created_at：创建时间。
- updated_at：更新时间。

### 6.2 decks
统一表示教材来源、单元与课文三层结构，通过 `parent_id` 构成树形结构。
- id：主键，自增整数。
- parent_id：父级节点标识。教材来源为空，单元指向来源，课文指向单元。
- title：节点标题，例如"新概念英语第二册""Unit 1""Lesson 3"。
- type：节点类型，取值为 `source`、`unit`、`lesson`。
- level_index：同级排序字段，用于稳定展示顺序。
- created_at：创建时间。
- updated_at：更新时间。

### 6.3 cards
用于存储最小训练单元，每条记录关联到课文级 `deck` 节点。
- id：主键，自增整数。
- deck_id：关联 `decks.id`，且目标节点必须为 `lesson`。
- card_index：同课文内排序字段。
- front_text：正面文本（Text 类型），一般为原文句子。
- back_text：背面文本（Text 类型），一般为译文或解析文本，可为空。
- audio_path：原音频 OSS URL（格式如 `https://<bucket>.oss-cn-<region>.aliyuncs.com/audio/nce2/lesson01/s01.mp3`），可为空。
- created_at：创建时间。
- updated_at：更新时间。

### 6.4 user_card_srs
用于存储原生 FSRS `Card` 快照。该表按卡片记录原生状态、step、稳定度、难度与下次复习时间。
- card_id：主键，关联 `cards.id`。
- state：仅允许 `learning` / `review` / `relearning`；`new` 不再持久化到该字段。
- step：FSRS 当前学习/再学习步数；`review` 状态下为空。
- stability：稳定度（Float，可为空；初始卡为空）。
- difficulty：难度系数（Float，可为空；初始卡为空）。
- due：下次复习时间。
- last_review：上次复习时间（可为空）。`last_review IS NULL` 表示该卡仍属于 FSRS 初始卡，也即业务上的 `new cards` 桶。
- updated_at：状态更新时间。

### 6.5 fsrs_review_log
用于存储原生 FSRS `ReviewLog` 历史，作为每次评分后的调度审计链路。
- id：主键，自增整数。
- card_id：关联 `cards.id`。
- rating：FSRS 原生评分枚举值（`1/2/3/4` 对应 `Again/Hard/Good/Easy`）。
- review_datetime：评分发生时间（UTC）。
- review_duration：评分耗时（毫秒，可为空）。

### 6.6 review_log
用于存储训练记录与 AI 反馈。单句反馈与课级总结都写入该表，通过 `result_type` 区分。
- id：主键，自增整数。
- card_id：关联 `cards.id`，课级总结记录可为空。
- deck_id：关联 `lesson` 类型 `decks.id`，不可为空。
- rating：用户评分结果（again/hard/good/easy），课级总结可为空。
- result_type：记录类型，取值为 `single` 或 `summary`。
- ai_feedback_json：AI 反馈结构化结果 JSON（不可为空），包含 transcription（含 timestamps）、feedback、oss_path。
- status：处理状态，取值为 `processing`（处理中）、`completed`（已完成）、`failed`（失败）。
- error_code：失败时记录错误码（如 `ASR_TRANSCRIPTION_FAILED`、`AI_FEEDBACK_FAILED`）。
- error_message：失败时记录错误详情（Text 类型）。
- created_at：创建时间。

`review_log`、`fsrs_review_log` 与 `user_card_srs` 同属 `DATABASE_URL` 指向的运行时数据库；其中 `review_log` 是业务 submission / AI 结果真源，`user_card_srs` + `fsrs_review_log` 是原生 FSRS 调度真源，不存放在 OSS，也不以 `backend/datasets/` 为准。

学习页 submission 历史恢复同样以 `review_log` 为真源，查询口径覆盖 `processing` / `failed` / `completed`，不依赖卡片聚合字段推断。

**索引**：card_id, deck_id, status, result_type, created_at 均有索引。

### 6.7 settings
用于存储系统级配置项（每日任务数量、默认教材范围等）。
- key：主键，字符串类型（最大 100 字符）。
- value：配置项值（JSON 类型，支持复杂值）。
- updated_at：更新时间。

## 7. AI 反馈规范

### 7.1 AI 服务选型
- **ASR 转写**：阿里云 DashScope qwen3-asr-flash 模型用于实时转写会话；其 `final_text` 仅用于提交前置条件校验，不再直接作为单句反馈展示转写。
- **多模态评测**：Google Gemini 基于原文、参考音频与学生音频生成结构化反馈，输出展示转写、中文反馈，以及 `issues[]` / `suggestions[]` 上的问题点时间戳。
- API Key 通过环境变量配置（`GEMINI_API_KEY`、`DASHSCOPE_API_KEY`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`），禁止硬编码。
### 7.2 单句反馈 JSON 结构
单句反馈必须包含 Gemini 生成的展示转写与发音/完整度/流畅度三大核心指标，使用固定结构化字段：
```json
{
  "transcription": {
    "text": "Hello world this is a test",
    "timestamps": []
  },
  "feedback": {
    "pronunciation": "中文发音评估文字描述",
    "completeness": "中文内容完整度评估文字描述",
    "fluency": "中文流畅度评估文字描述",
    "suggestions": [
      {
        "text": "中文建议内容",
        "target_word": "world",
        "timestamp": 0.6
      }
    ],
    "issues": [
      {
        "problem": "中文问题描述",
        "timestamp": 0.6
      }
    ]
  }
}
```

**说明**：
- `transcription.text`：Gemini 基于学生音频生成的展示转写。
- `transcription.timestamps`：兼容字段，当前固定为空数组，不再承载词级跳转。
- `feedback.suggestions` / `feedback.issues`：两者的 `timestamp` 语义一致，都是“问题发生点”，点击可跳转到对应音频位置。
- `feedback` 文本统一使用中文；`target_word` 保留英文词或短语。
- **移除 `overall_score` 数值评分**，仅保留文字反馈。
- `ai_feedback_json` 实际存储时额外包含 `oss_path` 字段（用户录音 OSS 路径）。

### 7.3 课级总结 JSON 结构
课级总结必须聚合本课单句反馈并输出共性问题与优先改进建议：
```json
{
  "overall": "本课表现总评",
  "patterns": ["高频问题模式1", "高频问题模式2"],
  "prioritized_actions": ["优先改进建议1", "优先改进建议2"]
}
```

### 7.4 一致性要求
前后端使用固定 JSON 字段，避免渲染不稳定。

## 8. 无降级原则与错误处理
V1 阶段所有关键流程必须严格成功，不允许以备用流程绕过失败。

### 8.1 前端 OSS 上传阶段
- 前端 OSS 上传失败时，**禁止提交训练请求**，提示"音频上传失败，请重试"。

### 8.2 异步处理阶段
- **ASR 转写失败**：`review_log` 状态改为 `failed`，返回 `error_code=ASR_TRANSCRIPTION_FAILED`。
- **AI 评测失败**：`review_log` 状态改为 `failed`，返回 `error_code=AI_FEEDBACK_FAILED`。
- **FSRS 更新失败**：记录错误但不影响反馈展示（review_log 仍标记为 completed），返回 `error_code=SRS_UPDATE_FAILED`。
- **未知错误**：`review_log` 状态改为 `failed`，返回 `error_code=UNEXPECTED_ERROR`。

### 8.3 轮询超时策略
- 前端轮询 30 秒后超时：停止轮询，显示"处理中，请稍后在历史记录中查看"。
- 后台任务继续执行，完成后用户可在历史记录中查看结果。
- **不阻塞用户继续下一张卡片**。

### 8.4 课级总结阶段
- 课级总结生成失败时，必须阻止课文完成，提供"重试生成"按钮。

### 8.5 数据库写入
- 数据库写入失败时，必须返回明确错误并禁止前端伪成功展示。

## 9. 验收标准（v2.0 异步架构）
以下用例均以 "V1/当前版本" 口径验收。

1) 可完整跑通训练闭环（从选择教材到完成卡片与总结）。
2) 翻面时才上传 OSS + 创建 submission（强制要求），且可轮询拿到 completed/failed。
3) 单句反馈包含 Gemini 展示转写；`transcription.timestamps` 保持空数组兼容，跳转回听仅依赖 `issues[]` / `suggestions[]` 的问题点时间戳；AI 反馈无数值总分。
4) 范围按 source deck 多选生效；每日 due/new 目标分别生效，且不足不补齐。
5) Dashboard：连续天数与热力图按“评分提交”口径统计。

## 10. 文档维护规则
- 若前后端实现细节变更，优先更新对应子文档，再回写本总纲的关键约束。
- 任何新的 PRD 草稿必须标注状态，不得与本文件并列为"最新版本"。
