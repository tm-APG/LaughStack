"""Config loading: config/default.yaml plus optional per-engagement overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Default config lives at <repo>/config/default.yaml in the source layout;
# deployment copies of the package (e.g. Cloud Functions) bundle it inside
# the package as _default_config.yaml instead. First hit wins.
_DEFAULT_CANDIDATES = (
    Path(__file__).resolve().parent / "_default_config.yaml",
    Path(__file__).resolve().parents[2] / "config" / "default.yaml",
)


def load_config(override_path: str | Path | None = None) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    for p in _DEFAULT_CANDIDATES:
        if p.exists():
            cfg = yaml.safe_load(p.read_text()) or {}
            break
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
