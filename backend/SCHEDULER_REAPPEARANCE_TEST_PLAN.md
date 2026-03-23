# LangGear 同 Lesson 到期复现测试计划

## 1. 背景与目标

这份文档用于指导后端同事补齐一组更具体的调度验证测试，确认以下业务行为在当前 LangGear 调度下成立：

1. 在同一个 `lesson` 牌组中，用户已经学习过的卡片不会在同一天、同一次学习流里立刻复现。
2. 同一张卡在经过若干天、到达 `due` 日期后，会重新进入 `GET /api/v1/study/session?lesson_id=...` 返回集合，前端因此再次提示用户上传录音并进行复习。
3. 同一张卡的多次复习必须保留完整历史 trace，而不是被“去重覆盖”成一条记录。

这次的重点不是前端视觉验证，而是通过后端 API、数据库状态和自动化测试，明确证明“不会当日即时复现，但会在到期后重新出现”。

## 1.1 先对齐一个关键认知

结合当前代码，产品想法和实际实现大方向是一致的，但需要避免两个误解：

- 误解一：“系统有一个硬编码规则，规定已学卡同一天绝不复现”
  - 当前代码里并没有单独的“同一天禁止复现”规则。
  - 真正决定卡片是否重新进入 session 的条件是 `user_card_srs.due <= now`。
  - 之所以看起来像“同一天不会回来”，是因为评分后 FSRS 通常会把 `due` 推到未来。
- 误解二：“前端会在当前 lesson 页面里自动把这张卡重新插回队列”
  - 当前前端没有这条逻辑。
  - 前端只会在重新请求 `GET /api/v1/study/session` 后，基于后端返回的 `cards[]` 再次看到这张卡。

因此，后端同事在实现测试时，应把目标写成：

- 验证“due 驱动回归”
- 验证“历史 trace 保留”
- 不要把“同一天不复现”测试写成基于自然日的硬编码规则
- 不要把前端本地队列行为和后端重新供给 session 的行为混为一谈

## 2. 当前代码事实

### 2.1 当前 session 生成逻辑

- `GET /api/v1/study/session` 由 `backend/app/services/study_session_service.py` 生成。
- 当前返回顺序是：
  1. 已到期的 `learning/relearning`
  2. 已到期的 `review`
  3. 新卡桶
- 已学习过的卡片是否进入 session，关键取决于 `user_card_srs.due <= now`。
- `SRSRepository.get_due_cards()` 明确排除了 `last_review IS NULL` 的新卡桶，只会返回真正完成过至少一次评分的卡。

### 2.2 当前评分与落库逻辑

- 评分入口是 `POST /api/v1/study/submissions/{submission_id}/rating`。
- 评分后调用 `FSRSAdapter.schedule_card(...)`，将新的：
  - `state`
  - `step`
  - `due`
  - `last_review`
  - `stability`
  - `difficulty`
  写回 `user_card_srs`。
- 同时会新增一条 `fsrs_review_log`。
- 每次提交录音任务时，也会新增一条 `review_log`。

### 2.3 当前历史 trace 现状

当前实现天然更接近“保留历史”而不是“覆盖历史”：

- `review_log` 是 append-only，新提交会新建一条记录，不会按 `card_id + day` 去重更新。
- `fsrs_review_log` 也是 append-only，每次评分新增一条记录。
- `user_card_srs` 只保存“当前最新快照”，不是历史表。

这意味着：

- 一张卡可以保留多次提交、多次评分、多次 due 演进的历史。
- 需要补充的不是“新增历史表”，而是测试验证当前行为不会被后续改动破坏。

### 2.4 当前前端关于“再次上传/复习”的真实触发方式

这部分虽然不要求后端改代码，但需要在测试结论里写清楚，否则很容易误读。

- 前端在进入 lesson 时会加载一次 `GET /api/v1/study/session`。
- 评分成功后，前端只会更新当前卡的本地元数据，然后跳到下一张。
- 前端不会在评分后自动 refetch 当前 lesson session。
- 前端也不会把同一张卡重新插回当前本地 `cards[]` 队列。

