# LanGear ADK 学习助手待办清单

## 目标

在保留现有 `single_feedback` 主链的前提下，新增一个基于 ADK 的多用户学习助手。该助手默认围绕当前 `lesson` 工作，支持独立流式聊天、答疑、总结、知识库检索、固定 B 站发音资源引用，以及对统一卡片体系的受控增删改。

## 关键约束

- 保留当前 `study submission -> review_task -> GeminiAdapter -> review_log.ai_feedback_json` 主链
- Agent 为旁路接口，不进入单句反馈评测主流程
- 默认按多用户设计，所有聊天、检索、卡片变更、FSRS、反馈数据都跟 `user_id` 走
- 默认上下文单位为 `user_id + lesson_id`
- 外部资源仅允许引用固定 B 站链接：
  - `https://www.bilibili.com/video/BV1Y4411M7Ac/?spm_id_from=333.337.search-card.all.click&vd_source=ed38c8a108bdf614c79b6ca89e859e4a`
- 内部知识库来自本地 Markdown 目录，通过后端受控 tools 检索
- 第一版不预写长期 memory；按需检索业务数据和知识库
- 卡片体系按 Anki 风格重构：`note + fields + card rendering`
- AI 可以对教材原卡做增删改，但必须经过草案、diff、用户确认、落库，并保留 mutation log 与回退能力

## 一、ADK Agent 主体

- [ ] 新增独立 `coach` 模块，不复用 `study/submissions`
- [ ] 设计 Lesson-first 的 ADK Coach Agent
- [ ] 为 agent 单独配置模型与 `base_url/gateway`
- [ ] 支持独立流式聊天接口
- [ ] 默认输入 `user_id + lesson_id + message + thread_id? + card_id?`
- [ ] 默认输出回答、引用、跳转目标、建议动作、卡片变更草案

## 二、聊天接口与线程

- [ ] 新增 `POST /api/v1/coach/chat` 流式接口
- [ ] 新增 `GET /api/v1/coach/threads/{thread_id}`
- [ ] 新增 `GET /api/v1/coach/threads/{thread_id}/messages`
- [ ] 为 thread/message 设计多用户隔离
- [ ] 流式事件至少支持：
  - [ ] `message_delta`
  - [ ] `citations`
  - [ ] `jump_targets`
  - [ ] `suggested_actions`
  - [ ] `mutation_draft`
  - [ ] `done`

## 三、上下文装配策略

- [ ] 实现当前卡片强上下文组装：
  - [ ] 原文
  - [ ] 翻译
  - [ ] 用户转写文本
  - [ ] 当前或最近一次 feedback JSON
  - [ ] 当前卡片最近 1-3 次历史表现
- [ ] 实现 lesson 弱上下文组装：
  - [ ] lesson 高频错误 summary
  - [ ] 近期相关卡片引用
  - [ ] lesson FSRS / 进度概览
- [ ] 实现用户全局上下文按需下钻，不默认进 prompt
- [ ] 实现上下文超长时的裁剪与压缩策略：
  - [ ] 保留当前卡完整上下文
  - [ ] 保留相关卡的完整记录
  - [ ] 其他记录压缩为 summary

## 四、业务 Tool 层

- [ ] 封装受控业务查询 tools，Agent 不直连 ORM/SQL
- [ ] 实现 `get_current_card_context(user_id, lesson_id, card_id?)`
- [ ] 实现 `get_lesson_feedback_history(user_id, lesson_id, card_id?, limit, cursor?)`
- [ ] 实现 `get_lesson_fsrs_overview(user_id, lesson_id)`
- [ ] 实现 `get_lesson_progress(user_id, lesson_id)`
- [ ] 实现 `get_user_global_patterns(user_id, limit?)`
- [ ] 统一 tool 输出 schema，方便 agent 稳定引用

## 五、知识库 RAG

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

## 六、固定 B 站资源引用

- [ ] 实现发音问题识别规则
- [ ] 仅在明确命中发音问题时引用固定 B 站链接
- [ ] 实现 `get_pronunciation_followup_resource(problem_type, phoneme?, word?)`
- [ ] 输出固定结构：`url + reason + target_problem`

## 七、统一卡片体系重构（Anki 风格）

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

## 八、AI 卡片增删改工作流

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

## 九、引用与跳转协议

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

## 十、测试与验收

- [ ] 验证 `coach/chat` 流式事件协议
- [ ] 验证多用户隔离：不同 `user_id` 不互串线程、上下文、卡片变更
- [ ] 验证当前卡片上下文完整返回
- [ ] 验证 lesson 历史裁剪与压缩逻辑
- [ ] 验证 Markdown RAG 命中率与引用输出
- [ ] 验证发音问题才会返回固定 B 站链接
- [ ] 验证卡片变更草案不会静默落库
- [ ] 验证确认后落库、回退后恢复
- [ ] 验证现有 `single_feedback`、轮询、FSRS 主链行为不变

## 十一、实施顺序建议

- [ ] 第 1 阶段：定义 `coach` 接口与 thread/message 持久化
- [ ] 第 2 阶段：封装业务查询 tools
- [ ] 第 3 阶段：接入 Markdown RAG
- [ ] 第 4 阶段：接入 ADK agent 与流式输出
- [ ] 第 5 阶段：补充固定 B 站发音资源引用
- [ ] 第 6 阶段：设计统一卡片模型与 mutation workflow
- [ ] 第 7 阶段：实现卡片草案、确认、回退
- [ ] 第 8 阶段：联调前端聊天、跳转、引用与卡片变更预览
