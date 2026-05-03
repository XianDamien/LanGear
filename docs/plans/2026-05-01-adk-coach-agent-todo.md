# LanGear Agent 体系待办清单

## 总目标

在保留现有 `single_feedback` 主链的前提下，分阶段建设两类面向学习者的 Agent：

1. **答疑 / 总结 Agent**：围绕当前 `lesson` 与当前卡片，基于完整 feedback JSON、学习记录与内部知识库进行答疑、解释、总结与资源引用。
2. **端到端语音对话 Agent**：让用户在完成复述训练后，立即进入情景模拟对话，把刚学内容即时使用出来。

## 总体优先级

### P0：共享基础能力（两类 Agent 共用）
- [ ] 多用户上下文与 `user_id` 贯通
- [ ] 统一业务 Tool 层
- [ ] 当前卡片 / lesson 完整上下文装配
- [ ] Markdown 知识库 RAG
- [ ] 引用与跳转协议

### P1：答疑 / 总结 Agent（先落地）
- [ ] 独立聊天接口
- [ ] lesson / card 答疑
- [ ] lesson 内总结与问题归纳
- [ ] 发音问题时引用固定 B 站链接

### P2：端到端语音对话 Agent（第二阶段）
- [ ] 情景模拟入口
- [ ] 实时语音对话链路
- [ ] 基于当前 lesson 的角色扮演与任务推进
- [ ] 对话后复盘与迁移建议

### P3：统一卡片体系与 AI 增删改（后置）
- [ ] Anki 风格 `note + fields + card rendering` 重构
- [ ] AI 卡片草案、diff、确认、回退

## 关键约束

- 保留当前 `study submission -> review_task -> GeminiAdapter -> review_log.ai_feedback_json` 主链
- Agent 为旁路接口，不进入单句反馈评测主流程
- 默认按多用户设计，所有聊天、检索、卡片变更、FSRS、反馈数据都跟 `user_id` 走
- 默认上下文单位为 `user_id + lesson_id`，必要时细化到 `card_id`
- 答疑必须能获取当前卡片：原文、翻译、用户转写、对应 feedback JSON 等完整 context
- 内部知识库来自本地 Markdown 目录，通过后端受控 tools 检索
- 外部资源当前仅允许引用固定 B 站链接：
  - `https://www.bilibili.com/video/BV1Y4411M7Ac/?spm_id_from=333.337.search-card.all.click&vd_source=ed38c8a108bdf614c79b6ca89e859e4a`
- B 站链接只在明确识别到发音问题时作为跟练资源引用，不参与主知识检索
- 第一版不预写长期 memory；按需检索业务数据和知识库
- 后续统一卡片体系按 Anki 风格重构：`note + fields + card rendering`
- AI 可以对教材原卡做增删改，但必须经过草案、diff、用户确认、落库，并保留 mutation log 与回退能力

## 一、P0 共享基础能力（最高优先级）

### 1.1 多用户上下文
- [ ] 为 Agent 相关接口、线程、检索、卡片操作统一带上 `user_id`
- [ ] 明确 `lesson_id` 为默认上下文主键，`card_id` 为当前问题下钻键
- [ ] 设计 Agent thread / message 的多用户隔离

### 1.2 业务 Tool 层
- [ ] 封装受控业务查询 tools，Agent 不直连 ORM/SQL
- [ ] 实现 `get_current_card_context(user_id, lesson_id, card_id?)`
- [ ] 实现 `get_lesson_feedback_history(user_id, lesson_id, card_id?, limit, cursor?)`
- [ ] 实现 `get_lesson_fsrs_overview(user_id, lesson_id)`
- [ ] 实现 `get_lesson_progress(user_id, lesson_id)`
- [ ] 实现 `get_user_global_patterns(user_id, limit?)`
- [ ] 统一 tool 输出 schema，方便不同 Agent 复用

### 1.3 上下文装配策略
- [ ] 当前卡片强上下文：
  - [ ] 原文
  - [ ] 翻译
  - [ ] 用户转写文本
  - [ ] 当前或最近一次 feedback JSON
  - [ ] 当前卡片最近 1-3 次历史表现
