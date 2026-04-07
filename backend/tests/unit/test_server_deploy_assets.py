"""Smoke tests for server deployment assets."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.unit
def test_server_compose_overrides_backend_data_and_disables_frontend_by_default():
    compose_path = REPO_ROOT / "docker-compose.server.yml"

    payload = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    services = payload["services"]

    for service_name in ("backend-migrate", "backend-seed", "backend"):
        service = services[service_name]
        assert service["volumes"] == [
            {
                "type": "bind",
                "source": "/srv/langear/data",
                "target": "/app/data",
            }
        ]

    assert services["frontend"]["profiles"] == ["frontend"]


@pytest.mark.unit
def test_server_shell_scripts_have_valid_bash_syntax_and_exec_bit():
    script_paths = [
        REPO_ROOT / "scripts" / "server_backend_common.sh",
        REPO_ROOT / "scripts" / "bootstrap_server_deploy_user.sh",
        REPO_ROOT / "scripts" / "deploy_server_backend.sh",
        REPO_ROOT / "scripts" / "restore_server_database.sh",
        REPO_ROOT / "scripts" / "check_server_backend.sh",
    ]

    for script_path in script_paths:
        assert script_path.exists()
        mode = script_path.stat().st_mode
        assert mode & stat.S_IXUSR

        completed = subprocess.run(
            ["bash", "-n", os.fspath(script_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr


@pytest.mark.unit
def test_server_common_defaults_to_langear_deploy_and_bootstrap_ubuntu():
    common_script = (
        REPO_ROOT / "scripts" / "server_backend_common.sh"
    ).read_text(encoding="utf-8")

    assert 'LANGEAR_SERVER_USER="${LANGEAR_SERVER_USER:-langear-deploy}"' in common_script
    assert 'LANGEAR_BOOTSTRAP_USER="${LANGEAR_BOOTSTRAP_USER:-ubuntu}"' in common_script
