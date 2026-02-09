# PRD（V1）：复述训练与 AI 反馈闭环

> 快速沟通与阶段基准版本请优先查看：`PRD_BASELINE.md`（更新日期：2026-02-09）。
> 本文档保留为详细实现总纲（含完整约束与技术细节）。

## 0. 文档定位（最新权威入口）
- 本文档是 LanGear **V1/当前版本** 的唯一最新产品总纲。
- 版本：v2.1（基于代码实际实现同步更新）
- 最后更新：2026-02-09。
- 实施文档拆分为：
  - 前端：`frontend/PRD_FRONTEND.md`
  - 后端：`backend/PRD_BACKEND.md`
- 旧版 PRD 类文档已归档到 `archive/docs/`。

## 1. 产品目标与范围（V1/当前版本）

### 1.1 产品目标
本产品面向口语复述训练场景，目标是建立"听、复述、AI 反馈、复盘、复习"的完整闭环，并让学习者能：
- 在卡片级别获得稳定、可回放对照的 AI 反馈（含词级时间戳）。
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
- **ASR（语音转文本）**：阿里云 DashScope - qwen3-asr-flash 模型，通过 `dashscope.audio.asr.Recognition` API 调用。输入 OSS 签名 URL，返回完整转写文本 + 词级时间戳（word-level timestamps），用于前端音频跳转功能，且支持流式输出。
- **AI 多模态评测**：Google Gemini（gemini-3.0-pro-preview），用于单句反馈与课级总结生成。Gemini 接收原文文本 + 用户转写文本进行多维度评估，返回文字反馈（不包含数值评分）。支持可选 Gemini Relay 代理配置。
- **对象存储**：阿里云 OSS，用于存储教材原音频与用户录音。采用 **OSS STS 临时凭证机制**：前端获取临时凭证后直接上传音频到 OSS，后端通过 OSS 签名 URL 处理音频。

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
4) **背面复盘**：展示原音频 vs 用户音频、原文 vs 转写（含词级时间戳）、AI 单句反馈与可跳转建议。
5) **评分（与 AI 反馈解耦）**：
   - 用户选择 again/hard/good/easy。
   - **评分不会影响 AI 反馈生成结果**；评分仅用于 FSRS 调度与学习统计。
   - 评分作为单独步骤提交，成功后进入下一张。
6) **下一张/课级总结**：卡片完成后进入下一张；完成整课后生成课级总结。

### 4.4 异步与轮询
- submission 创建后，前端轮询结果（processing/completed/failed）。
- 轮询超时 30 秒：提示“处理中，稍后在历史记录查看”，不阻塞继续学习。

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
- Review Service：训练记录写入与查询（异步处理）。
- AI Evaluation Service：调用 Gemini 生成单句反馈与课级总结（仅返回文字反馈，不包含数值评分）。
- ASR Service：调用阿里云 DashScope qwen3-asr-flash 模型完成用户录音转写，输入 OSS 签名 URL，返回 transcription + word-level timestamps。
- OSS Service：管理音频文件上传与 URL 签名。**STS AssumeRole 临时凭证生成**（前端直接上传），后端生成签名 URL 用于 ASR。
- FSRS Service：卡片调度状态计算与更新。
- Settings Service：系统配置项读写。

### 5.3 关键 API 概览（v2.0 异步架构）

本总纲只描述关键链路，具体字段与响应结构以 `backend/PRD_BACKEND.md` 为准。

- `GET /api/v1/oss/sts-token`：获取 STS 临时凭证（用于上传录音到 OSS）。
- `POST /api/v1/study/submissions`：翻面后提交训练（携带 `oss_audio_path`），返回 `submission_id` 并进入异步处理队列。
- `GET /api/v1/study/submissions/{id}`：轮询获取处理结果（processing/completed/failed）。
- 评分提交：用于 FSRS 更新与学习统计（接口形态以后端实现为准）。

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
用于存储 FSRS 调度状态。该表按卡片记录状态、稳定度、难度与下次复习时间。
- card_id：主键，关联 `cards.id`。
- state：FSRS 状态值（如 new/learning/review/relearning）。
- stability：稳定度（Float）。
- difficulty：难度系数（Float）。
- due：下次复习时间。
- last_review：上次复习时间（可为空）。
- updated_at：状态更新时间。

### 6.5 review_log
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

**索引**：card_id, deck_id, status, result_type, created_at 均有索引。

### 6.6 settings
用于存储系统级配置项（每日任务数量、默认教材范围等）。
- key：主键，字符串类型（最大 100 字符）。
- value：配置项值（JSON 类型，支持复杂值）。
- updated_at：更新时间。

## 7. AI 反馈规范

### 7.1 AI 服务选型
- **ASR 转写**：阿里云 DashScope qwen3-asr-flash 模型。后端通过 `dashscope.audio.asr.Recognition` API 传入 OSS 签名 URL（`file_urls` 参数），启用 `timestamp_alignment_enabled=True` 获取词级时间戳。获取转写文本 + 词级时间戳。
- **多模态评测**：Google Gemini（gemini-3.0-pro-preview）。后端将原文文本、用户转写文本发送至 Gemini，获取结构化反馈（仅文字描述，不包含数值评分）。
- API Key 通过环境变量配置（`GEMINI_API_KEY`、`DASHSCOPE_API_KEY`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`），禁止硬编码。
- 支持可选 Gemini Relay 代理（`GEMINI_RELAY_BASE_URL`、`GEMINI_RELAY_API_KEY`）。

### 7.2 单句反馈 JSON 结构
单句反馈必须包含转写文本（含词级时间戳）与发音/完整度/流畅度三大核心指标，使用固定结构化字段：
```json
{
  "transcription": {
    "text": "Hello world this is a test",
    "timestamps": [
      {"word": "Hello", "start": 0.0, "end": 0.5},
      {"word": "world", "start": 0.6, "end": 1.0},
      {"word": "this", "start": 1.1, "end": 1.3},
      {"word": "is", "start": 1.4, "end": 1.5},
      {"word": "a", "start": 1.6, "end": 1.7},
      {"word": "test", "start": 1.8, "end": 2.2}
    ]
  },
  "feedback": {
    "pronunciation": "发音评估文字描述",
    "completeness": "内容完整度评估文字描述",
    "fluency": "流畅度评估文字描述",
    "suggestions": [
      {
        "text": "建议内容",
        "target_word": "world",
        "timestamp": 0.6
      }
    ]
  }
}
```

**说明**：
- `transcription.timestamps`：词级时间戳数组，用于前端音频跳转功能。
- `feedback.suggestions`：建议数组（最多 3 条），可关联 `target_word` 和 `timestamp`，点击可跳转到对应音频位置。
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
3) 单句反馈包含词级时间戳，支持跳转回听；AI 反馈无数值总分。
4) 范围按 source deck 多选生效；每日 due/new 目标分别生效，且不足不补齐。
5) Dashboard：连续天数与热力图按“评分提交”口径统计。

## 10. 文档维护规则
- 若前后端实现细节变更，优先更新对应子文档，再回写本总纲的关键约束。
- 任何新的 PRD 草稿必须标注状态，不得与本文件并列为"最新版本"。
