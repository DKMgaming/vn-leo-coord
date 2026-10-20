"""Phân tích phủ sóng chòm sao LEO trên lãnh thổ Việt Nam.

- Bán kính phủ (footprint) theo góc ngẩng tối thiểu.
- Thống kê phủ sóng trên lưới: % thời gian có vệ tinh khả kiến, số vệ tinh
  khả kiến trung bình, tại mỗi ô lưới.
- Thống kê tại điểm tham chiếu (Hà Nội, Đà Nẵng, TP.HCM): kèm khoảng trống
  phủ sóng dài nhất (phục vụ đánh giá chất lượng dịch vụ).
"""
from __future__ import annotations

import math
import numpy as np

from .orbits import R_EARTH, elevation_and_range


def footprint_radius_km(alt_km: float, min_elev_deg: float) -> float:
    """Bán kính phủ mặt đất (km) ứng với góc ngẩng tối thiểu."""
    el = math.radians(min_elev_deg)
    central = math.acos((R_EARTH / (R_EARTH + alt_km)) * math.cos(el)) - el
    return central * R_EARTH


def _visible_matrix(sat_ecef, gs_lat, gs_lon, min_elev_deg):
    """Ma trận khả kiến (T, S) bool. sat_ecef shape (T, S, 3)."""
    el, _ = elevation_and_range(sat_ecef, gs_lat, gs_lon)
    return el >= min_elev_deg


def point_stats(sat_ecef, times_s, gs_lat, gs_lon, min_elev_deg=10.0) -> dict:
    """Thống kê phủ sóng tại một điểm mặt đất."""
    vis = _visible_matrix(sat_ecef, gs_lat, gs_lon, min_elev_deg)  # (T, S)
    any_vis = vis.any(axis=1)
    n_vis = vis.sum(axis=1)
    dt = float(times_s[1] - times_s[0]) if len(times_s) > 1 else 0.0
    # khoảng trống dài nhất (phút)
    max_gap = 0.0
    cur = 0.0
    for v in any_vis:
        if v:
            max_gap = max(max_gap, cur)
            cur = 0.0
        else:
            cur += dt
    max_gap = max(max_gap, cur)
    return {
        "lat": gs_lat,
        "lon": gs_lon,
        "fraction_covered": float(any_vis.mean()),
        "mean_sats_visible": float(n_vis.mean()),
        "max_gap_min": float(max_gap / 60.0),
        "min_elev_deg": min_elev_deg,
    }


def coverage_grid(constellation, bbox, grid_step_deg=0.5, min_elev_deg=10.0,
                  t0_unix=0.0, duration_s=86400.0, dt_s=60.0) -> dict:
    """Thống kê phủ sóng trên lưới chữ nhật.

    bbox = (lat_min, lat_max, lon_min, lon_max).
    Trả về dict gồm lats, lons, fraction_covered (Ny, Nx), mean_sats (Ny, Nx).
    """
    lat_min, lat_max, lon_min, lon_max = bbox
    lats = np.arange(lat_min, lat_max + 1e-9, grid_step_deg)
    lons = np.arange(lon_min, lon_max + 1e-9, grid_step_deg)
    times = np.arange(t0_unix, t0_unix + duration_s, dt_s)
    sat_ecef = constellation.ecef_positions(times)  # (T, S, 3)

    frac = np.zeros((lats.size, lons.size))
    mean_n = np.zeros((lats.size, lons.size))
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            vis = _visible_matrix(sat_ecef, float(la), float(lo), min_elev_deg)
            frac[i, j] = vis.any(axis=1).mean()
            mean_n[i, j] = vis.sum(axis=1).mean()
    return {
        "lats": lats,
        "lons": lons,
        "fraction_covered": frac,
        "mean_sats_visible": mean_n,
        "min_elev_deg": min_elev_deg,
        "constellation": constellation.name,
    }
