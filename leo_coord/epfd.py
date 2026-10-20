"""Mô phỏng sàng lọc EPFD đường xuống (single-entry) — tinh thần ITU-R S.1503.

PHẠM VI RÕ RÀNG: đây là mô phỏng sàng lọc rút gọn (mẫu ăng-ten tham chiếu
S.465, một trạm mặt đất GSO tham chiếu, giả thiết mọi vệ tinh NGSO phát cực
đại). KHÔNG thay thế phần mềm S.1503 / đánh giá của ITU BR cho hồ sơ chính thức.

Định nghĩa EPFD (RR 22.5C): EPFD = 10log10( Σ_i 10^(pfd_i/10) * g_i/g_max ),
với g_i là độ tăng ích ăng-ten nạn nhân theo hướng nguồn nhiễu i.
"""
from __future__ import annotations

import math
import numpy as np

from .config import load_config
from .orbits import R_EARTH

R_GEO = 42164.0  # km — bán kính quỹ đạo địa tĩnh


def dish_gmax_dbi(d_m: float, freq_ghz: float, efficiency: float = 0.6) -> float:
    """Độ tăng ích cực đại của ăng-ten parabol (dBi)."""
    lam = 0.3 / freq_ghz  # bước sóng (m)
    return 10.0 * math.log10(efficiency * (math.pi * d_m / lam) ** 2)


def s465_gain_dbi(theta_deg, gmax_dbi: float):
    """Mẫu bức xạ tham chiếu ITU-R S.465 (bao ngoài sàng lọc).

    G = 32 - 25log10(theta) dBi với 1° <= theta < 48°; -10 dBi ngoài 48°;
    trong 1° lấy gmax.
    """
    th = np.asarray(theta_deg, dtype=float)
    g = np.where(
        th < 1.0, gmax_dbi,
        np.where(th < 48.0,
                 np.minimum(gmax_dbi, 32.0 - 25.0 * np.log10(np.maximum(th, 1.0))),
                 -10.0))
    return g


def _gs_ecef(lat_deg: float, lon_deg: float, r_km: float = R_EARTH) -> np.ndarray:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return r_km * np.array([math.cos(lat) * math.cos(lon),
                            math.cos(lat) * math.sin(lon),
                            math.sin(lat)])


def single_entry_epfd_down(constellation, eirp_dbw_per_mhz: float, freq_ghz: float,
                           victim_lat: float, victim_lon: float, gso_lon_deg: float,
                           dish_d_m: float = 0.6, t0_unix: float = 0.0,
                           duration_s: float = 86400.0, dt_s: float = 60.0,
                           cfg=None) -> dict:
    """Mô phỏng EPFD↓ đơn lẻ vào một trạm mặt đất GSO tham chiếu.

    Trả về các mẫu EPFD (dBW/m2/40kHz) theo thời gian và phân vị, kèm so sánh
    sàng lọc với điểm không-bao-giờ-vượt-quá của Table 22-1A.
    """
    cfg = cfg or load_config()
    anchor = cfg["epfd"]["single_entry"]["never_exceed_dbw_m2_40khz"]

    times = np.arange(t0_unix, t0_unix + duration_s, dt_s)
    sat_ecef = constellation.ecef_positions(times)  # (T, S, 3)
    gs = _gs_ecef(victim_lat, victim_lon)
    gso = _gs_ecef(0.0, gso_lon_deg, R_GEO)
    bore = gso - gs
    bore = bore / np.linalg.norm(bore)
    up = gs / np.linalg.norm(gs)

    gmax = dish_gmax_dbi(dish_d_m, freq_ghz)
    eirp_40k = eirp_dbw_per_mhz - 10.0 * math.log10(1000.0 / 40.0)

    n_t = times.size
    epfd = np.full(n_t, np.nan)
    for k in range(n_t):
        sats = sat_ecef[k]  # (S, 3)
        rho = sats - gs  # (S, 3)
        rng = np.linalg.norm(rho, axis=1)  # km
        los = rho / rng[:, None]
        sin_el = los @ up
        vis = sin_el > 0.0  # trên đường chân trời
        if not np.any(vis):
            continue
        rho_v, rng_v, los_v = rho[vis], rng[vis], los[vis]
        r_m = rng_v * 1000.0
        pfd = eirp_40k - 10.0 * np.log10(4.0 * math.pi * r_m ** 2)  # dBW/m2/40kHz
        cos_th = np.clip(los_v @ bore, -1.0, 1.0)
        theta = np.degrees(np.arccos(cos_th))
        g_rel = s465_gain_dbi(theta, gmax) - gmax  # <= 0 dB
        lin = np.sum(10.0 ** ((pfd + g_rel) / 10.0))
        epfd[k] = 10.0 * math.log10(lin)

    finite = epfd[np.isfinite(epfd)]
    pct = [0, 50, 90, 99, 99.9, 100]
    percentiles = {}
    if finite.size:
        vals = np.percentile(finite, pct)
        percentiles = {f"p{p}": float(v) for p, v in zip(pct, vals)}
    result = {
        "unit": "dBW/m2/40kHz",
        "n_samples": n_t,
        "n_valid": int(finite.size),
        "percentiles": percentiles,
        "max": float(np.nanmax(epfd)) if finite.size else None,
        "anchor_22_1A": anchor,
        "margin_vs_anchor_db": (anchor - float(np.nanmax(epfd))) if finite.size else None,
        "screening_pass": bool(finite.size and np.nanmax(epfd) <= anchor),
        "assumptions": ("S.465 screening envelope; moi ve tinh phat cuc dai; "
                        "mot tram GSO tham chieu; KHONG thay the S.1503/ITU BR"),
        "provenance": "RR Article 22 Table 22-1A anchor, index-sourced",
    }
    return result
