# LanGear

LanGear 是一个 AI 英语复述训练平台，核心链路是“原音频播放 -> 用户录音 -> 实时 ASR -> OSS 上传 -> 后端异步生成 AI 反馈 -> 前端轮询展示结果 -> 用户评分触发 FSRS 更新”。

当前 Study 页顶部提供句子任务导航栏：任务状态（待练、上传中、评测中、完成、失败）独立于当前卡片展示与切换，切卡不会中断已提交任务的前端跟踪。学习页卡片列表由 `/api/v1/study/session` 提供，优先返回 `learning/relearning` 与 `review` 卡，再按 quota 补充 FSRS 初始卡桶；当请求显式带 `lesson_id` 时，接口还会在队列后追加“已复习但尚未到期”的卡，避免刷新后把刚复习过的卡从课内视图里移除。每张卡返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`，其中 `card_state` 只表达原生三态。课程树接口 `/api/v1/decks/tree` 的 lesson 节点返回 `total_cards` / `completed_cards` / `due_cards` / `new_cards`；`/api/v1/decks/{lesson_id}/cards` 返回 `card_state`、`is_new_card`、`due_at`、`last_review_at`。进入 lesson 时，前端会先调用 `GET /api/v1/study/submissions?lesson_id=...`，用后端 `review_log` 历史回填最近的 `processing` / `failed` / `completed` submission，刷新后不再只依赖前端内存态。

FSRS 底层契约按原生 `py-fsrs` 对齐：`user_card_srs.state` 只持久化 `learning/review/relearning`，`new cards` 由 FSRS 初始卡条件推导，主判定口径是 `last_review IS NULL`；原生评分历史单独写入 `fsrs_review_log`。

## 技术栈

- 前端：Vue 3 + TypeScript + Vite + Pinia
- 后端：FastAPI + SQLAlchemy + SQLite + Alembic
- ASR：DashScope `qwen3-asr-flash`
- AI 评测：Google Gemini 官方 `google-genai` SDK
- 存储：阿里云 OSS
- 调度：FSRS

## 仓库结构

```text
frontend/          前端应用
backend/           后端服务、适配器、测试与迁移
docs/              联调与补充文档
scripts/           仓库级辅助脚本
docker-compose.yml 单机 Docker Compose 部署入口
PRD.md             详细产品/实现总纲
PRD_BASELINE.md    当前联调基线
AGENTS.md          协作约束与项目运行规则
CLAUDE.md          指向 AGENTS.md 的软链接
```

## 本地运行

### 前端

```bash
cd frontend
pnpm dev
```

- 默认地址：`http://localhost:3002`
- Vite 会将 `/api` 代理到后端 `http://127.0.0.1:8000`
- 正式前端链路统一走相对路径 `/api/...`；如果直接在浏览器里请求 `http://127.0.0.1:8000/api/...`，是否能通取决于后端当前 CORS 配置。

### 后端

```bash
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

- 默认地址：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`
- 默认允许的开发 CORS 来源：`http://localhost:3002`、`http://127.0.0.1:3002`
- 启动前先执行一次 `uv run alembic upgrade head`，确保本地 SQLite schema 与当前代码一致
- 如果后端在 startup 阶段直接退出并提示 schema/revision 不匹配，先在 `backend/` 目录执行 `uv run alembic current` 和 `uv run alembic upgrade head`，再重新启动
- 可用 `uv run python scripts/show_runtime_config.py` 查看当前进程实际使用的 `DATABASE_URL`、解析后的 SQLite 文件路径、当前 CORS 来源列表、`review_log` / `user_card_srs` 条数，以及最近写入的评测记录。

### 测试

```bash
cd backend
uv run pytest
```

```bash
cd frontend
pnpm test:e2e
```

## Docker 部署

项目已提供单机 `docker compose` 部署文件，保持当前架构不变：

- `frontend` 使用多阶段构建产出静态文件，并由 Nginx 对外提供 `http://localhost:8080`
- `backend` 使用 FastAPI 独立容器，对外保留 `http://localhost:8000`
- `backend-migrate` 在后端启动前自动执行 `alembic upgrade head`
- SQLite 数据库存放在 Docker named volume `langear_backend_data` 中，避免依赖宿主机 `backend/data/langear.db`

