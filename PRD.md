# 产品需求文档 (PRD): AI口语复盘功能

## 文档信息
- **版本**: 2.0
- **功能名称**: AI口语即时反馈与复盘系统
- **创建日期**: 2025年7月26日
- **最后更新**: 2025年1月17日
- **负责人**: AI口语复盘项目组

---

## 目录
1. [产品目标与愿景](#1-产品目标与愿景)
2. [系统架构设计](#2-系统架构设计)
3. [技术栈说明](#3-技术栈说明)
4. [数据库设计](#4-数据库设计)
5. [用户流程设计](#5-用户流程设计)
6. [模块功能设计](#6-模块功能设计)
7. [AI分析引擎](#7-ai分析引擎)
8. [API接口设计](#8-api接口设计)
9. [性能优化策略](#9-性能优化策略)
10. [部署和运维](#10-部署和运维)

---

## 1. 产品目标与愿景

本功能旨在通过先进的AI即时分析技术，为语言学习者提供一个高效、智能的口语练习闭环系统。我们采用**分离式微服务架构**，将复杂的AI分析过程无缝融入到用户的学习流程中，通过**AssemblyAI + Gemini双重AI引擎**实现深度语言分析，并通过**"单句详情" + "会话汇总" + "深度模式分析"**的三层反馈体系，帮助用户精准定位口语问题的根本原因，实现基于**"听口不分家"**理论的智能化语言学习体验。

### 核心创新点
- **分离式架构**: Backend + RetellingASR 微服务设计
- **异步处理机制**: 消除用户等待时间，提升体验流畅度  
- **深度AI汇总**: 基于Gemini的会话级智能分析和模式识别
- **存储优化**: 节省55.5%存储空间的优化架构
- **听口关联分析**: 独创的听力理解与口语产出关联诊断

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │  RetellingASR   │
│   (HTML/CSS/JS) │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   静态页面      │    │   端口: 8000    │    │   端口: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐        ┌─────────────┐
                       │ SQLite DB   │        │ SQLite DB   │
                       │ (langear.db)│        │(evaluation_ │
                       │             │        │ jobs.db)    │
                       └─────────────┘        └─────────────┘
                                                     │
                                                     ▼
                                              ┌─────────────┐
                                              │ AI Services │
                                              │ AssemblyAI  │
                                              │ + Gemini    │
                                              └─────────────┘
```

### 2.2 服务职责分工

#### **Backend服务 (端口8000)**
- **用户认证和授权**: 注册、登录、会话管理
- **学习内容管理**: 章节、卡片、音频文件管理
- **基础数据操作**: CRUD操作和数据验证
- **前端页面服务**: 静态文件服务和路由

#### **RetellingASR服务 (端口8001)**
- **ASR音频处理**: AssemblyAI语音转文本
- **AI深度分析**: Gemini语言分析和评估
- **异步任务管理**: 音频处理任务队列
- **会话级汇总**: 智能模式识别和听口关联分析

### 2.3 服务间通信

- **HTTP API调用**: Backend通过HTTP调用RetellingASR的API
- **会话ID关联**: 使用session_id作为两个服务间的数据关联键
- **异步处理**: 音频分析任务异步执行，不阻塞用户操作
- **状态同步**: 定期同步任务状态和分析结果

---

## 3. 技术栈说明

### 3.1 前端技术
- **基础技术**: HTML5 + CSS3 + 现代JavaScript
- **UI框架**: 原生DOM操作 + 现代ES6+语法
- **音频处理**: Web Audio API + MediaRecorder API
- **HTTP通信**: Fetch API + 双后端集成

### 3.2 Backend服务技术栈
- **Web框架**: FastAPI (异步高性能)
- **ORM框架**: SQLAlchemy (数据库操作)
- **数据库**: SQLite3 (嵌入式数据库)
- **认证系统**: 自定义认证 (无JWT简化版)
- **文件存储**: 本地文件系统 + 静态文件服务

### 3.3 RetellingASR服务技术栈
- **Web框架**: FastAPI (异步任务处理)
- **AI服务**: AssemblyAI (语音转文本) + Google Gemini (语言分析)
- **数据库**: SQLite3 (评估数据存储)
- **异步处理**: asyncio + BackgroundTasks
- **数据优化**: JSON存储优化 + 数据迁移机制

### 3.4 部署技术
- **容器化**: Docker + Docker Compose
- **服务发现**: 基于端口的服务路由
- **日志系统**: Python logging + 文件日志
- **监控**: 自定义健康检查API

---

## 4. 数据库设计

### 4.1 Backend项目数据库 (langear.db)

#### 4.1.1 表结构设计

**Table 1: users - 用户表**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Table 2: sections - 单元表**
```sql
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0
);
```

**Table 3: cards - 复述卡片内容表**
```sql
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL,
    original_text_en TEXT NOT NULL,
    original_text_cn TEXT,
    original_audio_url VARCHAR(255) NOT NULL,
    order_in_section INTEGER DEFAULT 0,
    FOREIGN KEY (section_id) REFERENCES sections(id)
);
```

**Table 4: practice_records - 用户练习记录表**
```sql
CREATE TABLE practice_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    user_audio_url VARCHAR(255) NOT NULL,
    fsrs_rating TEXT CHECK(fsrs_rating IN ('again', 'hard', 'good', 'easy')) NOT NULL,
    ai_analysis_status TEXT CHECK(ai_analysis_status IN ('pending', 'completed', 'failed')) NOT NULL DEFAULT 'pending',
    ai_analysis_result TEXT, -- JSON格式
    session_id VARCHAR(255), -- 关联到ASR会话
    asr_task_id INTEGER,     -- ASR任务ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (card_id) REFERENCES cards(id)
);
```

**Table 5: practice_sessions - 练习会话表**
```sql
CREATE TABLE practice_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    total_cards INTEGER NOT NULL,
    completed_cards INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active', -- active/completed/abandoned
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (section_id) REFERENCES sections(id)
);
```

### 4.2 RetellingASR项目数据库 (evaluation_jobs.db)

#### 4.2.1 核心表结构

**Table 1: asr_evaluations - ASR评估表**
```sql
CREATE TABLE asr_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    original_audio_path VARCHAR(255) NOT NULL,
    user_audio_path VARCHAR(255) NOT NULL,
    analysis_status TEXT CHECK(analysis_status IN ('pending', 'processing', 'completed', 'failed')) NOT NULL DEFAULT 'pending',
    single_analysis_result TEXT, -- JSON格式，优化后的分析结果
    transcribed_text TEXT,       -- 用户音频转录文本
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
```

**Table 2: practice_sessions - 练习会话管理表**
```sql
CREATE TABLE practice_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    total_cards INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active/completed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME
);
```

**Table 3: session_summaries - AI深度汇总表**
```sql
CREATE TABLE session_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    summary_analysis TEXT NOT NULL, -- JSON格式的AI深度汇总
    cards_analyzed INTEGER NOT NULL,
    total_cards INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Table 4: jobs - 向后兼容表**
```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id VARCHAR(255) NOT NULL,
    card_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(round_id, card_id)
);
```

#### 4.2.2 AI分析结果JSON结构

**single_analysis_result 字段结构 (优化后)**:
```json
{
  "meaning_fidelity": {
    "assessment": "核心意思已准确表达，但遗漏了一个关键细节",
    "missing_details": ["关键的时间信息"],
    "added_inaccuracies": []
  },
  "expression_comparison": {
    "summary": "您的表达清晰，但原文的表达更地道",
    "original_highlight": "原文中的'tackle the issue'是一个非常地道的搭配",
    "user_highlight": "您使用的'deal with the problem'也是一个很好的同义替换"
  },
  "fluency_and_rhythm": {
    "assessment": "整体节奏因逐词朗读而显得生硬，缺少自然的连贯性"
  },
  "critical_pronunciation_errors": [
    {
      "word": "three",
      "issue": "'three'中的/θ/音发得更像/s/，可能会被听成'see'"
    }
  ],
  "overall_score": 78
}
```

**summary_analysis 字段结构 (会话级AI汇总)**:
```json
{
  "performance_overview": {
    "comment": "本轮在意义传达上整体表现良好，核心信息基本准确",
    "final_score": 82,
    "analyzed_cards": 5
  },
  "pattern_analysis": {
    "meaning_fidelity_patterns": ["经常遗漏介词", "时间表达不够精确"],
    "pronunciation_patterns": ["th音替换为s音", "词尾辅音丢失"],
    "fluency_patterns": ["语速过慢", "停顿过多"]
  },
  "listening_speaking_correlation": {
    "key_insight": "您的听力理解困难主要源于自身口语习惯的局限性",
    "evidence_examples": [
      "在多个句子中将连读语块复述为孤立单词",
      "对弱读现象不敏感，影响了意思的准确理解"
    ]
  },
  "priority_focus_areas": {
    "top_language_points": ["连读技巧", "弱读识别"],
    "rationale": "掌握这些技巧将同时提升听力理解和口语自然度"
  }
}
```

### 4.3 数据库关联和同步

#### 4.3.1 跨服务数据关联
- **session_id**: 作为两个数据库间的主要关联键
- **user_id + card_id**: 用于数据验证和一致性检查
- **时间戳**: 用于数据同步和版本控制

#### 4.3.2 数据一致性策略
- **最终一致性**: 允许短暂的数据不一致，通过异步同步保证最终一致
- **补偿机制**: 自动检测和修复缺失的会话记录
- **数据迁移**: 支持数据结构变更的平滑迁移

---

## 5. 用户流程设计

### 5.1 完整用户流程

用户的核心体验分为五个阶段：**会话创建**、**卡片练习**、**异步分析**、**会话汇总** 和 **深度复盘**。

#### 5.1.1 阶段一：会话创建
1. **用户选择学习单元**: 从sections列表中选择要练习的单元
2. **系统创建练习会话**: 
   - Backend调用RetellingASR的`/api/v1/asr/create-session`接口
   - 生成唯一的session_id (格式: `session_{timestamp}_{random}`)
   - 在两个数据库中记录会话信息
3. **会话初始化完成**: 用户进入第一张卡片练习

#### 5.1.2 阶段二：卡片练习循环
1. **卡片正面 - 练习与录音**:
   - 用户收听标准音频（可重复播放）
   - 用户进行口语复述录音（支持多次录音，保留最新）
   - 录音完成后出现"提交"按钮

2. **卡片背面 - 自我评估**:
   - 显示原音频+英文原文
   - 显示用户录音+预览（等待AI转录）
   - 用户选择FSRS评分：[重来/困难/良好/容易]

3. **异步任务触发**:
   - 用户点击评分按钮后，音频立即上传到RetellingASR服务
   - 系统调用`/api/v1/asr/submit-evaluation`接口
   - 返回task_id，开始异步处理

4. **进入下一张卡片**: 不等待分析完成，用户继续练习

#### 5.1.3 阶段三：异步AI分析 (后台进行)
1. **音频转录**: 使用AssemblyAI将用户音频和标准音频转为文本
2. **深度分析**: 使用Gemini进行语言对比分析
3. **结果存储**: 将分析结果存储到asr_evaluations表
4. **汇总触发**: 当会话完成度达到80%时，自动触发AI深度汇总

#### 5.1.4 阶段四：会话汇总
1. **进入总结页面**: 用户完成所有卡片后，进入section-summary页面
2. **状态检查**: 前端检查会话状态和分析完成情况
3. **AI深度汇总显示**:
   - 如果已有汇总，直接显示
   - 如果未生成，调用`/api/v1/asr/session-summary/{session_id}`自动生成
4. **单句列表**: 显示本单元所有句子和"查看详情"入口

#### 5.1.5 阶段五：深度复盘
1. **查看单句详情**: 点击"查看详情"进入detail-card页面
2. **详细分析展示**:
   - 意义保真度分析
   - 表达方式对比
   - 流畅度评估
   - 关键发音错误
3. **模式识别洞察**: 基于"听口不分家"理论的深度分析

### 5.2 异步处理机制

#### 5.2.1 任务状态管理
- **pending**: 任务已提交，等待处理
- **processing**: 正在进行AI分析
- **completed**: 分析完成，结果可用
- **failed**: 分析失败，包含错误信息

#### 5.2.2 用户体验优化
- **无等待**: 用户无需等待AI分析完成即可继续练习
- **渐进式加载**: 分析完成的句子逐步在总结页显示
- **错误恢复**: 失败的任务支持重试机制

---

## 6. 模块功能设计

### 6.1 模块一：复述卡片（正面）

#### 6.1.1 布局设计
- **原音频播放器**: 标准发音播放按钮，支持重复播放
- **用户录音模块**: 录音按钮，实时录音状态显示
- **提交按钮**: 录音完成后显示，点击进入背面

#### 6.1.2 功能实现
- **无限重听**: 用户可反复收听标准发音
- **录音覆盖**: 支持多次录音，系统保留最新录音
- **会话管理**: 确保录音与当前session_id关联

#### 6.1.3 新增功能
- **会话初始化**: 首次进入时自动创建练习会话
- **进度显示**: 显示当前卡片在单元中的位置

### 6.2 模块二：复述卡片（背面/自评页）

#### 6.2.1 布局设计
- **原声模块**: 原音频播放器 + 英文原文显示
- **用户录音模块**: 用户录音播放器 + 转录文本预览区域
- **自评按钮组**: [重来/困难/良好/容易] 四个FSRS评分按钮
- **状态指示器**: 显示音频上传和分析状态

#### 6.2.2 功能增强
- **异步上传**: 点击评分后立即上传音频，不阻塞界面
- **状态反馈**: 实时显示"上传中"、"分析中"等状态
- **错误处理**: 上传失败时提供重试选项
- **渐进式显示**: AI转录完成后动态更新转录文本

#### 6.2.3 新增功能
- **任务追踪**: 记录ASR任务ID，支持状态查询
- **会话关联**: 确保评分记录与session_id正确关联

### 6.3 模块三：环节总结页

#### 6.3.1 布局设计重大更新
- **页面标题**: "环节总结" + 会话状态指示
- **AI深度汇总区**: 全新的AI分析结果展示区域，包含：
  - 本轮表现快照 (performance_overview)
  - 关键模式分析 (pattern_analysis)  
  - 听口关联洞察 (listening_speaking_correlation)
  - 优先关注点 (priority_focus_areas)
- **逐句列表区**: 动态加载的句子列表，显示分析状态
- **操作按钮**: [完成] [继续下一单元] [生成AI汇总]

#### 6.3.2 功能实现
- **动态加载**: 根据异步分析进度动态展示内容
- **智能等待**: 自动检测会话完成度，触发AI汇总生成
- **状态同步**: 实时同步RetellingASR服务的分析状态

#### 6.3.3 新增核心功能
- **AI深度汇总**: 基于Gemini的会话级智能分析
- **模式识别**: 跨句子的系统性问题识别
- **听口关联分析**: 听力理解与口语产出的关联洞察
- **手动触发**: 支持手动触发AI汇总生成

### 6.4 模块四：详情卡片页（全面升级）

#### 6.4.1 布局设计升级
- **导航区**: 返回按钮 + 卡片信息（卡片X/总数Y）
- **原声模块**: 原音频播放器 + 英文原文
- **用户录音模块**: 用户录音播放器 + AI转录文本
- **AI深度分析区**: 全新的多维度分析展示
  - 意义保真度 (meaning_fidelity)
  - 表达方式对比 (expression_comparison)
  - 流畅度与节奏 (fluency_and_rhythm)
  - 关键发音错误 (critical_pronunciation_errors)
  - 综合评分 (overall_score)

#### 6.4.2 数据源升级
- **数据来源**: 从RetellingASR服务获取详细分析结果
- **API调用**: `/api/v1/asr/session/{session_id}/card/{card_id}/evaluation`
- **实时同步**: 支持分析结果的实时更新

#### 6.4.3 新增分析维度
- **意义保真度**: 核心信息传达准确性分析
- **表达对比**: 用户表达与标准表达的地道性对比
- **听口关联**: 基于"听口不分家"理论的深度洞察
- **个性化建议**: 针对性的改进建议

---

## 7. AI分析引擎

### 7.1 双重AI架构

#### 7.1.1 AssemblyAI集成
- **功能**: 高精度语音转文本 (Speech-to-Text)
- **处理对象**: 用户录音 + 标准音频
- **输出**: 转录文本 + 音频特征数据
- **优势**: 专业ASR服务，支持多种音频格式

#### 7.1.2 Google Gemini集成
- **功能**: 深度语言分析和对比
- **模型**: gemini-2.5-flash (高性能版本)
- **处理对象**: 转录文本对比分析
- **输出**: 结构化的语言分析报告

### 7.2 分析维度详解

#### 7.2.1 意义保真度 (Meaning Fidelity)
- **核心评估**: 用户复述的核心意思准确性
- **分析指标**: 
  - 关键信息遗漏 (missing_details)
  - 不准确添加 (added_inaccuracies)
  - 整体意思评估 (assessment)

#### 7.2.2 表达方式对比 (Expression Comparison)
- **对比维度**: 地道性、简洁性、准确性
- **分析内容**:
  - 原文亮点词汇/表达识别
  - 用户表达的优点发现
  - 表达方式对比总结

#### 7.2.3 流畅度与节奏 (Fluency and Rhythm)
- **评估重点**: 自然连贯性、语音节奏
- **问题识别**: 逐词朗读、不自然停顿、语速问题

#### 7.2.4 关键发音错误 (Critical Pronunciation Errors)
- **筛选标准**: 影响理解的严重发音问题
- **错误类型**: 音素替换、音素遗漏、重音错误
- **改进建议**: 具体的发音纠正指导

### 7.3 听口关联分析理论

#### 7.3.1 "听口不分家"核心理念
- **理论基础**: 听力理解困难往往源于口语产出习惯的局限
- **分析逻辑**: "因为你不会这样说，所以你很难听懂"
- **应用场景**: 连读、弱读、语音变化的理解和产出

#### 7.3.2 模式识别机制
- **跨句子聚合**: 识别用户在多个句子中的系统性问题
- **根本原因分析**: 找出听力和口语问题的共同根源
- **个性化诊断**: 基于用户具体表现的精准分析

### 7.4 AI汇总生成机制

#### 7.4.1 触发条件
- **自动触发**: 会话完成度达到80%时自动生成
- **手动触发**: 用户或系统管理员手动请求生成
- **重新生成**: 支持汇总结果的更新和优化

#### 7.4.2 汇总内容
- **表现快照**: 本轮练习的整体评价和评分
- **模式分析**: 系统性问题的识别和归类
- **听口关联**: 听力理解和口语产出的关联洞察
- **改进建议**: 优先级最高的学习重点

---

## 8. API接口设计

### 8.1 Backend服务API (端口8000)

#### 8.1.1 认证相关接口

**POST /api/v1/auth/register**
- 功能: 用户注册
- 请求体: `{username, email, password}`
- 响应: 用户信息

**POST /api/v1/auth/login**
- 功能: 用户登录
- 请求体: `{email, password}`
- 响应: `{access_token, user}`

**GET /api/v1/auth/me**
- 功能: 获取当前用户信息
- 响应: 用户详细信息

#### 8.1.2 练习管理接口

**POST /api/v1/practice/sessions**
- 功能: 创建练习会话
- 请求体: `{section_id}`
- 响应: `{session_id, user_id, section_id, total_cards}`

**GET /api/v1/practice/sessions/{session_id}/status**
- 功能: 获取会话状态
- 响应: 会话状态和进度信息

**POST /api/v1/practice/**
- 功能: 创建练习记录(用户自评后)
- 请求体: `{card_id, fsrs_rating, session_id}`
- 响应: 练习记录信息

**GET /api/v1/practice/{record_id}**
- 功能: 获取练习记录详情
- 响应: 完整的练习记录和分析结果

### 8.2 RetellingASR服务API (端口8001)

#### 8.2.1 会话管理接口

**POST /api/v1/asr/create-session**
- 功能: 创建ASR分析会话
- 请求体: `{user_id, section_id, total_cards}`
- 响应: `{session_id, message}`

**GET /api/v1/asr/session-status/{session_id}**
- 功能: 获取会话分析状态
- 响应: `{session_id, total_tasks, completed_tasks, is_ready_for_summary}`

#### 8.2.2 音频分析接口

**POST /api/v1/asr/submit-evaluation**
- 功能: 提交音频分析任务
- 请求体: `{user_id, section_id, card_id, session_id, practice_audio_path, original_audio_path}`
- 响应: `{task_id, message, status}`

**GET /api/v1/asr/task-status/{task_id}**
- 功能: 查询任务状态
- 响应: `{task_id, status, progress, completed_at, error_message}`

#### 8.2.3 汇总分析接口

**GET /api/v1/asr/session-summary/{session_id}**
- 功能: 获取会话总结(自动生成AI汇总)
- 参数: `deep_analysis=true` (默认启用AI深度汇总)
- 响应: 完整的会话总结和AI汇总

**POST /api/v1/asr/session-summary/{session_id}/generate**
- 功能: 手动触发AI汇总生成
- 响应: `{message, summary}`

#### 8.2.4 详细分析接口

**GET /api/v1/asr/session/{session_id}/card/{card_id}/evaluation**
- 功能: 获取特定卡片的详细分析结果
- 响应: 完整的单句分析结果

### 8.3 错误处理和状态码

#### 8.3.1 标准HTTP状态码
- **200**: 成功
- **201**: 创建成功
- **202**: 已接受(异步任务)
- **400**: 请求错误
- **401**: 未授权
- **404**: 资源不存在
- **500**: 服务器内部错误

#### 8.3.2 自定义错误格式
```json
{
  "error": "错误类型",
  "message": "详细错误信息",
  "details": "额外的调试信息",
  "timestamp": "2025-01-17T10:30:00Z"
}
```

---

## 9. 性能优化策略

### 9.1 存储架构优化

#### 9.1.1 数据结构优化
- **存储空间节省**: 通过LAN-30项目优化，节省55.5%存储空间
- **JSON结构精简**: 移除冗余的source_data字段，只保留essential evaluation_report
- **数据分层存储**: 单句分析 + 会话汇总 + 用户统计的分层架构

#### 9.1.2 数据迁移机制
- **向后兼容**: 支持旧数据格式的自动识别和转换
- **渐进式迁移**: 不中断服务的数据结构升级
- **数据校验**: 迁移后的数据完整性检查

### 9.2 异步处理优化

#### 9.2.1 任务队列设计
- **非阻塞提交**: 音频分析任务异步提交，立即返回task_id
- **并行处理**: AssemblyAI和音频预处理并行执行
- **智能重试**: 失败任务的自动重试机制

#### 9.2.2 用户体验优化
- **渐进式加载**: 分析完成的内容逐步显示
- **状态实时同步**: WebSocket或轮询更新任务状态
- **无等待设计**: 用户操作不受AI分析速度影响

### 9.3 缓存策略

#### 9.3.1 数据缓存
- **会话状态缓存**: 减少数据库查询频率
- **分析结果缓存**: 避免重复的AI分析调用
- **静态资源缓存**: 音频文件的浏览器缓存策略

#### 9.3.2 API调用优化
- **批量处理**: 多个音频文件的批量分析
- **请求合并**: 减少不必要的API调用
- **错误率监控**: 实时监控AI服务的可用性

---

## 10. 部署和运维

### 10.1 容器化部署

#### 10.1.1 Docker配置
```dockerfile
# Backend服务
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# RetellingASR服务  
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 10.1.2 Docker Compose配置
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/db:/app/db
      - ./backend/uploads:/app/uploads
      - ./frontend:/app/frontend
    
  retelling-asr:
    build: ./RetellingASR
    ports:
      - "8001:8001"
    volumes:
      - ./RetellingASR:/app
    environment:
      - ASSEMBLYAI_API_KEY=${ASSEMBLYAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

### 10.2 环境配置

#### 10.2.1 必需的环境变量
```bash
# RetellingASR服务
ASSEMBLYAI_API_KEY=your_assemblyai_key
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL_NAME=gemini-2.5-flash

# Backend服务
DATABASE_URL=sqlite:///./db/langear.db
SECRET_KEY=your_secret_key
```

#### 10.2.2 目录结构
```
/opt/Langear/
├── backend/                 # Backend服务
│   ├── app/                 # 应用代码
│   ├── db/                  # 数据库文件
│   ├── uploads/             # 上传文件
│   └── requirements.txt     # Python依赖
├── RetellingASR/            # ASR服务
│   ├── main.py              # 服务入口
│   ├── database.py          # 数据库管理
│   ├── evaluation_jobs.db   # ASR数据库
│   └── requirements.txt     # Python依赖
├── frontend/                # 前端文件
│   ├── *.html               # 页面文件
│   ├── css/                 # 样式文件
│   └── js/                  # 脚本文件
└── docker-compose.yml       # 容器编排
```

### 10.3 监控和日志

#### 10.3.1 日志配置
- **详细日志**: 所有API调用和错误的详细记录
- **日志分级**: DEBUG/INFO/WARNING/ERROR分级管理
- **日志轮转**: 防止日志文件过大的轮转策略

#### 10.3.2 健康检查
```python
# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "backend/retelling-asr",
        "version": "2.0"
    }
```

#### 10.3.3 性能监控
- **API响应时间**: 监控各接口的响应性能
- **错误率统计**: AI服务调用的成功率监控
- **资源使用**: CPU、内存、磁盘使用情况

### 10.4 数据备份策略

#### 10.4.1 数据库备份
```bash
# 自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp backend/db/langear.db "backup/langear_${DATE}.db"
cp RetellingASR/evaluation_jobs.db "backup/evaluation_jobs_${DATE}.db"
```

#### 10.4.2 音频文件备份
- **定期备份**: 用户录音文件的定期备份
- **云存储**: 考虑使用云存储服务进行异地备份
- **版本控制**: 重要配置文件的版本控制

---

## 总结

本PRD文档详细描述了AI口语复盘系统的完整架构设计和实现方案。系统采用分离式微服务架构，通过Backend和RetellingASR两个服务的协同工作，实现了高效的语音分析和智能反馈功能。

### 核心特性
1. **分离式架构**: 清晰的服务职责分工和高可扩展性
2. **异步处理**: 用户体验流畅，无需等待AI分析完成
3. **深度AI分析**: 基于"听口不分家"理论的智能语言分析
4. **存储优化**: 节省55.5%存储空间的优化数据结构
5. **完整的用户流程**: 从练习到复盘的完整闭环体验

### 技术优势
- **现代化技术栈**: FastAPI + SQLAlchemy + AI服务集成
- **高性能异步处理**: 支持高并发的音频分析任务
- **智能化分析**: AssemblyAI + Gemini双重AI引擎
- **可扩展架构**: 支持未来功能扩展和服务拆分

该系统为语言学习者提供了一个智能、高效、体验优良的口语练习平台，通过先进的AI技术帮助用户精准定位口语问题并持续改进。