因此，“再次提示上传和复习”在当前系统里的准确含义是：

- 这张卡在未来某次重新进入 lesson 时，后端再次把它包含进 `GET /api/v1/study/session?lesson_id=...` 返回的 `cards[]`
- 前端随后把它当成普通待学习卡再次展示

这也是为什么本次测试重点应该放在 session inclusion contract，而不是放在前端页面即时行为。

## 3. 需要验证的业务结论

后端测试需要最终给出下面三个明确答案：

### A. 已学卡会不会在同一天立即复现

预期结论：

- 不会因为刚刚完成一次评分，就立刻重新进入当前 lesson 的同一轮 `study/session`。
- 只有在新的 `due` 到点后，它才有资格再次进入 session。
- 这里的真实规则是“基于 due 判断”，不是“基于自然日判断”。

### B. 到了 `due` 之后会不会重新出现

预期结论：

- 会。
- 当同一张已学卡的 `user_card_srs.due` 小于等于当前时间时，再次请求 `GET /api/v1/study/session?lesson_id=...`，该卡应该重新进入返回的 `cards[]`。

### C. 历史复习 trace 会不会被去重覆盖

预期结论：

- 不会。
- 同一张卡的两次独立复习，应该产生两条不同的 `review_log`。
- 如果两次都完成评分，还应产生两条不同的 `fsrs_review_log`。
- `user_card_srs` 可以被更新为最新快照，但历史日志不能被覆盖。

## 4. 本次建议新增的测试范围

## 4.1 核心范围

- 限定在同一个 `lesson` 内验证同一张卡的调度闭环。
- 重点覆盖“已学卡”而不是“新卡首学”。
- 重点覆盖 `good` 和 `again` 两类场景：
  - `good` 代表正常复习后排到未来
  - `again` 代表复习失败后进入更近的再次复习窗口

### 4.2 非目标

- 不在本轮测试中验证前端页面文案或按钮文案。
- 不依赖手工等待几天。
- 不把重点放在不同 source_scope 或跨 lesson 混合调度。
- 不改动 README、PRD、PRD_BASELINE。

## 5. 建议测试设计

## 5.1 测试文件落点

建议新增或扩展以下测试文件：

- `backend/tests/integration/test_study_router.py`
  - 负责验证“提交评分后如何落库，以及是否保留多次历史”
- `backend/tests/integration/test_study_session_router.py`
  - 负责验证“到 due 后是否重新进入同 lesson 的 session”

如需把逻辑拆得更清晰，也可以新增：

- `backend/tests/integration/test_study_reappearance_flow.py`

如果新增文件，请保持命名直接表达“reappearance / due return / history trace”。

## 5.2 测试数据准备

每个用例都尽量使用一棵最小 lesson 树，至少包含：

- 1 个 source
- 1 个 unit
- 1 个 lesson
- 1 张目标测试卡
- 可选 1~2 张干扰卡，用于确认排序和筛选没有误判

目标卡初始状态建议准备为“已学卡”：

- `user_card_srs.state = "review"` 或 `"learning"`
- `user_card_srs.last_review != NULL`
- `user_card_srs.due <= now`

这样可以确保它一开始已经在当前 lesson 的可学习集合内。

## 6. 具体测试用例

### 6.1 用例一：已学卡评分后不会在同一次 refetch 中立刻复现

目标：

- 证明同一张卡在刚完成本次复习后，不会因为仍在同一天就立刻重新出现在当前 lesson session 中。

步骤：

1. 创建 lesson 和目标卡，使其初始 `due <= now`。
2. 先请求一次 `GET /api/v1/study/session?lesson_id=...`，确认该卡存在于 `cards[]`。
3. 创建 submission，并对该卡提交 `rating = "good"`。
4. 记录 rating 响应里的 `srs.state / srs.due_at / srs.difficulty / srs.stability`。
5. 再次请求 `GET /api/v1/study/session?lesson_id=...`。
6. 断言该卡此时不再出现在 `cards[]`。

