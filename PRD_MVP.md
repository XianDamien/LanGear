# PRD（MVP 版）：复述训练与 AI 反馈闭环

## 0. 文档定位（最新权威入口）
- 本文档是 Langear MVP 的唯一最新产品总纲。
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
- **ASR（语音转文本）**：阿里云语音服务（Paraformer），用于用户录音转写。
- **AI 多模态评测**：Google Gemini（gemini-2.5-flash），用于单句反馈与课级总结生成。Gemini 接收原文文本 + 用户转写文本（+ 可选音频）进行多维度评估。
- **对象存储**：阿里云 OSS，用于存储教材原音频与用户录音。

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
4. 翻面展示原文音频、原文文本、用户录音、转写文本与词块对齐结果，并生成 AI 单句反馈写入训练记录。
5. 管理员选择评分按钮（重来、困难、良好、简单）。
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
- Review Service：训练记录写入与查询。
- AI Evaluation Service：调用 Gemini 生成单句反馈与课级总结。
- ASR Service：调用阿里云语音服务完成用户录音转写。
- OSS Service：管理音频文件上传与 URL 签名。
- FSRS Service：卡片调度状态计算与更新。
- Settings Service：系统配置项读写。

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
- ai_feedback_json：AI 反馈结构化结果 JSON。
- created_at：创建时间。

### 6.6 settings
用于存储系统级配置项（每日任务数量、默认教材范围等）。
- id：主键，自增整数。
- key：配置项名称。
- value：配置项值（文本存储）。
- updated_at：更新时间。

## 7. AI 反馈规范

### 7.1 AI 服务选型
- **ASR 转写**：阿里云语音服务（Paraformer 模型）。后端接收用户音频后调用阿里云 ASR 获取转写文本。
- **多模态评测**：Google Gemini（gemini-2.5-flash）。后端将原文文本、用户转写文本（及可选的用户音频）发送至 Gemini，获取结构化反馈。
- API Key 通过环境变量配置（`GEMINI_API_KEY`、`ALIBABA_CLOUD_AK`、`ALIBABA_CLOUD_SK`），禁止硬编码。

### 7.2 单句反馈 JSON 结构
单句反馈必须包含发音准确度、内容完整度与流畅度三大核心指标，使用固定结构化字段：
```json
{
  "pronunciation": "发音评估描述",
  "completeness": "内容完整度评估描述",
  "fluency": "流畅度评估描述",
  "suggestions": ["改进建议1", "改进建议2"],
  "overall_score": 78
}
```

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
1. 音频上传失败时，必须阻止评分提交。
2. AI 单句反馈失败时，必须阻止卡片完成。
3. 课级总结生成失败时，必须阻止课文完成。
4. 数据库写入失败时，必须返回明确错误并禁止前端伪成功展示。

## 9. 验收标准
1. 新概念英语与剑桥雅思听力课文可完整跑通训练闭环。
2. 单句反馈能稳定生成并写入 `review_log`（`result_type=single`）。
3. 课级总结能自动生成并写入 `review_log`（`result_type=summary`）。
4. FSRS 调度按教材来源维度独立运作并可追踪。
5. Dashboard 能正确展示任务配置、连续学习天数与热力图。

## 10. 文档维护规则
- 若前后端实现细节变更，优先更新对应子文档，再回写本总纲的关键约束。
- 任何新的 PRD 草稿必须标注状态，不得与本文件并列为“最新版本”。
