#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "用法: $0 /absolute/path/to/langear.db" >&2
  exit 1
fi

LOCAL_DB_PATH="$1"
if [[ ! -f "${LOCAL_DB_PATH}" ]]; then
  echo "数据库文件不存在: ${LOCAL_DB_PATH}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/server_backend_common.sh"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令: $1" >&2
    exit 1
  fi
}

require_command ssh
require_command scp

REMOTE_DB_PATH="${LANGEAR_SERVER_DATA_DIR}/langear.db"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REMOTE_TMP_DB_PATH="/tmp/langear.db.${TIMESTAMP}"

echo "==> 准备服务器目录"
ssh "${LANGEAR_REMOTE}" \
  "sudo mkdir -p '${LANGEAR_SERVER_DIR}' '${LANGEAR_SERVER_DATA_DIR}' '${LANGEAR_SERVER_BACKUP_DIR}' \
  && sudo chown -R '${LANGEAR_SERVER_USER}:${LANGEAR_SERVER_USER}' '${LANGEAR_SERVER_DIR}'"

echo "==> 备份服务器现有数据库（若存在）"
ssh "${LANGEAR_REMOTE}" \
  "if [ -f '${REMOTE_DB_PATH}' ]; then sudo cp '${REMOTE_DB_PATH}' '${LANGEAR_SERVER_BACKUP_DIR}/langear.db.${TIMESTAMP}'; fi"

echo "==> 停止运行中的后端服务（若存在）"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) stop backend >/dev/null 2>&1 || true"

echo "==> 上传真实数据库到临时路径 ${REMOTE_TMP_DB_PATH}"
scp "${LOCAL_DB_PATH}" "${LANGEAR_REMOTE}:${REMOTE_TMP_DB_PATH}"

echo "==> 安装真实数据库到 ${REMOTE_DB_PATH}"
ssh "${LANGEAR_REMOTE}" \
  "sudo mv '${REMOTE_TMP_DB_PATH}' '${REMOTE_DB_PATH}' \
  && sudo chown '${LANGEAR_SERVER_USER}:${LANGEAR_SERVER_USER}' '${REMOTE_DB_PATH}'"

echo "==> 重新启动后端，确保迁移与空库兜底链路仍然生效"
ssh "${LANGEAR_REMOTE}" \
  "cd '${LANGEAR_SERVER_DIR}' && sudo docker compose $(server_compose_args) up -d --build backend"

echo "==> 数据库恢复完成"