断言重点：

- `user_card_srs.last_review` 已更新。
- `user_card_srs.due > now`。
- 同一次 lesson refetch 中，该卡已消失。
- 这个用例的前提是评分后实际写入的 `due` 在未来；如果测试使用 mock FSRS，应确保 mock 返回未来时间。

### 6.2 用例二：已学卡到 due 后重新进入同 lesson session

目标：

- 证明不是“永久消失”，而是“future due 回归”。

步骤：

1. 承接用例一，拿到评分后的目标卡。
2. 人工把该卡 `user_card_srs.due` 改成当前时间前 1 分钟。
3. 再次请求 `GET /api/v1/study/session?lesson_id=...`。
4. 断言该卡重新出现在 `cards[]`。

断言重点：

- 该卡重新出现时 `lesson_id` 不变，仍在同一个 lesson session 下。
- `card_id` 与第一次学习的是同一张卡，不是新生成的副本。
- 返回的 `card_state` 应与当前最新 `user_card_srs.state` 对应。

说明：

- 这一步不需要真的等几天，直接修改 `due` 即可模拟“几天后到期”。
- 如果团队更希望避免直接改表，也可以在测试里冻结时间或注入 `as_of`，但当前项目已有接口最直接的是改测试数据库里的 `due`。

### 6.3 用例三：已学卡 `again` 后也遵循 due 回归，而不是同轮重复插队

目标：

- 证明即使评分是 `again`，系统行为仍然是“基于 due 回归”，而不是“当前 session 立即插回”。

步骤：

1. 准备一张已学卡并确认它当前在 session 内。
2. 提交 `rating = "again"`。
3. 立即重新请求 `GET /api/v1/study/session?lesson_id=...`。
4. 根据评分后写入的 `due` 判断：
   - 若 `due > now`，则不应立即出现
   - 若 mock/真实 FSRS 给出 `due <= now`，则允许出现，但必须以数据库值为准
5. 再通过手工推进 `due` 的方式，确保它在到期后一定能重新出现。

断言重点：

- 测试应避免写死“again 一定立即出现”或“一定不出现”，而应以评分后的实际 `due` 为准。
- 核心要证明系统是“due 驱动”，不是“写死同轮复现”。

### 6.4 用例四：同一张卡两次独立复习会保留两份历史 trace

目标：

- 证明不会因为同一天或同一张卡重复复习而覆盖旧记录。

步骤：

1. 对同一张卡完成第一次 submission + rating。
2. 将 `due` 推进到已到期状态。
3. 再次请求 session，确认该卡重新出现。
4. 对同一张卡完成第二次 submission + rating。
5. 查询数据库中的 `review_log` 与 `fsrs_review_log`。

断言重点：

- `review_log` 至少有两条不同记录，且 `card_id` 相同、`id` 不同、`created_at` 不同。
- `fsrs_review_log` 至少有两条不同记录，且 `card_id` 相同、`review_datetime` 不同。
- `list_submissions(lesson_id, card_id)` 返回结果中可以看到两次历史。
- 不允许通过 upsert 或覆盖把第一次记录抹掉。

### 6.5 用例五：同 lesson 内只重新出现一次当前卡，不应产生 session 级重复卡

目标：

- 处理“是否去重”的另一层含义：同一次 `GET /study/session` 返回中，不应出现同一 `card_id` 的重复项。

步骤：

1. 准备一个 lesson，包含目标卡和其他卡。
2. 让目标卡处于 due 状态。
3. 请求一次 `GET /api/v1/study/session?lesson_id=...`。

断言重点：

- 返回数组中同一个 `card_id` 最多出现一次。
- “保留历史 trace”不等于“当前 session 里重复发两张同 id 的卡”。

这条测试很重要，因为它把两个概念分开了：

- 日志历史不能去重覆盖
- session 卡片列表必须按 `card_id` 去重

## 6.6 用例六：前端“再次复习”依赖新的 session 返回，而不是当前队列重排

