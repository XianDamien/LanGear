# LanGear

LanGear 是一个 AI 英语复述训练平台，核心链路是“原音频播放 -> 用户录音 -> 实时 ASR -> OSS 上传 -> 后端异步生成 AI 反馈 -> 前端轮询展示结果”。

当前 Study 页顶部提供句子任务导航栏：任务状态（待练、上传中、评测中、完成、失败）独立于当前卡片展示与切换，切卡不会中断已提交任务的前端跟踪。

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

## 环境变量

- 前端环境变量：`frontend/.env`
- 后端环境变量：`backend/.env`
- 后端运行时不要依赖仓库根目录 `.env`
- 可从 `backend/.env.example` 复制一份作为后端配置起点

## 当前关键约束

- ASR 必须使用 `qwen3-asr-flash`
- Gemini 必须走官方 SDK
- 不使用 Gemini relay
- 不添加 Gemini runtime fallback 分支
- 后端 Gemini 配置来源固定为 `backend/.env`
- 前端真实接口默认走 `/api/v1`
- `VITE_USE_MOCK=true` 时才切换到 mock 适配器

## 典型开发流程

1. 启动后端服务。
2. 启动前端服务。
3. 在学习页验证原音频播放、录音、上传、轮询与反馈展示。
4. 修改后端适配器、服务或路由时同步补单测。
5. 修改行为、流程或约束时同步检查 `README.md`、`PRD.md`、`PRD_BASELINE.md` 是否需要更新。

## 文档分工

- `README.md`：仓库入口、启动方式、开发约束
- `AGENTS.md`：协作规则与代理工作约束
- `CLAUDE.md`：`AGENTS.md` 的软链接，不单独维护
- `PRD.md`：详细产品与实现总纲
- `PRD_BASELINE.md`：当前联调基线与对齐口径

## 提交规范

- 提交信息使用简明中文
- 标题需要直接写出要点
- 默认只提交与当前任务相关的文件

## 相关文档

- `PRD.md`
- `PRD_BASELINE.md`
- `backend/IMPLEMENTATION_STATUS.md`
- `backend/TESTING_REPORT.md`
- `docs/realtime-gemini-e2e-test-plan.md`
