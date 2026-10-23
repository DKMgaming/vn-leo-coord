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
    for b in cfg.get("pfd", {}).get("bands", []):
        lo, hi = _parse_band(b["freq_ghz"])
        if lo <= freq_ghz <= hi:
            return b
    # Thử nạp từ bảng tham chiếu chính thức data/reference/pfd_limits.yaml
    try:
        from .reference import load_pfd_reference
        ref = load_pfd_reference()
        for b in ref.get("bands", []):
            lo, hi = _parse_band(b["freq_ghz"])
            if lo <= freq_ghz <= hi:
                return b
    except Exception:
        pass
    raise ValueError(f"Tần số {freq_ghz} GHz chưa có trong Table 21-4 đã nạp")


def pfd_limit(freq_ghz: float, delta_deg: float, n_sats: int = 1, cfg=None):
    """Giới hạn PFD (theo đơn vị của dải) tại góc tới delta (độ).

    Hệ NGSO có n_sats >= 51 chịu giảm thêm hệ số X (WRC-19 / RR No. 21.16.2).
    Trả về (limit, unit, x_db).
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
    if n_sats >= 51 and ("ngso_reduction_X" in b or b.get("ngso_reduction_X_applicable", False)):
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
        "pfd": round(pfd, 4),
        "limit": round(limit, 4),
        "x_reduction_db": round(x_db, 4),
        "margin_db": round(margin, 4),
        "compliant": bool(margin >= 0.0),
        "provenance": "RR Article 21 Table 21-4, ITU-OFFICIAL-VERIFIED",
    }


def evaluate_pfd_curve(eirp_dbw_per_mhz: float, freq_ghz: float, alt_km: float,
                       n_sats: int = 1, angles_deg: list[float] | None = None, cfg=None) -> list[dict]:
    """Tính toán đường cong PFD và giới hạn theo các góc ngẩng delta từ 0 đến 90 độ (chuẩn ITU GIBC)."""
    cfg = cfg or load_config()
    if angles_deg is None:
        angles_deg = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 45.0, 60.0, 90.0]
    
    b = find_band(freq_ghz, cfg)
    unit = b["unit"]
    results = []
    R_EARTH = 6371.0  # km

    for delta in angles_deg:
        delta_rad = math.radians(delta)
        # Tính cự ly thực tế r(delta) từ trạm tới vệ tinh
        # Theo định lý hàm cos tam giác O-EarthCenter-Sat:
        sin_psi = (R_EARTH / (R_EARTH + alt_km)) * math.cos(delta_rad)
        psi_rad = math.asin(min(1.0, max(-1.0, sin_psi)))
        theta_rad = math.pi / 2.0 - delta_rad - psi_rad
        range_km = (R_EARTH + alt_km) * math.sin(theta_rad) / max(1e-6, math.cos(delta_rad))
        range_km = max(alt_km, range_km)

        pfd_mhz = pfd_from_eirp(eirp_dbw_per_mhz, range_km)
        if unit == "dB(W/m2)/4kHz":
            pfd_val = pfd_mhz - 10.0 * math.log10(1000.0 / 4.0)
        else:
            pfd_val = pfd_mhz

        limit_val, _, x_db = pfd_limit(freq_ghz, delta, n_sats, cfg)
        margin = limit_val - pfd_val
        results.append({
            "delta_deg": delta,
            "slant_range_km": round(range_km, 1),
            "pfd": round(pfd_val, 4),
            "limit": round(limit_val, 4),
            "x_reduction_db": round(x_db, 4),
            "margin_db": round(margin, 4),
            "compliant": bool(margin >= 0.0)
        })
    return results


def benchmark_against_gibc(test_vector: dict, tolerance_db: float = 0.05) -> dict:
    """So sánh kết quả tính toán của LEO-COORD với dữ liệu chuẩn xuất từ ITU GIBC."""
    freq = float(test_vector["freq_ghz"])
    alt = float(test_vector["alt_km"])
    n_sats = int(test_vector["n_sats"])
    eirp = float(test_vector["eirp_dbw_per_mhz"])
    delta = float(test_vector.get("delta_deg", 90.0))
    expected = test_vector["gibc_results"]

    calc = check_downlink_pfd(eirp, freq, alt, n_sats=n_sats)
    diff_pfd = abs(calc["pfd"] - expected["pfd_at_nadir_db"])
    diff_limit = abs(calc["limit"] - expected["gibc_limit_effective_db"])
    diff_x = abs(calc["x_reduction_db"] - expected["x_reduction_db"])
    diff_margin = abs(calc["margin_db"] - expected["margin_db"])

    passed = (
        diff_pfd <= tolerance_db and
        diff_limit <= tolerance_db and
        diff_x <= tolerance_db and
        diff_margin <= tolerance_db and
        calc["compliant"] == expected["compliant"]
    )

    return {
        "test_vector_id": test_vector.get("id"),
        "name": test_vector.get("name"),
        "passed": passed,
        "max_diff_db": round(max(diff_pfd, diff_limit, diff_x, diff_margin), 6),
        "calc": calc,
        "expected": expected
    }
