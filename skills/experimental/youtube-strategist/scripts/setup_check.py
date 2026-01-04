#!/usr/bin/env python3
"""Verify dependencies and ensure MCP server configuration."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple

VENV_DIRNAME = ".venv"

MCP_NAME = "youtube_transcript"
MCP_COMMAND = [
    "uvx",
    "--from",
    "git+https://github.com/jkawamoto/mcp-youtube-transcript",
    "mcp-youtube-transcript",
]


def _strip_jsonc(text: str) -> str:
    # Remove // and /* */ comments for simple JSONC parsing.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"(^|\s)//.*$", "", text, flags=re.MULTILINE)
    return text


def _load_jsonc(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    cleaned = _strip_jsonc(raw)
    if not cleaned.strip():
        return {}
    return json.loads(cleaned)


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_project_config(start_dir: Path) -> Path | None:
    for parent in [start_dir, *start_dir.parents]:
        json_path = parent / "opencode.json"
        jsonc_path = parent / "opencode.jsonc"
        if json_path.exists():
            return json_path
        if jsonc_path.exists():
            return jsonc_path
    return None


def _command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _ensure_python_package(
    pkg_import: str, install_name: str, python_path: Path | None
) -> Tuple[bool, str]:
    if python_path:
        check_cmd = [str(python_path), "-c", f"import {pkg_import}"]
    else:
        check_cmd = ["python", "-c", f"import {pkg_import}"]

    check = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
    if check.returncode == 0:
        return True, f"{install_name} already installed."

    if _command_exists("uv") and python_path:
        cmd = ["uv", "pip", "install", "--python", str(python_path), install_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, f"Installed {install_name} via {' '.join(cmd)}."
        err = result.stderr.strip() or "install failed"
        return False, f"Failed to install {install_name}: {err}"

    cmd = ["python", "-m", "pip", "install", install_name]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True, f"Installed {install_name} via {' '.join(cmd)}."
    err = result.stderr.strip() or "install failed"
    return False, f"Failed to install {install_name}: {err}"


def _ensure_mcp_config(config_path: Path, apply: bool) -> Tuple[bool, str]:
    data = _load_jsonc(config_path) if config_path.exists() else {}
    mcp = data.get("mcp", {})

    if MCP_NAME in mcp:
        return True, f"MCP server '{MCP_NAME}' already configured."

    mcp[MCP_NAME] = {
        "type": "local",
        "command": MCP_COMMAND,
        "enabled": True,
    }
    data["mcp"] = mcp

    if apply:
        _write_json(config_path, data)
        return True, f"Configured MCP server '{MCP_NAME}' in {config_path}."

    return True, f"Would configure MCP server '{MCP_NAME}' in {config_path}."


def _select_config_path() -> Path:
    cwd = Path.cwd()
    project_config = _find_project_config(cwd)
    if project_config:
        return project_config
    return Path.home() / ".config" / "opencode" / "opencode.json"


def _ensure_venv(skill_root: Path) -> Tuple[Path | None, str]:
    if not _command_exists("uv"):
        return None, "uv not found. Using system Python for installs."

    venv_path = skill_root / VENV_DIRNAME
    python_path = venv_path / "bin" / "python"
    if python_path.exists():
        return python_path, f"Using existing venv at {venv_path}."

    result = subprocess.run(
        ["uv", "venv"],
        cwd=skill_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or "uv venv failed"
        return None, f"Failed to create venv: {err}"

    if python_path.exists():
        return python_path, f"Created venv at {venv_path}."

    return None, "uv venv did not create expected .venv path."


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dependencies and MCP config.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--config", type=str, help="Custom opencode config path.")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser() if args.config else _select_config_path()
    apply = not args.dry_run

    status = []

    skill_root = Path(__file__).resolve().parents[1]
    python_path, venv_msg = _ensure_venv(skill_root)
    status.append((python_path is not None or "uv not found" in venv_msg, venv_msg))

    ok_yt, msg_yt = _ensure_python_package("yt_dlp", "yt-dlp", python_path)
    status.append((ok_yt, msg_yt))

    ok_tr, msg_tr = _ensure_python_package("pytrends", "pytrends", python_path)
    status.append((ok_tr, msg_tr))

    if not _command_exists("uvx"):
        status.append((False, "uvx not found. Install uv to enable MCP server startup."))
    else:
        ok_mcp, msg_mcp = _ensure_mcp_config(config_path, apply=apply)
        status.append((ok_mcp, msg_mcp))

    all_ok = True
    for ok, msg in status:
        prefix = "OK" if ok else "WARN"
        print(f"[{prefix}] {msg}")
        if not ok:
            all_ok = False

    if all_ok:
        print("Setup check complete.")
        return 0

    print("Setup check completed with warnings.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