这个用例不一定要写成前端 E2E，但建议在测试说明或注释中写明，用来约束后端同事对现状的理解。

目标：

- 避免把后端调度测试误写成“评分后前端当前页立即再看到同一张卡”。

建议验证方式：

1. 以代码注释或测试说明明确记录当前前端行为：
   - 前端评分后不会自动调用 `fetchStudySession()`
   - 前端只更新当前卡本地状态并 `goNextCard()`
2. 在后端测试中，把“重新出现”的判定统一定义为：
   - 再次请求 `GET /api/v1/study/session?lesson_id=...` 后，目标卡重新回到 `cards[]`

这条不是额外的产品逻辑，而是为了防止测试目标被写偏。

## 7. 实现建议

### 7.1 优先级

建议后端同事按以下顺序完成：

1. 先补“评分后消失、到 due 后回归”的集成测试。
2. 再补“同一卡多次复习保留两份历史 trace”的测试。
3. 最后补“session 中单次请求不返回重复 card_id”的守护测试。

### 7.2 关于 mock 与真实 FSRS

当前 `backend/tests/conftest.py` 已默认 mock `FSRSAdapter.schedule_card`，适合稳定验证业务接线。

建议：

- 第一批测试继续复用 mock，先把“回归机制”和“历史保留”验证稳定。
- 如需进一步确认真实 `py-fsrs` 下的 `again/good` 时间跨度，可再补一组不 mock FSRS 的测试，但这不是本轮必须项。

### 7.3 关于“重新出现后会提示重新上传和复习”

后端侧真正需要保证的是：

- 到期卡会重新进入 `GET /api/v1/study/session?lesson_id=...` 的 `cards[]`
- 返回的还是同一张 card，具备再次复习所需的标准卡片字段

基于当前前端逻辑，只要卡重新进入 session，前端就会把它当成可再次录音上传和评分的学习卡处理。因此这部分对后端而言主要是 session inclusion contract，而不是额外接口。

## 8. 验收标准

完成后，测试应能稳定证明：

1. 同一张已学卡在评分后不会因为“还是今天”就自动在当前 lesson session 里再次出现。
2. 当该卡 `due` 到点后，再次请求同一 lesson 的 study session，它会重新出现。
3. 同一张卡的两次独立复习会保留两份 `review_log` 历史和两份 `fsrs_review_log` 历史。
4. 同一次 session 响应中不会出现重复 `card_id`。
5. 以上行为都通过自动化测试验证，而不是靠手工页面观察。

## 9. 建议输出记录格式

为了让调试结果更容易看懂，建议在关键断言前后整理统一的调试字段：

```text
card_id=123
lesson_id=45
initial_due=2026-03-23T09:00:00+08:00
rating=good
after_state=review
after_due=2026-03-27T09:00:00+08:00
present_in_initial_session=true
present_in_same_day_refetch=false
present_after_due_forced=true
review_log_count=2
fsrs_review_log_count=2
```

这不是接口契约，只是便于本地调试和 code review。

## 10. 开放问题

下面两个点建议后端同事在实现测试时顺手确认：

1. 当前 `daily_review_limit` 是否可能影响“到期后重新出现”的测试结果。
   - 建议测试里显式设置足够高的 `daily_review_limit`，避免被 quota 干扰。
2. 当前 `review_log.count_quota_usage_by_date()` 会把同一天的再次复习计入 review quota。
   - 这是否符合产品预期，需要单独确认，但不影响本次“due 后是否回归”的核心验证。

3. 当前前端不会自动刷新当前 lesson session。
   - 如果未来产品希望“用户停留在 lesson 页面时，due 一到就自动再次看到这张卡”，那将是一个新的前后端联动需求，不属于本次测试任务。

---

结论先写在这里，方便执行人对齐：

我们要验证的不是“同一天重复刷同一张卡”，而是“同一张卡在 lesson 内完成一次复习后退出当前 session，等 future due 到点后再重新进入，并保留完整两次历史 trace”。
