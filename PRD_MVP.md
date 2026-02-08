# PRD（MVP 版）：复述训练与 AI 反馈闭环

## 0. 文档定位（最新权威入口）
- 本文档是 Langear MVP 的唯一最新产品总纲。
- 版本：v2.0（异步架构版本）
- 最后更新：2026-02-08。
- 实施文档拆分为：
  - 前端：`frontend/PRD_MVP_FRONTEND.md`
  - 后端：`backend/PRD_MVP_BACKEND.md`
- 旧版 PRD 类文档已归档到 `archive/docs/`。

## 1. 产品目标与范围
本产品面向口语复述训练场景，目标是建立“听、复述、AI 反馈、复盘、复习”的完整闭环。MVP 阶段只关注内置教材训练流程，不包含自定义上传与字幕切分等扩展功能。内置教材至少包含新概念英语与剑桥雅思听力，后续教材通过数据导入扩展。

MVP 必须达成以下结果：
1. 管理员可以选择教材与课文并完成全部卡片训练。
2. 每张卡片都能生成 AI 单句反馈并持久化记录。
3. 当课文全部完成时自动生成课级总结并持久化记录。
4. FSRS 调度必须生效，并且在同一教材来源内独立运作。

## 2. 目标技术栈（重构迁移口径）
### 2.1 前端技术栈
- Vue 3.5.25（Composition API）
- TypeScript 5.9.3
- Vite 7.2.6
- Element Plus 2.12.0
- Pinia 3.0.4
- Vue Router 4.6.3
- lucide-vue-next
- @ffmpeg/ffmpeg + @ffmpeg/core（浏览器端音视频处理）
- @vueuse/core
- axios
- crypto-js

### 2.2 后端技术栈
- Python 3.11+
- FastAPI
- SQLAlchemy（ORM）
- SQLite（单库）
- uv（唯一包管理与运行入口）
- fsrs（`>=6.3.0`，通过 uv 安装，不使用源码内嵌）
- google-genai（Gemini API SDK）
- alibabacloud-nls（阿里云语音服务 SDK）
- oss2（阿里云 OSS SDK）

### 2.3 AI 与云服务
- **ASR（语音转文本）**：阿里云 DashScope - qwen3-asr-flash 模型，用于用户录音转写。支持 HTTP API 调用，返回完整转写文本 + 词级时间戳（word-level timestamps），用于前端音频跳转功能。
- **AI 多模态评测**：Google Gemini（gemini-3.0-pro-preview），用于单句反馈与课级总结生成。Gemini 接收原文文本 + 用户转写文本进行多维度评估，返回文字反馈（不包含数值评分）。
- **对象存储**：阿里云 OSS，用于存储教材原音频与用户录音。采用 **OSS STS 临时凭证机制**：前端获取临时凭证后直接上传音频到 OSS，后端通过 OSS 路径处理音频。

### 2.4 数据导入
- 内置教材（新概念英语、剑桥雅思听力）通过 Python 种子脚本导入。
- 种子脚本读取结构化 JSON 文件，写入 `decks` 与 `cards` 表。
- 教材音频文件预上传至阿里云 OSS，`cards.audio_path` 存储 OSS URL。
- 种子脚本位于 `backend/scripts/seed_data.py`，数据文件位于 `backend/data/`。

## 3. 用户与权限
MVP 采用管理员单用户模式。系统仅维护一个管理员账号，所有数据归属于该账号。当前阶段不提供访客模式与登录注册流程。

## 4. 核心用户流程
1. 管理员进入应用并在教材库中选择教材来源与课文。
2. 系统加载课文卡片列表并进入训练流程。
3. 正面播放原音频，管理员进行复述录音。
3.5. **录音完成后，前端通过 STS 凭证直接上传音频到 OSS**。
4. **提交训练请求（包含 OSS 路径 + 评分），系统立即返回 submission_id**。
4.5. **前端轮询获取 AI 评测结果（处理中/已完成/失败）**。
5. **收到 completed 状态后**，翻面展示原文音频、原文文本、用户录音、转写文本（含词级时间戳）与 AI 单句反馈。点击建议可跳转到音频对应时间戳位置。管理员选择评分按钮（重来、困难、良好、简单）。
6. 当课文全部卡片完成后，系统自动生成课级总结并写入训练记录。
7. 课级总结页面展示该课文的共性问题与学习建议。

所有关键动作失败都必须阻断流程并提示错误，包括但不限于：音频上传失败、AI 单句反馈失败、课级总结生成失败。

## 5. 模块边界总览
### 5.1 前端模块（详见 `frontend/PRD_MVP_FRONTEND.md`）
- Dashboard：学习概览、任务配置、连续学习热力图、继续练习入口。
- Library：教材来源/单元/课文树形浏览与进入训练。
- Study Session：正反面训练流程、录音、评分、提交。
- Card Detail：单句反馈细节展示。
- Summary：课级总结展示与复盘建议。
- Settings：管理员系统配置（每日任务、默认来源范围）。

