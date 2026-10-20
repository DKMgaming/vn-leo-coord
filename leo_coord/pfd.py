"""Kiểm tra giới hạn mật độ thông lượng công suất (PFD) — RR Article 21, Table 21-4.

Áp dụng cho đánh giá sàng lọc đường xuống (space-to-Earth) của hệ NGSO tại
điểm chiếu vệ tinh (góc tới 90°, cự ly ngắn nhất — trường hợp xấu nhất).

Số liệu giới hạn lấy từ configs/leo_coord.yaml (index-sourced — cần đối chiếu
văn bản ITU gốc trước khi dùng cho kết luận chính thức).
"""
from __future__ import annotations

import math
import numpy as np

from .config import load_config


def _parse_band(freq_range: str):
    lo, hi = freq_range.split("-")
    return float(lo), float(hi)


def find_band(freq_ghz: float, cfg=None) -> dict:
    """Tìm dải tần trong Table 21-4 chứa tần số cho trước."""
    cfg = cfg or load_config()
    for b in cfg["pfd"]["bands"]:
        lo, hi = _parse_band(b["freq_ghz"])
        if lo <= freq_ghz <= hi:
            return b
    raise ValueError(f"Tần số {freq_ghz} GHz chưa có trong Table 21-4 đã nạp")


def pfd_limit(freq_ghz: float, delta_deg: float, n_sats: int = 1, cfg=None):
    """Giới hạn PFD (theo đơn vị của dải) tại góc tới delta (độ).

    Hệ NGSO có n_sats >= 51 chịu giảm thêm hệ số X (WRC-19).
    Trả về (limit, unit).
    """
    b = find_band(freq_ghz, cfg)
    d = float(delta_deg)
    if d <= 5.0:
        lim = b["delta_le_5"]
    elif d >= 25.0:
        lim = b["delta_ge_25"]
    else:
        lim = b["delta_le_5"] + b["slope"] * (d - 5.0)
    x_db = 0.0
    if n_sats >= 51 and "ngso_reduction_X" in b:
        n = int(n_sats)
        x_db = (5.0 / 119.0) * (n - 50) if n <= 288 else (1.0 / 69.0) * (n + 402)
        lim -= x_db
    return lim, b["unit"], x_db


def pfd_from_eirp(eirp_dbw: float, range_km: float) -> float:
    """PFD (dBW/m2) từ EIRP tại cự ly cho trước (cùng băng thông tham chiếu)."""
    r_m = range_km * 1000.0
    return eirp_dbw - 10.0 * math.log10(4.0 * math.pi * r_m ** 2)


def check_downlink_pfd(eirp_dbw_per_mhz: float, freq_ghz: float, alt_km: float,
                       n_sats: int = 1, cfg=None) -> dict:
    """Kiểm tra PFD đường xuống tại điểm chiếu vệ tinh (trường hợp xấu nhất).

    eirp_dbw_per_mhz: EIRP phổ trên 1 MHz (dBW/MHz).
    """
    cfg = cfg or load_config()
    b = find_band(freq_ghz, cfg)
    unit = b["unit"]
    pfd_mhz = pfd_from_eirp(eirp_dbw_per_mhz, alt_km)
    if unit == "dB(W/m2)/4kHz":
        pfd = pfd_mhz - 10.0 * math.log10(1000.0 / 4.0)
    else:
        pfd = pfd_mhz
    limit, _, x_db = pfd_limit(freq_ghz, 90.0, n_sats, cfg)
    margin = limit - pfd
    return {
        "freq_ghz": freq_ghz,
        "band": b["freq_ghz"],
        "unit": unit,
        "delta_deg": 90.0,
        "eirp_dbw_per_mhz": eirp_dbw_per_mhz,
        "pfd": pfd,
        "limit": limit,
        "x_reduction_db": x_db,
        "margin_db": margin,
        "compliant": bool(margin >= 0.0),
        "provenance": "RR Article 21 Table 21-4, index-sourced — can doi chieu van ban goc",
    }
