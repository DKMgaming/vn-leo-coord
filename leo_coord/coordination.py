"""Xác định nhu cầu phối hợp tần số — RR Article 9, Appendix 5/8 (sàng lọc).

- Cung phối hợp Appendix 5 Table 5-1 (sàng lọc hình học rút gọn).
- Ngưỡng PFD kích hoạt phối hợp 9.7A/9.7B.
- Tiêu chí ΔT/T 6% (Appendix 8) — tính từ PFD nhiễu, G/T nạn nhân.

Đây là sàng lọc sơ bộ; thủ tục phối hợp chính thức theo RR Article 9 và
phần mềm của ITU BR.
"""
from __future__ import annotations

import math
import numpy as np

from .config import load_config
from .orbits import R_EARTH
from .epfd import R_GEO


def _band_lo_hi(spec: str):
    return tuple(float(x) for x in spec.split()[0].split("-"))


def coordination_arc(freq_ghz: float, cfg=None) -> float:
    """Cung phối hợp (độ) theo Appendix 5 Table 5-1 cho tần số cho trước."""
    cfg = cfg or load_config()
    for a in cfg["coordination"]["arcs"]:
        lo, hi = _band_lo_hi(a["band"])
        if lo <= freq_ghz <= hi:
            return float(a["arc_deg"])
    raise ValueError(f"Tần số {freq_ghz} GHz chưa có cung phối hợp trong config")


def bands_overlap(b1, b2) -> bool:
    """Hai dải (lo, hi) có chồng lấn không."""
    return max(b1[0], b2[0]) <= min(b1[1], b2[1])


def pfd_trigger_9_7(freq_ghz: float, cfg=None):
    """Ngưỡng PFD kích hoạt phối hợp 9.7A/9.7B. Trả về (value, unit) hoặc None."""
    cfg = cfg or load_config()
    for t in cfg["coordination"]["pfd_triggers_9_7"]:
        lo, hi = _band_lo_hi(t["band"])
        if lo <= freq_ghz <= hi:
            return float(t["value"]), t["unit"]
    return None


def delta_t_over_t_percent(pfd_dbw_m2_per_hz: float, freq_ghz: float,
                           g_t_dbk: float, bw_hz: float) -> float:
    """ΔT/T (%) theo Appendix 8 từ PFD nhiễu (dBW/m2/Hz), G/T và băng thông.

    ΔT/T = pfd * λ² * (G/T) / (4π·k·B)  (tuyến tính).
    """
    lam = 0.3 / freq_ghz
    val_db = (pfd_dbw_m2_per_hz + 20.0 * math.log10(lam) + g_t_dbk
              - 10.0 * math.log10(4.0 * math.pi) + 228.6
              - 10.0 * math.log10(bw_hz))
    return 100.0 * 10.0 ** (val_db / 10.0)


def coordination_triggered_by_delta_t(delta_t_percent: float, cfg=None) -> bool:
    cfg = cfg or load_config()
    return delta_t_percent > cfg["coordination"]["delta_T_over_T_trigger_percent"]


def _ground_ecef(lat_deg: float, lon_deg: float) -> np.ndarray:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return R_EARTH * np.array([math.cos(lat) * math.cos(lon),
                               math.cos(lat) * math.sin(lon),
                               math.sin(lat)])


def screen_ngso_vs_gso(constellation, freq_ghz: float, eirp_dbw_per_mhz: float,
                       gso_lon_deg: float, ref_points,
                       t0_unix: float = 0.0, duration_s: float = 43200.0,
                       dt_s: float = 120.0, cfg=None) -> dict:
    """Sàng lọc phối hợp giữa chòm sao NGSO và một mạng GSO tham chiếu.

    Kiểm tra: (1) góc phân tách địa tâm tối thiểu (nhìn từ điểm tham chiếu)
    giữa vệ tinh NGSO và vệ tinh GSO so với cung phối hợp Appendix 5;
    (2) PFD cực đại tại điểm tham chiếu so với ngưỡng 9.7A/9.7B.

    ref_points: list (lat, lon, tên).
    """
    cfg = cfg or load_config()
    arc = coordination_arc(freq_ghz, cfg)
    trig = pfd_trigger_9_7(freq_ghz, cfg)

    times = np.arange(t0_unix, t0_unix + duration_s, dt_s)
    sat_ecef = constellation.ecef_positions(times)  # (T, S, 3)
    gso = R_GEO * np.array([math.cos(math.radians(gso_lon_deg)),
                            math.sin(math.radians(gso_lon_deg)), 0.0])

    min_sep_overall = 180.0
    max_pfd_overall = -np.inf
    per_point = []
    for lat, lon, pname in ref_points:
        gs = _ground_ecef(lat, lon)
        bore = gso - gs
        bore /= np.linalg.norm(bore)
        rho = sat_ecef - gs  # (T, S, 3)
        rng = np.linalg.norm(rho, axis=-1)
        los = rho / rng[..., None]
        up = gs / np.linalg.norm(gs)
        vis = (los @ up) > 0.0
        cos_sep = np.clip(los @ bore, -1.0, 1.0)
        sep = np.degrees(np.arccos(cos_sep))
        sep_vis = np.where(vis, sep, np.inf)
        min_sep = float(np.min(sep_vis)) if np.any(vis) else None
        # PFD cực đại (mọi vệ tinh phát cực đại) — dBW/m2/40kHz
        eirp_40k = eirp_dbw_per_mhz - 10.0 * math.log10(1000.0 / 40.0)
        pfd = np.where(vis,
                       eirp_40k - 10.0 * np.log10(4.0 * math.pi * (rng * 1000.0) ** 2),
                       -np.inf)
        max_pfd = float(np.max(pfd)) if np.any(vis) else None
        per_point.append({"point": pname, "min_separation_deg": min_sep,
                          "max_pfd_dbw_m2_40khz": max_pfd})
        if min_sep is not None:
            min_sep_overall = min(min_sep_overall, min_sep)
        if max_pfd is not None:
            max_pfd_overall = max(max_pfd_overall, max_pfd)

    arc_hit = min_sep_overall <= arc
    pfd_hit = trig is not None and max_pfd_overall >= trig[0]
    need = arc_hit or pfd_hit
    reasons = []
    if arc_hit:
        reasons.append(f"goc phan tach toi thieu {min_sep_overall:.1f}° nam trong cung pho hop ±{arc:g}° (Appendix 5)")
    if pfd_hit:
        reasons.append(f"PFD cuc dai {max_pfd_overall:.1f} dB(W/m2)/40kHz vuot nguong 9.7A/9.7B {trig[0]:g} {trig[1]}")
    return {
        "freq_ghz": freq_ghz,
        "coordination_arc_deg": arc,
        "min_separation_deg": min_sep_overall if min_sep_overall < 180.0 else None,
        "max_pfd_dbw_m2_40khz": max_pfd_overall if np.isfinite(max_pfd_overall) else None,
        "pfd_trigger_9_7": {"value": trig[0], "unit": trig[1]} if trig else None,
        "per_point": per_point,
        "coordination_likely_required": bool(need),
        "reasons": reasons,
        "note": ("Sang loc so bo — tieu chi cung pho hop ap dung rut gon cho NGSO; "
                 "thu tuc chinh thuc theo RR Article 9"),
    }