### 5.2 后端模块（详见 `backend/PRD_MVP_BACKEND.md`）
- Content Service：教材层级与卡片内容管理。
- Review Service：训练记录写入与查询（异步处理）。
- AI Evaluation Service：调用 Gemini 生成单句反馈与课级总结（仅返回文字反馈，不包含数值评分）。
- ASR Service：调用阿里云 DashScope qwen3-asr-flash 模型完成用户录音转写，输入 OSS 签名 URL，返回 transcription + word-level timestamps。
- OSS Service：管理音频文件上传与 URL 签名。**STS AssumeRole 临时凭证生成**（前端直接上传），后端生成签名 URL 用于 ASR。
- FSRS Service：卡片调度状态计算与更新。
- Settings Service：系统配置项读写。

### 5.3 关键 API 概览（v2.0 异步架构）

以下为核心训练流程的关键 API 接口：

#### 1. `GET /api/v1/oss/sts-token`
**用途**：前端获取 STS 临时凭证用于直接上传音频到 OSS。

**响应示例**：
```json
{
  "access_key_id": "STS.xxx",
  "access_key_secret": "xxx",
  "security_token": "xxx",
  "expiration": "2026-02-08T12:00:00Z",
  "bucket": "langear",
  "region": "oss-cn-shanghai"
}
```

#### 2. `POST /api/v1/study/submissions`
**用途**：提交训练请求（oss_audio_path + rating），立即返回 submission_id，不等待 AI 评测。

**请求体**：
```json
{
  "lesson_id": 111,
  "card_id": 1001,
  "rating": "good",
  "oss_audio_path": "recordings/20260208/1001_1707382800.wav"
}
```

**响应示例**（立即返回）：
```json
{
  "submission_id": 9001,
  "status": "processing"
}
```

#### 3. `GET /api/v1/study/submissions/{id}`
**用途**：轮询获取处理结果（processing/completed/failed）。

**响应示例（处理中）**：
```json
{
  "submission_id": 9001,
  "status": "processing",
  "progress": "asr_completed"
}
```

**响应示例（已完成）**：
```json
{
  "submission_id": 9001,
  "status": "completed",
  "result_type": "single",
  "transcription": {
    "text": "Hello world this is a test",
    "timestamps": [
      {"word": "Hello", "start": 0.0, "end": 0.5},
      {"word": "world", "start": 0.6, "end": 1.0}
    ]
  },
  "feedback": {
    "pronunciation": "发音评估文字...",
    "completeness": "完整度评估文字...",
    "fluency": "流畅度评估文字...",
    "suggestions": [
      {
        "text": "建议内容",
        "target_word": "world",
        "timestamp": 0.6
      }
    ]
  },
  "srs": {
    "state": "review",
    "difficulty": 5.8,
    "stability": 12.3,
    "due": "2026-02-08T08:00:00Z"
  }
}
```

**响应示例（失败）**：
```json
{
  "submission_id": 9001,
  "status": "failed",
  "error_code": "ASR_TRANSCRIPTION_FAILED",
  "error_message": "ASR 转写失败：超时"
}
```

## 6. 数据库设计（6 张表）
数据库采用 SQLite 单库。教材层级使用单表树形表达，卡片作为最小训练单元。字段定义如下。

### 6.1 users
用于存储管理员账号信息，仅维护一个账号。
- id：主键，自增整数。
- role：固定为 `admin`，用于权限身份声明。
- display_name：管理员显示名称。
- created_at：创建时间。

### 6.2 decks
统一表示教材来源、单元与课文三层结构，通过 `parent_id` 构成树形结构。
- id：主键，自增整数。
- parent_id：父级节点标识。教材来源为空，单元指向来源，课文指向单元。
- title：节点标题，例如“新概念英语第二册”“Unit 1”“Lesson 3”。
- type：节点类型，取值为 `source`、`unit`、`lesson`。
- level_index：同级排序字段，用于稳定展示顺序。
- created_at：创建时间。

### 6.3 cards
用于存储最小训练单元，每条记录关联到课文级 `deck` 节点。
- id：主键，自增整数。
- deck_id：关联 `decks.id`，且目标节点必须为 `lesson`。
- front_text：正面文本，一般为原文句子。
- back_text：背面文本，一般为译文或解析文本。
- audio_path：原音频 OSS URL（格式如 `https://<bucket>.oss-cn-<region>.aliyuncs.com/audio/nce2/lesson01/s01.mp3`）。
- card_index：同课文内排序字段。
- created_at：创建时间。

