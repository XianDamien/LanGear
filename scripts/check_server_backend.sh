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

require_command curl
require_command python3

run_check() {
  local name="$1"
  local path="$2"
  local parser="$3"
  local payload

  payload="$(curl --silent --show-error --fail "${LANGEAR_SERVER_URL}${path}")"
  python3 -c "${parser}" "${payload}"
  echo "PASS ${name}"
}

run_check \
  "health" \
  "/health" \
  'import json, sys; payload = json.loads(sys.argv[1]); assert payload["status"] == "healthy", payload'

run_check \
  "decks tree" \
  "/api/v1/decks/tree" \
  'import json, sys; payload = json.loads(sys.argv[1]); sources = payload["data"]["sources"]; assert isinstance(sources, list), payload; assert len(sources) > 0, payload'

run_check \
  "sts token" \
  "/api/v1/oss/sts-token" \
  'import json, sys; payload = json.loads(sys.argv[1]); data = payload["data"]; assert data["bucket"], payload; assert data["region"], payload'

echo "全部检查通过: ${LANGEAR_SERVER_URL}"
