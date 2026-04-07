#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/server_backend_common.sh"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令: $1" >&2
    exit 1
  fi
}

require_command ssh
require_command rsync

echo "==> 准备服务器目录 ${LANGEAR_REMOTE}:${LANGEAR_SERVER_DIR}"
ssh "${LANGEAR_REMOTE}" \
  "sudo mkdir -p '${LANGEAR_SERVER_DIR}' '${LANGEAR_SERVER_DATA_DIR}' '${LANGEAR_SERVER_BACKUP_DIR}' \
  && sudo chown -R '${LANGEAR_SERVER_USER}:${LANGEAR_SERVER_USER}' '${LANGEAR_SERVER_DIR}'"

echo "==> 同步代码到服务器"
rsync \
  --archive \
  --compress \
  --delete \
  --filter "P data/" \
  --filter "P backups/" \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "backend/.env" \
  --exclude "backend/data/langear.db" \
  --exclude "backend/data/langear.db.backup*" \
  --exclude "backend/__pycache__" \
  --exclude "backend/.pytest_cache" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  --exclude ".DS_Store" \
  "${REPO_ROOT}/" \
  "${LANGEAR_REMOTE}:${LANGEAR_SERVER_DIR}/"

echo "==> 确保运行目录与持久化目录存在"
ssh "${LANGEAR_REMOTE}" \
  "sudo mkdir -p '${LANGEAR_SERVER_DIR}' '${LANGEAR_SERVER_DATA_DIR}' '${LANGEAR_SERVER_BACKUP_DIR}' \
  && sudo chown -R '${LANGEAR_SERVER_USER}:${LANGEAR_SERVER_USER}' '${LANGEAR_SERVER_DIR}'"

echo "==> 校验服务器依赖与敏感配置"
ssh "${LANGEAR_REMOTE}" "cd '${LANGEAR_SERVER_DIR}' && test -f backend/.env"
ssh "${LANGEAR_REMOTE}" "sudo docker compose version >/dev/null"

echo "==> 校验 Compose 配置"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) config >/dev/null"

echo "==> 启动后端迁移、空库种子与服务"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) up -d --build backend"

echo "==> 当前服务状态"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) ps"

echo "==> 最近日志（backend-migrate / backend-seed / backend）"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) logs --tail=80 backend-migrate backend-seed backend"

echo "==> 完成，可使用 scripts/check_server_backend.sh 继续验收"
