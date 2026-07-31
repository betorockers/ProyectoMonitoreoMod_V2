from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildProfile:
    profile_id: str = "commercial"
    label: str = "Comercial"
    app_name: str = "Anvic Network Sentinel"
    window_title_suffix: str = ""
    require_license_activation: bool = True
    preload_default_equipment: bool = True
    auto_login_demo_user: bool = False
    enable_visual_supervision: bool = True
    enable_support_center: bool = True
    enable_administration: bool = True


DEFAULT_BUILD_PROFILE = BuildProfile()


def _candidate_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [repo_root / "build_profile.json"]

    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, Path(sys._MEIPASS) / "build_profile.json")

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "build_profile.json")

    return candidates


def load_build_profile() -> BuildProfile:
    data: dict = {}
    for candidate in _candidate_paths():
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                break
            except Exception:
                data = {}

    merged = asdict(DEFAULT_BUILD_PROFILE)
    for key, value in data.items():
        if key in merged:
            merged[key] = value
    return BuildProfile(**merged)