### 准备环境变量

- Docker 部署仍然使用 `backend/.env`
- 启动前确认 `backend/.env` 已存在，且 Gemini、DashScope、OSS 相关配置齐全
- 前端镜像只注入非敏感 `VITE_*` 构建变量；敏感密钥不会进入前端镜像

可从示例文件开始：

```bash
cp backend/.env.example backend/.env
```

### 构建与启动

```bash
docker compose build
docker compose up -d
```

默认访问地址：

- 前端：`http://localhost:8080`
- 后端 OpenAPI：`http://localhost:8000/docs`
- 后端健康检查：`http://localhost:8000/health`

Compose 默认行为：

- 浏览器访问 `http://localhost:8080/api/...` 时，会由前端容器内的 Nginx 反向代理到 `backend:8000`
- `GET /api/v1/realtime/...` 与 WebSocket `/api/v1/realtime/asr/ws` 也走同一入口，不需要单独改前端 API Base URL
- `backend` 只有在迁移容器成功执行完 `alembic upgrade head` 后才会启动

### 常用运维命令

查看服务状态与日志：

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

停止服务但保留数据库卷：

```bash
docker compose down
```

停止服务并删除 SQLite 数据卷：

```bash
docker compose down -v
```

如果你只想重新执行迁移，可以单独运行：

```bash
docker compose run --rm backend-migrate
```

### `uv` 使用说明

- 默认在 `backend/` 目录下使用 `uv run ...` 与 `uv sync ...`
- 如果本机 `uv` 不在 `PATH`，请先将 `uv` 安装目录加入 shell 的 `PATH`
- 不建议混用系统 Python、系统 `pytest` 和 `uv run`，否则容易出现依赖不一致
- 后端默认 `DATABASE_URL=sqlite:///data/langear.db` 会在运行时归一到 `backend/data/langear.db`，避免因进程工作目录不同误连到别的 SQLite 文件
- `backend/data/langear.db` 是本地运行态 SQLite 文件，不会随 Git 提交同步到 GitHub；远端仓库不会包含你本机最新的 `review_log`、`fsrs_review_log`、`user_card_srs` 或其他运行时数据
- 如果不希望在项目目录下生成 `.venv`，请按命令显式指定单独的环境路径，例如：

```bash
cd backend
UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv/project-envs/langear-backend" uv run pytest
```

## 环境变量

- 前端环境变量：`frontend/.env`
- 后端环境变量：`backend/.env`
- 后端运行时不要依赖仓库根目录 `.env`
- 并行 worktree 开发时，也要保证各自 worktree 下存在 `backend/.env`；推荐直接在 worktree 内创建指向主工作区 `backend/.env` 的本地 symlink，避免 `uv run alembic ...` / `uv run pytest ...` 因缺少环境变量而失败
- 可从 `backend/.env.example` 复制一份作为后端配置起点
- `docker compose` 部署同样通过 `backend/.env` 注入后端运行时配置，不依赖仓库根目录 `.env`
- 想确认当前后端实际会连接哪个数据库，可在 `backend/` 目录执行 `uv run python scripts/show_runtime_config.py`；该脚本只依赖 `DATABASE_URL`，不要求先配齐完整 Gemini/OSS 密钥
- 如果你在本地看到了评测/复习记录，但 GitHub 上的代码或别的 worktree 里看不到，优先假设是命中了不同的本地 SQLite，而不是“数据库会跟着仓库自动同步”
- `OSS_PUBLIC_BASE_URL` 不是后端启动必填项；默认采用 STS 上传 + 预签名 URL 访问 OSS
- `ALIYUN_ROLE_ARN` 仅用于 `/api/v1/oss/sts-token` 生成前端直传 OSS 所需的临时 STS 凭证
- 缺失 `ALIYUN_ROLE_ARN` 时，后端仍可启动，但前端直传 OSS 的 STS 能力不可用

## 评测链路排查

- Study 页当前依赖两个接口恢复任务状态：
  - `GET /api/v1/study/submissions?lesson_id=...&card_id=...`
  - `GET /api/v1/study/submissions/{submission_id}`
