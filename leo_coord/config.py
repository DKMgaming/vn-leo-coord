"""Nạp khung tham số kỹ thuật versioned (configs/leo_coord.yaml).

Quy ước: mọi ngưỡng kỹ thuật sống ở file YAML, không hard-code trong source.
"""
from __future__ import annotations

from pathlib import Path
import yaml


def config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "configs" / "leo_coord.yaml"


def load_config(path=None) -> dict:
    p = Path(path) if path else config_path()
    return yaml.safe_load(p.read_text(encoding="utf-8"))
