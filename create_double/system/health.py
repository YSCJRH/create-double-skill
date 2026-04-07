"""Environment and repository health checks for create-double."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised through doctor in real environments
    yaml = None


def ensure_utf8_output() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def stdout_is_utf8() -> bool:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    return "utf" in encoding


def repo_validation_errors(root: Path) -> list[str]:
    validator_path = root / "scripts" / "validate_repo.py"
    if not validator_path.exists():
        return ["缺少 scripts/validate_repo.py。"]
    if yaml is None:
        return ["PyYAML 未安装，暂时无法运行完整仓库校验。"]

    spec = importlib.util.spec_from_file_location("validate_repo", validator_path)
    if spec is None or spec.loader is None:
        return ["无法加载 scripts/validate_repo.py。"]

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.validate(root))


def write_access_ok(root: Path) -> tuple[bool, str]:
    doubles_root = root / "doubles"
    doubles_root.mkdir(parents=True, exist_ok=True)
    probe = doubles_root / ".doctor-write-check"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return False, str(exc)
    return True, str(doubles_root)


def doctor_report(root: Path) -> dict[str, Any]:
    python_ok = sys.version_info >= (3, 9)
    write_ok, write_detail = write_access_ok(root)
    validation_errors = repo_validation_errors(root)
    terminal_ok = stdout_is_utf8()

    checks = [
        {
            "name": "Python",
            "ok": python_ok,
            "detail": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        {
            "name": "PyYAML",
            "ok": yaml is not None,
            "detail": "已安装" if yaml is not None else "缺少 PyYAML，请先安装 requirements.txt",
        },
        {
            "name": "Repo validation",
            "ok": not validation_errors,
            "detail": "通过" if not validation_errors else "；".join(validation_errors),
        },
        {
            "name": "Write access",
            "ok": write_ok,
            "detail": write_detail if write_ok else f"无法写入 doubles/：{write_detail}",
        },
        {
            "name": "UTF-8 terminal",
            "ok": terminal_ok,
            "detail": (
                "终端编码看起来正常。"
                if terminal_ok
                else "当前终端可能不是 UTF-8；若出现乱码，请先运行 `chcp 65001`。"
            ),
        },
    ]
    ok = all(item["ok"] for item in checks)
    return {
        "ok": ok,
        "checks": checks,
        "next_steps": [
            "python -m pip install -r requirements.txt",
            "python scripts/double_builder.py doctor",
            'python scripts/double_builder.py start --slug my-double --display-name "我的分身"',
        ],
    }


def format_doctor_report(report: dict[str, Any]) -> str:
    lines = ["create-double doctor", ""]
    for check in report["checks"]:
        label = "OK" if check["ok"] else "WARN"
        lines.append(f"[{label}] {check['name']}: {check['detail']}")
    lines.extend(["", "下一步："])
    lines.extend([f"- {step}" for step in report["next_steps"]])
    return "\n".join(lines)