- 历史状态真源是 `review_log`，不是卡片接口里的“最新 completed oss path”弱口径。
- `POST /api/v1/study/submissions` 的前置校验失败会直接返回明确 `error_code` / `error_message`，例如 `REALTIME_SESSION_NOT_FOUND`、`REALTIME_TRANSCRIPT_NOT_READY`、`REALTIME_SESSION_FAILED`、`INVALID_OSS_PATH`；这类失败不会创建 `review_log`。
- 前端开发态只会代理到当前配置的 `127.0.0.1:8000`。如果本地同时运行多个 worktree 或多个 backend 端口，先确认浏览器命中的实例，再判断“评测结果没保存”。
- 排查多 worktree / 多后端实例时，先在目标后端目录执行 `uv run python scripts/show_runtime_config.py`，确认：
  - 当前进程监听端口
  - 当前 `DATABASE_URL`
  - 实际命中的 SQLite 文件
  - 最近 `review_log` 写入记录
- 如果前端显示“任务历史加载失败，请确认后端实例和数据库是否正确”，优先检查前端代理目标是否仍指向你预期的 `127.0.0.1:8000`，以及该实例是否连接到你预期的 SQLite。

## 当前关键约束

- ASR 必须使用 `qwen3-asr-flash`
- Gemini 必须走官方 SDK
- 不使用 Gemini relay
- 不添加 Gemini runtime fallback 分支
- 后端 Gemini 配置来源固定为 `backend/.env`
- Gemini prompt 按版本目录管理，且每个任务使用 `system.md` + `user.md` + `metadata.json` 结构
- `single_feedback` 由 Gemini 同时产出展示转写与问题点反馈；`transcription.timestamps` 仅为兼容保留空数组，不再承载词级跳转
- 前端真实接口默认走 `/api/v1`
- `VITE_USE_MOCK=true` 时才切换到 mock 适配器
- 学习页评分按钮前端使用 `1|2|3|4`，后端统一映射为 `again/hard/good/easy`
- `POST /api/v1/study/submissions/{id}/rating` 与 `GET /api/v1/study/submissions/{id}` 若返回 `srs.state`，仅暴露原生三态：`learning` / `review` / `relearning`
- 仅在 subagent 输出会实质影响当前任务时才创建；创建后必须等待并消费结果，不再需要时显式关闭

## Gemini Prompt 开发

- Prompt 目录：`backend/app/adapters/prompts/<version>/`
- 当前任务结构：
  - `single_feedback/system.md`
  - `single_feedback/user.md`
  - `single_feedback/metadata.json`
  - `lesson_summary/system.md`
  - `lesson_summary/user.md`
  - `lesson_summary/metadata.json`
- `system.md` 放稳定角色、规则和判定原则
- `user.md` 放运行时输入模板、处理指令和输出 schema
- `metadata.json` 记录版本、说明和 changelog
- 激活版本通过 `backend/.env` 中的 `GEMINI_PROMPT_VERSION` 控制
- `single_feedback` 当前输出包含：展示用 `transcription_text`、中文反馈文本、以及 `issues[]` / `suggestions[]` 上的问题点时间戳；不再请求字级时间戳

## Gemini 双模式

- 生产模式：继续走 `study submission -> review_task -> GeminiAdapter -> review_log` 的正式链路，用于真实用户评测。
- 离线评测模式：走 `backend/scripts/export_single_feedback_dataset.py` 与 `backend/scripts/run_single_feedback_eval.py`，只读取本地数据集并把 run 结果落盘，不写业务 `review_log`。
- 两种模式共享 `GeminiAdapter` 的 prompt 渲染、响应解析与结构校验逻辑，但入口与产物分离，避免把 prompt 实验流程混进线上任务。
- 线上真源仍然是 `DATABASE_URL` 指向数据库里的 `review_log` / `user_card_srs`；`backend/datasets/` 只是导出的离线快照目录。

## Prompt 离线评测工作流

- 数据集根目录：`backend/datasets/gemini_single_feedback_eval/`
- 样本目录：`samples/<sample_id>/`
- 运行结果目录：`runs/<run_id>/`
- 导出记录目录：`exports/`
- 目录说明见 `backend/datasets/README.md`

### 1. 导出本地数据集