- [ ] lesson 弱上下文：
  - [ ] lesson 高频错误 summary
  - [ ] 近期相关卡片引用
  - [ ] lesson FSRS / 进度概览
- [ ] 用户全局上下文只按需下钻，不默认进 prompt
- [ ] 实现上下文超长时的裁剪与压缩策略

### 1.4 Markdown 知识库 RAG
- [ ] 设计本地 Markdown 知识库索引器
- [ ] 约定最小 frontmatter：
  - [ ] `title`
  - [ ] `tags`
  - [ ] `aliases`
  - [ ] 可选 `problem_types`
- [ ] 实现 Markdown chunking
- [ ] 实现 tag 约束候选集筛选
- [ ] 实现 query rewrite / 总结改写
- [ ] 实现 `search_internal_kb(query, tags?, lesson_id?, card_id?, top_k=...)`
- [ ] 实现 `get_kb_document_chunk(doc_path, chunk_id)`
- [ ] 检索顺序固定为：
  - [ ] 当前 `lesson/card/context` 抽问题
  - [ ] query rewrite
  - [ ] tag 约束
  - [ ] chunk 检索
- [ ] 回答中强制附带知识库引用来源

### 1.5 引用与跳转协议
- [ ] 业务引用返回：
  - [ ] `source_type=card_feedback`
  - [ ] `lesson_id`
  - [ ] `card_id`
  - [ ] `review_log_id` 或 `submission_id`
- [ ] 知识库引用返回：
  - [ ] `source_type=knowledge_base`
  - [ ] `doc_path`
  - [ ] `chunk_id`
- [ ] 外部资源引用返回：
  - [ ] `source_type=external_resource`
  - [ ] 固定 `url`
- [ ] 前端支持基于这些引用跳转到卡片、反馈详情、知识片段、外部资源

## 二、P1 答疑 / 总结 Agent（先落地）

### 2.1 Agent 主体
- [ ] 新增独立 `coach` 模块，不复用 `study/submissions`
- [ ] 设计 Lesson-first 的 ADK Q&A Agent
- [ ] 为该 agent 单独配置模型与 `base_url/gateway`
- [ ] 默认输入 `user_id + lesson_id + message + thread_id? + card_id?`
- [ ] 默认输出回答、引用、跳转目标、建议动作

### 2.2 聊天接口与线程
- [ ] 新增 `POST /api/v1/coach/chat` 流式接口
- [ ] 新增 `GET /api/v1/coach/threads/{thread_id}`
- [ ] 新增 `GET /api/v1/coach/threads/{thread_id}/messages`
- [ ] 流式事件至少支持：
  - [ ] `message_delta`
  - [ ] `citations`
  - [ ] `jump_targets`
  - [ ] `resource_links`
  - [ ] `done`

### 2.3 能力范围
- [ ] 支持当前卡片答疑
- [ ] 支持 lesson 内问题总结与归纳
- [ ] 支持引用具体哪张卡 / 哪次反馈
- [ ] 支持基于内部知识库回答
- [ ] 在发音问题时补充固定 B 站跟练链接

### 2.4 固定 B 站资源引用
- [ ] 实现发音问题识别规则
- [ ] 实现 `get_pronunciation_followup_resource(problem_type, phoneme?, word?)`
- [ ] 输出固定结构：`url + reason + target_problem`
- [ ] 非发音问题不返回外部资源链接

### 2.5 测试与验收
- [ ] 验证 `coach/chat` 流式事件协议
- [ ] 验证多用户隔离：不同 `user_id` 不互串线程和上下文
- [ ] 验证当前卡片 context 完整返回
- [ ] 验证 lesson 历史裁剪与压缩逻辑
- [ ] 验证 Markdown RAG 命中率与引用输出
- [ ] 验证发音问题才会返回固定 B 站链接
- [ ] 验证现有 `single_feedback`、轮询、FSRS 主链行为不变

## 三、P2 端到端语音对话 Agent（第二阶段）

