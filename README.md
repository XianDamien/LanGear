# LanGear

LanGear 是一个 AI 英语复述训练平台，核心链路是“原音频播放 -> 用户录音 -> 实时 ASR -> OSS 上传 -> 后端异步生成 AI 反馈 -> 前端轮询展示结果 -> 用户评分触发 FSRS 更新”。

当前 Study 页顶部提供句子任务导航栏：任务状态（待练、上传中、评测中、完成、失败）独立于当前卡片展示与切换，切卡不会中断已提交任务的前端跟踪。学习页卡片列表由 `/api/v1/study/session` 提供，按 `learning/relearning -> review -> new` 顺序返回，并受每日 new/review quota 约束。

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
- Vite 会将 `/api` 代理到后端 `http://localhost:8000`

### 后端

```bash
cd backend
uv run uvicorn app.main:app --reload
```

- 默认地址：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`

### 测试

```bash
cd backend
uv run pytest
```

```bash
cd frontend
pnpm test:e2e
```

### `uv` 使用说明

- 默认在 `backend/` 目录下使用 `uv run ...` 与 `uv sync ...`
- 如果本机 `uv` 不在 `PATH`，请先将 `uv` 安装目录加入 shell 的 `PATH`
- 不建议混用系统 Python、系统 `pytest` 和 `uv run`，否则容易出现依赖不一致
- 如果不希望在项目目录下生成 `.venv`，请按命令显式指定单独的环境路径，例如：

```bash
cd backend
UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv/project-envs/langear-backend" uv run pytest
```
## 环境变量

- 前端环境变量：`frontend/.env`
- 后端环境变量：`backend/.env`
- 后端运行时不要依赖仓库根目录 `.env`
- 可从 `backend/.env.example` 复制一份作为后端配置起点
- `OSS_PUBLIC_BASE_URL` 不是后端启动必填项；默认采用 STS 上传 + 预签名 URL 访问 OSS
- `ALIYUN_ROLE_ARN` 仅用于 `/api/v1/oss/sts-token` 生成前端直传 OSS 所需的临时 STS 凭证
- 缺失 `ALIYUN_ROLE_ARN` 时，后端仍可启动，但前端直传 OSS 的 STS 能力不可用

## 当前关键约束

- ASR 必须使用 `qwen3-asr-flash`
- Gemini 必须走官方 SDK
- 不使用 Gemini relay
- 不添加 Gemini runtime fallback 分支
- 后端 Gemini 配置来源固定为 `backend/.env`
- Gemini prompt 按版本目录管理，且每个任务使用 `system.md` + `user.md` + `metadata.json` 结构
- 前端真实接口默认走 `/api/v1`
- `VITE_USE_MOCK=true` 时才切换到 mock 适配器
- 学习页评分按钮前端使用 `1|2|3|4`，后端统一映射为 `again/hard/good/easy`
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
- `skills/`：项目级协作 skill；例如 `langear-prompt-update` 用于安全更新 Gemini prompt

## PRD 版本追踪

```bash
python3 scripts/prd_version_manager.py status
python3 scripts/prd_version_manager.py sync
python3 scripts/prd_version_manager.py snapshot --version v2.2 --date 2026-03-20 --changes "..."
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
