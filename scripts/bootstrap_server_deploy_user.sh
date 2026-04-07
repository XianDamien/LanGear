#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/server_backend_common.sh"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令: $1" >&2
    exit 1
  fi
}

require_command ssh

echo "==> 校验 bootstrap 入口 ${LANGEAR_BOOTSTRAP_REMOTE}"
ssh "${LANGEAR_BOOTSTRAP_REMOTE}" "whoami"

SUDO_CMD="sudo"
if ssh "${LANGEAR_BOOTSTRAP_REMOTE}" "sudo -n true" >/dev/null 2>&1; then
  SUDO_CMD="sudo -n"
fi

echo "==> 使用 ${LANGEAR_BOOTSTRAP_REMOTE} 创建 ${LANGEAR_SERVER_USER}"
ssh -tt "${LANGEAR_BOOTSTRAP_REMOTE}" \
  "DEPLOY_USER='${LANGEAR_SERVER_USER}' SUDO_CMD='${SUDO_CMD}' bash -s" <<'EOF'
set -euo pipefail

if ! id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
  ${SUDO_CMD} adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi

${SUDO_CMD} mkdir -p "/home/${DEPLOY_USER}/.ssh"
if [ -f /home/ubuntu/.ssh/authorized_keys ]; then
  ${SUDO_CMD} cp /home/ubuntu/.ssh/authorized_keys "/home/${DEPLOY_USER}/.ssh/authorized_keys"
fi
${SUDO_CMD} chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"
${SUDO_CMD} chmod 700 "/home/${DEPLOY_USER}/.ssh"
if [ -f "/home/${DEPLOY_USER}/.ssh/authorized_keys" ]; then
  ${SUDO_CMD} chmod 600 "/home/${DEPLOY_USER}/.ssh/authorized_keys"
fi

${SUDO_CMD} usermod -aG sudo "${DEPLOY_USER}"
if getent group docker >/dev/null 2>&1; then
  ${SUDO_CMD} usermod -aG docker "${DEPLOY_USER}"
fi

printf '%s\n' "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" | \
  ${SUDO_CMD} tee "/etc/sudoers.d/${DEPLOY_USER}" >/dev/null
${SUDO_CMD} chmod 440 "/etc/sudoers.d/${DEPLOY_USER}"
${SUDO_CMD} visudo -cf "/etc/sudoers.d/${DEPLOY_USER}"
EOF

echo "==> 验证 ${LANGEAR_REMOTE}"
ssh "${LANGEAR_REMOTE}" "whoami && sudo -n true && id && groups"

echo "==> bootstrap 完成"