### 3.1 产品目标
- [ ] 用户完成复述训练后，可立即进入情景模拟对话
- [ ] 默认入口是：当前 `Lesson` 的全部卡片练完后，出现“进入情境对话”按钮
- [ ] 对话内容围绕当前 lesson 的主题、表达与问题点展开
- [ ] 目标是“即时学、即时用”，而不是再做一次单句评测

### 3.2 Agent 主体
- [ ] 新增独立的 Scenario / Dialogue Agent
- [ ] 与 Q&A Agent 分开建模与配置
- [ ] 支持场景驱动、角色扮演、任务推进式对话

### 3.3 语音链路
- [ ] 复用现有 realtime ASR 能力作为语音输入基础
- [ ] 设计端到端语音对话接口（独立于 `study/submissions`）
- [ ] 支持用户语音输入、Agent 文本/语音回复、轮次管理
- [ ] 明确 TTS 方案与接入边界（当前仓库尚未落地）

### 3.4 上下文与对话策略
- [ ] 默认围绕当前 `lesson` 构造情景
- [ ] 第一版只支持从 lesson 完成后的显式入口进入，不扩展到 Dashboard / Library / 历史重复进入
- [ ] 结合当前卡片、lesson 内问题、用户 recent feedback 生成对话目标
- [ ] 支持把用户刚练习的表达迁移到情景对话中
- [ ] 对话中尽量引用 lesson 内已有内容，而不是脱离教材自由发散

### 3.5 对话后复盘
- [ ] 对每次语音对话产出简要复盘
- [ ] 标记可迁移表达、常见错误、建议复练点
- [ ] 与 Q&A Agent 共享引用和跳转协议，方便回看具体卡片与反馈

### 3.6 测试与验收
- [ ] 验证对话可在 lesson 完成后顺畅进入
- [ ] 验证实时语音输入输出链路可用
- [ ] 验证对话内容与当前 lesson 保持相关
- [ ] 验证对话后复盘可以引用原卡片与原反馈

## 四、P3 统一卡片体系与 AI 增删改（后置）

### 4.1 统一卡片体系重构（Anki 风格）
- [ ] 设计统一卡片模型，完全参考 `note + fields + card rendering`
- [ ] 设计 `note_types`
- [ ] 设计 `note_field_defs`
- [ ] 设计 `notes`
- [ ] 设计 `note_field_values`
- [ ] 设计 `card_templates`
- [ ] 设计 `cards`
- [ ] 设计 `card_mutation_logs`
- [ ] 第一版先落最小 `voca` 基础闪卡能力
- [ ] 允许后续扩展更多 note/card 模式，而不再拆独立卡片体系

### 4.2 AI 卡片增删改工作流
- [ ] Agent 可对现有教材卡和其他卡片提出增删改草案
- [ ] 所有改动统一采用：
  - [ ] 草案生成
  - [ ] diff 预览
  - [ ] 用户确认
  - [ ] 正式落库
- [ ] 删除第一版仅做软删除 / 归档
- [ ] mutation log 至少记录：
  - [ ] `user_id`
  - [ ] `card_id`
  - [ ] `action`
  - [ ] `before_snapshot`
  - [ ] `after_snapshot`
  - [ ] `actor_type`
  - [ ] `reason`
  - [ ] `thread_id/message_id`
  - [ ] `created_at`
- [ ] 实现回退能力
- [ ] 新增确认接口与回退接口

### 4.3 测试与验收
- [ ] 验证卡片变更草案不会静默落库
- [ ] 验证确认后落库、回退后恢复
- [ ] 验证教材原卡变更的可审计性

## 五、实施顺序建议

- [ ] 第 1 阶段：定义共享 Tool 层、上下文装配与引用协议
- [ ] 第 2 阶段：接入 Markdown RAG
- [ ] 第 3 阶段：落地 Q&A Agent 的聊天接口与流式输出
- [ ] 第 4 阶段：补充发音问题的固定 B 站资源引用
- [ ] 第 5 阶段：联调前端答疑、跳转、引用
- [ ] 第 6 阶段：落地语音对话 Agent 的接口与实时链路
- [ ] 第 7 阶段：补充情景模拟策略与对话后复盘
- [ ] 第 8 阶段：统一卡片体系重构与 AI 增删改工作流