### 6.4 user_card_srs
用于存储 FSRS 调度状态。该表按卡片记录状态、稳定度、难度与下次复习时间。
- card_id：主键，关联 `cards.id`。
- state：FSRS 状态值（如 new/learning/review/relearning）。
- stability：稳定度。
- difficulty：难度系数。
- due：下次复习时间。
- updated_at：状态更新时间。

### 6.5 review_log
用于存储训练记录与 AI 反馈。单句反馈与课级总结都写入该表，通过 `result_type` 区分。
- id：主键，自增整数。
- card_id：关联 `cards.id`，课级总结记录可为空。
- deck_id：关联 `lesson` 类型 `decks.id`，用于课级总结归档。
- rating：用户评分结果（重来/困难/良好/简单）。
- result_type：记录类型，取值为 `single` 或 `summary`。
- status：处理状态，取值为 `processing`（处理中）、`completed`（已完成）、`failed`（失败）。
- error_code：失败时记录错误码（如 `ASR_TRANSCRIPTION_FAILED`、`AI_FEEDBACK_FAILED`）。
- error_message：失败时记录错误详情。
- progress：处理进度标识（如 `asr_completed`、`ai_processing`），用于前端展示进度。
- ai_feedback_json：AI 反馈结构化结果 JSON，包含 transcription（含 timestamps）、feedback、oss_path。
- created_at：创建时间。

### 6.6 settings
用于存储系统级配置项（每日任务数量、默认教材范围等）。
- id：主键，自增整数。
- key：配置项名称。
- value：配置项值（文本存储）。
- updated_at：更新时间。

## 7. AI 反馈规范

### 7.1 AI 服务选型
- **ASR 转写**：阿里云 DashScope qwen3-asr-flash 模型。后端通过 HTTP API 传入 OSS 签名 URL，获取转写文本 + 词级时间戳。
- **多模态评测**：Google Gemini（gemini-3.0-pro-preview）。后端将原文文本、用户转写文本发送至 Gemini，获取结构化反馈（仅文字描述，不包含数值评分）。
- API Key 通过环境变量配置（`GEMINI_API_KEY`、`DASHSCOPE_API_KEY`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`），禁止硬编码。

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
- `feedback.suggestions`：建议数组，可关联 `target_word` 和 `timestamp`，点击可跳转到对应音频位置。
- **移除 `overall_score` 数值评分**，仅保留文字反馈。

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
MVP 阶段所有关键流程必须严格成功，不允许以备用流程绕过失败。

### 8.1 前端 OSS 上传阶段
- 前端 OSS 上传失败时，**禁止提交训练请求**，提示"音频上传失败，请重试"。

### 8.2 异步处理阶段
- **ASR 转写失败**：`review_log` 状态改为 `failed`，返回 `error_code=ASR_TRANSCRIPTION_FAILED`。
- **AI 评测失败**：`review_log` 状态改为 `failed`，返回 `error_code=AI_FEEDBACK_FAILED`。
- **FSRS 更新失败**：记录错误但不影响反馈展示，返回 `error_code=SRS_UPDATE_FAILED`。

### 8.3 轮询超时策略
- 前端轮询 30 秒后超时：停止轮询，显示"处理中，请稍后在历史记录中查看"。
- 后台任务继续执行，完成后用户可在历史记录中查看结果。
- **不阻塞用户继续下一张卡片**。

### 8.4 课级总结阶段
- 课级总结生成失败时，必须阻止课文完成，提供"重试生成"按钮。

### 8.5 数据库写入
- 数据库写入失败时，必须返回明确错误并禁止前端伪成功展示。

## 9. 验收标准（v2.0 异步架构）
1. 新概念英语与剑桥雅思听力课文可完整跑通训练闭环。
2. **前端可成功获取 STS 凭证并上传音频到 OSS**。
3. **训练提交后能轮询获取结果，显示 processing → completed 状态变化**。
4. **单句反馈包含词级时间戳**，前端可实现音频跳转功能（点击词或建议跳转到对应时间戳）。
5. 单句反馈能稳定生成并写入 `review_log`（`result_type=single`，`status=completed`）。
6. **AI 反馈不包含数值评分**，仅展示文字描述（pronunciation/completeness/fluency/suggestions）。
7. **异步失败（ASR/AI）时能正确返回 error_code 并阻断流程**（status=failed）。
8. 课级总结能自动生成并写入 `review_log`（`result_type=summary`）。
9. FSRS 调度按教材来源维度独立运作并可追踪。
10. Dashboard 能正确展示任务配置、连续学习天数与热力图。

## 10. 文档维护规则
- 若前后端实现细节变更，优先更新对应子文档，再回写本总纲的关键约束。
- 任何新的 PRD 草稿必须标注状态，不得与本文件并列为“最新版本”。
