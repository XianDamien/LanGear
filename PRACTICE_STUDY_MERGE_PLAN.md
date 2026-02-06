# Practice + Study 合并计划

## 现状分析

### practice.py 现有功能
| 端点 | 功能 | 核心职责 |
|------|------|----------|
| `POST /sessions` | 创建会话 | 调用 ASR 服务创建会话 |
| `GET /sessions/{session_id}/status` | 获取会话状态 | 代理 ASR 服务状态 |
| `GET /sessions/{session_id}/summary` | 获取会话总结 | 代理 ASR 服务总结 |
| `POST /sessions/{session_id}/summary/generate` | 触发生成总结 | 触发 ASR 深度分析 |
| `POST /` | 创建练习记录 | 单卡提交 + ASR 分析 |
| `GET /{record_id}` | 获取记录详情 | 查询 review_log |
| `GET /user/history` | 获取历史 | 查询 review_log |
| `GET /task-status/{task_id}` | ASR 任务状态 | 代理 ASR 任务状态 |

### study.py 新功能 (FSRS 批量模式)
| 端点 | 功能 | 核心职责 |
|------|------|----------|
| `POST /start` | 启动批次 | FSRS 卡片选择 + 批次创建 |
| `GET /batch/{batch_id}` | 恢复批次 | 查询 practice_sessions |
| `POST /review` | 提交复习 | FSRS 调度更新 + review_log |
| `POST /summary` | 批次总结 | 本地总结记录 |
| `GET /active` | 获取活跃批次 | 查询 practice_sessions |
| `GET /stats` | 学习统计 | 统计 user_card_srs |

## 问题

1. **会话创建重复**: practice `/sessions` vs study `/start`
2. **记录提交重复**: practice `POST /` vs study `/review`
3. **总结功能重复**: practice `/sessions/{id}/summary` vs study `/summary`
4. **数据表共享**: 都用 `practice_sessions` 和 `review_log`

## 学习模式定义

### 三种模式的区别

| 模式 | 范围 | 卡片类型 | 使用场景 |
|------|------|----------|----------|
| **learn** | 全局 | 只有新卡 | Dashboard "学习新卡" |
| **review** | 全局 | 只有到期复习卡 | Dashboard "复习到期" |
| **section** | 某章节 | 新卡 + 学习中 + 复习 (Anki风格混合) | 点击某个章节 |

### FSRS 卡片状态映射

```
py-fsrs State:
├── State.Learning (1)   → 学习中
├── State.Review (2)     → 复习中
└── State.Relearning (3) → 重新学习中
```

### Section 模式卡片选择逻辑 (Anki deck 风格)

```python
def get_section_cards(section_id, user_id, limit=10):
    # 1. 新卡: 该章节内用户没学过的
    new_cards = cards WHERE section_id = X
                AND card_id NOT IN user_card_srs

    # 2. 学习中: 该章节内正在学习/重新学习的
    learning_cards = user_card_srs WHERE section_id = X
                     AND state IN (1, 3)  # Learning, Relearning

    # 3. 复习卡: 该章节内到期的复习卡
    review_cards = user_card_srs WHERE section_id = X
                   AND state = 2  # Review
                   AND due <= now

    # 混合排序 (Anki 风格: 复习优先 → 学习中 → 新卡穿插)
    return mix_cards(review_cards, learning_cards, new_cards, limit)
```

## 合并方案

### 核心原则
- **practice_sessions** = 统一的学习批次表
- **review_log** = 统一的复习记录表
- **每次复习同时更新 FSRS 状态**
- **ASR 分析作为可选增强功能**

### 合并后的端点设计

```
/api/v1/practice/
├── POST   /start                    # [NEW] 启动批次 (支持 learn/review/section 模式)
├── GET    /batch/{batch_id}         # [NEW] 恢复批次
├── GET    /active                   # [NEW] 获取活跃批次
├── GET    /stats                    # [NEW] 学习统计
│
├── POST   /review                   # [MERGED] 提交单卡复习 (FSRS + 可选ASR)
├── GET    /{record_id}              # [KEEP] 获取记录详情
├── GET    /history                  # [RENAME] 用户历史 (从 /user/history)
│
├── POST   /batch/{batch_id}/summary          # [MERGED] 创建/获取批次总结
├── POST   /batch/{batch_id}/summary/generate # [KEEP] 触发 ASR 深度分析
├── GET    /batch/{batch_id}/status           # [RENAME] 批次状态 (从 sessions)
│
└── GET    /task-status/{task_id}    # [KEEP] ASR 任务状态
```

