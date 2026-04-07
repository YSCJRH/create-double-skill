"""Path, YAML, and snapshot helpers for create-double."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised through doctor in real environments
    yaml = None


def require_yaml(command_name: str = "this command") -> None:
    if yaml is None:
        raise RuntimeError(
            f"PyYAML 未安装，无法运行 {command_name}。先执行 `python -m pip install -r requirements.txt`。"
        )


def load_yaml(path: Path) -> dict[str, Any]:
    require_yaml(path.name)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    require_yaml(path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        )


def double_dir(root: Path, slug: str) -> Path:
    return root / "doubles" / slug


def profile_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "profile.yaml"


def profile_md_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "profile.md"


def generated_skill_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "SKILL.md"


def session_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "session.yaml"


def history_dir(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "history"


def ensure_exists(root: Path, slug: str) -> None:
    if not profile_path(root, slug).exists():
        raise FileNotFoundError(f"double '{slug}' does not exist under {root / 'doubles'}")


def snapshot_outputs(root: Path, slug: str) -> Path | None:
    targets = [
        profile_path(root, slug),
        profile_md_path(root, slug),
        generated_skill_path(root, slug),
        session_path(root, slug),
    ]
    existing = [path for path in targets if path.exists()]
    if len(existing) < 3:
        return None

    profile = load_yaml(profile_path(root, slug))
    version = profile.get("meta", {}).get("version", 1)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    snapshot_dir = history_dir(root, slug) / f"{stamp}__v{version}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    for source in existing:
        shutil.copy2(source, snapshot_dir / source.name)
    return snapshot_dir
