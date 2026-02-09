# LanGear

AI 英语复述训练平台，v2.0 异步架构。

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite + Element Plus + Pinia + ali-oss
- **后端**: FastAPI + SQLAlchemy 2.x + SQLite + Alembic
- **ASR**: 阿里云 DashScope qwen3-asr-flash（支持流式输出，返回词级时间戳）
- **AI 评测**: Google Gemini gemini-3.0-pro-preview（文字反馈，无数值评分）
- **存储**: 阿里云 OSS（STS 临时凭证，前端直传）
- **调度**: FSRS 间隔重复算法
- **包管理**: 前端 pnpm，后端 uv（唯一入口，不用 pip/venv）

## 架构索引

```
frontend/src/
  components/    # UI 组件（ui/ study/ layout/ library/ dashboard/ summary/）
  views/         # 页面级组件
  stores/        # Pinia 状态管理
  services/      # API 调用 + mock 适配器
  composables/   # useRecorder, useAudioPlayer, useHeatmap
  types/         # api.ts（接口契约）, domain.ts

backend/app/
  routers/       # API 路由
  services/      # 业务逻辑
  repositories/  # 数据访问
  adapters/      # 外部服务封装（oss, asr, gemini, fsrs）
  models/        # SQLAlchemy 模型（6 表）
  tasks/         # 后台异步任务
  schemas/       # Pydantic 模型
```

## 关键文档

- `PRD_MVP.md` — 产品总纲
- `frontend/PRD_MVP_FRONTEND.md` — 前端实施规格
- `backend/PRD_MVP_BACKEND.md` — 后端实施规格
- `backend/IMPLEMENTATION_STATUS.md` — 后端实施状态
- `backend/TESTING_REPORT.md` — 测试报告（183 tests, 79% coverage）

## 注意事项

- 环境变量已配置在 `backend/.env`，不要硬编码 API Key
- ASR 必须使用 **qwen3-asr-flash**，不要换模型
- AI 评测必须使用 **gemini-3.0-pro-preview**，不要用 flash 或旧版本
- 前端开发模式默认走 mock 适配器，联调时切换到真实 API
- backend 已整合进 monorepo，不再是独立 submodule
- 异步训练流程：前端 OSS 直传 → POST submission → 后台 ASR+Gemini+FSRS → 前端轮询结果