### 废弃的端点
- `POST /sessions` → 替换为 `POST /start`
- `GET /sessions/{session_id}/status` → 替换为 `GET /batch/{batch_id}/status`
- `GET /sessions/{session_id}/summary` → 替换为 `POST /batch/{batch_id}/summary`
- `POST /` → 替换为 `POST /review`

### 关键改动

#### 1. `POST /start` - 统一启动批次
```python
class BatchStartRequest(BaseModel):
    mode: StudyMode              # learn | review | section
    section_id: Optional[int]    # required for section mode
    limit: int = 10
    enable_asr: bool = False     # 是否启用 ASR 分析

# 流程:
# 1. 根据 mode 选择卡片 (FSRS 逻辑)
# 2. 创建 practice_sessions 记录
# 3. 如果 enable_asr=True, 调用 ASR 服务创建会话
```

#### 2. `POST /review` - 统一复习提交
```python
class ReviewRequest(BaseModel):
    batch_id: int
    card_id: int
    fsrs_rating: FSRSRating
    user_audio_url: Optional[str]     # 用户音频 (ASR 模式需要)
    review_duration_ms: Optional[int]
    user_input: Optional[str]

# 流程:
# 1. 验证 batch 和 card
# 2. 更新 user_card_srs (FSRS 调度)
# 3. 写入 review_log
# 4. 如果有 user_audio_url, 触发 ASR 分析
# 5. 更新 batch cursor
```

#### 3. `POST /batch/{batch_id}/summary` - 统一总结
```python
# 流程:
# 1. 如果 batch 关联了 ASR session, 获取 ASR 深度分析
# 2. 否则返回本地统计总结
# 3. 写入 review_log (record_type=summary)
```

## 迁移步骤

### Phase 1: 准备
- [ ] 备份现有 practice.py
- [ ] 创建 practice_merged.py (新实现)

### Phase 2: 实现合并版本
- [ ] 实现 `POST /start` (整合 FSRS 选卡 + 可选 ASR 会话)
- [ ] 实现 `POST /review` (整合 FSRS 更新 + 可选 ASR 分析)
- [ ] 实现 `POST /batch/{batch_id}/summary` (整合本地总结 + ASR 总结)
- [ ] 移植其他端点 (stats, active, history, task-status)

### Phase 3: 切换
- [ ] 删除 study.py
- [ ] 用 practice_merged.py 替换 practice.py
- [ ] 更新 api.py 路由注册
- [ ] 更新 schemas.py (清理重复)

### Phase 4: 验证
- [ ] 编译检查
- [ ] 端点测试
- [ ] 更新 FSRS_refactor_plan.md

## 数据流示意

```
[Dashboard]                    [Section 页面]
    |                              |
    v                              v
POST /start                   POST /start
(mode=learn/review)           (mode=section, section_id=X)
    |                              |
    +----------+-------------------+
               |
               v
        practice_sessions
        (card_ids, cursor, mode)
               |
               v
        POST /review  <----循环10次---+
               |                      |
    +----------+-----------+          |
    |                      |          |
    v                      v          |
user_card_srs          review_log     |
(FSRS状态)             (复习记录)      |
    |                      |          |
    |    [可选 ASR]        |          |
    |         |            |          |
    |         v            |          |
    |    ASR服务分析       |          |
    |         |            |          |
    |         v            |          |
    |    ai_analysis_result|          |
    |                      |          |
    +----------+-----------+          |
               |                      |
               +----------------------+
               |
               v
        POST /batch/{id}/summary
               |
               v
        review_log (record_type=summary)
```

## 注意事项

1. **向后兼容**: 旧的 session_id 查询需要支持一段时间
2. **ASR 可选**: 不是所有复习都需要 ASR 分析
3. **batch_id vs session_id**: 统一使用 batch_id (practice_sessions.id)
4. **错误处理**: ASR 服务不可用时不影响 FSRS 功能
