"""Config loading: config/default.yaml plus optional per-engagement overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "default.yaml"


def load_config(override_path: str | Path | None = None) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    if _DEFAULT_PATH.exists():
        cfg = yaml.safe_load(_DEFAULT_PATH.read_text()) or {}
    if override_path:
        over = yaml.safe_load(Path(override_path).read_text()) or {}
        cfg = _deep_merge(cfg, over)
    return cfg


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