在后端目录执行：

```bash
cd backend
uv run python scripts/export_single_feedback_dataset.py --limit 20
```

- 数据源是已完成的 `review_log(result_type=single, status=completed)`。
- 每个样本会落下：
  - `metadata.json`：样本元数据、来源记录、音频摘要、输入指纹
  - `input.json`：固定输入
  - `source_output.json`：历史线上输出快照，供人工参考
  - `user_audio.*` / `reference_audio.*`：本地音频归档
- `dataset_manifest.json` 与 `exports/*.json` 会额外记录本次导出使用的数据库来源，明确该目录是离线 snapshot，不是运行时真源。

如果当前还没有可用的 `review_log`，可以先把现有卡片记录和参考音频拉下来：

```bash
cd backend
uv run python scripts/export_single_feedback_dataset.py --source cards
```

- `--source cards` 会导出 `cards` 表中的 `front_text + reference_audio`，形成 `ready_for_eval=false` 的 reference-only 样本。
- 这类样本先作为本地输入档案，不直接参与 `run_single_feedback_eval.py`。
- 后续拿到用户录音或历史提交结果后，可以继续往同一个 dataset 根目录补 `ready_for_eval=true` 的正式评测样本。

### 2. 运行 prompt 对比

```bash
cd backend
uv run python scripts/run_single_feedback_eval.py \
  --variant baseline=app/adapters/prompts/v1/single_feedback \
  --variant candidate=/absolute/path/to/prompt_variant \
  --limit 20
```

- 每次 run 会固定：
  - dataset 样本集合
  - `GEMINI_MODEL_ID` 或 `--model-id`
  - `temperature`
  - `max_output_tokens`
- 允许变化的主变量是 prompt 目录。
- 每个 variant 会保存：
  - prompt 快照
  - `results.jsonl`
  - 每个样本的输入、输出、错误与耗时
- run 根目录会保存：
  - `run_manifest.json`
  - `comparison.json`

### 3. 控制变量约定

- 比较不同 prompt 时，先固定 dataset，再固定模型与 generation config。
- 不要直接在生产 prompt 目录上覆盖试验；新增候选 prompt 目录后通过 `--variant` 显式传入。
- 离线评测结果只用于实验复盘，不回写业务表，不替代正式用户反馈记录。

## 典型开发流程

1. 启动后端服务。
2. 启动前端服务。
3. 在学习页验证 `/api/v1/study/session` 选卡、原音频播放、录音、上传、轮询、评分与反馈展示。
4. 修改后端适配器、服务或路由时同步补单测。
5. 修改行为、流程或约束时同步检查 `README.md`、`PRD.md`、`PRD_BASELINE.md` 是否需要更新。
6. 修改 `PRD.md` 后，使用 `python3 scripts/prd_version_manager.py sync` 刷新镜像；需要归档命名版本时再执行 `snapshot`。

## 文档分工

- `README.md`：仓库入口、启动方式、开发约束
- `AGENTS.md`：协作规则与代理工作约束
- `CLAUDE.md`：`AGENTS.md` 的软链接，不单独维护
- `PRD.md`：详细产品与实现总纲
- `PRD_BASELINE.md`：当前联调基线与对齐口径
- `docs/prd_versions/`：单一 PRD 版本追踪目录，包含 `metadata.json`、`current.md` 与 `archived/` 快照

## PRD 版本追踪

```bash
python3 scripts/prd_version_manager.py status
python3 scripts/prd_version_manager.py sync
python3 scripts/prd_version_manager.py snapshot --version v2.2 --date 2026-03-22 --changes "..."
```

- 根目录 `PRD.md` 是版本追踪的编辑源文件
- `docs/prd_versions/current.md` 是同步镜像
- `docs/prd_versions/archived/` 保存命名版本快照

## 提交规范

- 提交信息使用简明中文
- 标题需要直接写出要点
- 默认只提交与当前任务相关的文件

## 相关文档

- `PRD.md`
- `PRD_BASELINE.md`
- `docs/prd_versions/README.md`
- `backend/IMPLEMENTATION_STATUS.md`
- `backend/TESTING_REPORT.md`
- `docs/realtime-gemini-e2e-test-plan.md`
