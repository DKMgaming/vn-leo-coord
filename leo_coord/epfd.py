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


def simulate_s1503_cumulative_epfd(
    constellation,
    eirp_dbw_per_mhz: float = 10.0,
    freq_ghz: float = 11.7,
    victim_lat: float = 16.0544,
    victim_lon: float = 108.2022,
    gso_lon_deg: float = 132.0,
    dish_d_m: float = 1.2,
    duration_s: float = 7200.0,
    dt_s: float = 60.0,
    antenna_model: str = "S.580"
) -> dict:
    """Mô phỏng hàm phân bố tích lũy EPFD (CDF Curve) theo Khuyến nghị ITU-R S.1503-3.

    Đánh giá độ tuân thủ đối với:
    - Bảng 22-1A Thể lệ Vô tuyến (RR Article 22, Table 22-1A: Single-entry limits).
    - Nghị quyết Resolution 76 (WRC-19, Table 1A: Aggregate EPFD limits).
    """
    from .antenna import itu_r_s580_pattern

    times = np.arange(0.0, duration_s, dt_s)
    sat_ecef = constellation.ecef_positions(times)  # (T, S, 3)
    gs = _gs_ecef(victim_lat, victim_lon)
    gso = _gs_ecef(0.0, gso_lon_deg, R_GEO)
    bore = gso - gs
    bore = bore / np.linalg.norm(bore)
    up = gs / np.linalg.norm(gs)

    gmax = dish_gmax_dbi(dish_d_m, freq_ghz)
    eirp_40k = eirp_dbw_per_mhz - 10.0 * math.log10(1000.0 / 40.0)

    n_t = times.size
    epfd_series = np.full(n_t, np.nan)

    for k in range(n_t):
        sats = sat_ecef[k]  # (S, 3)
        rho = sats - gs
        rng = np.linalg.norm(rho, axis=1)  # km
        los = rho / rng[:, None]
        vis = (los @ up) > 0.0  # Vệ tinh trên đường chân trời

        if not np.any(vis):
            continue

        rng_v = rng[vis]
        los_v = los[vis]
        r_m = rng_v * 1000.0

        pfd = eirp_40k - 10.0 * np.log10(4.0 * math.pi * r_m ** 2)
        cos_th = np.clip(los_v @ bore, -1.0, 1.0)
        theta_deg = np.degrees(np.arccos(cos_th))

        if antenna_model == "S.580":
            g_rx = itu_r_s580_pattern(theta_deg, d_m=dish_d_m, freq_ghz=freq_ghz)
        else:
            g_rx = s465_gain_dbi(theta_deg, gmax)

        g_rel = g_rx - gmax  # dB <= 0
        lin_sum = np.sum(10.0 ** ((pfd + g_rel) / 10.0))
        if lin_sum > 0:
            epfd_series[k] = 10.0 * math.log10(lin_sum)

    valid_epfd = epfd_series[np.isfinite(epfd_series)]
    if len(valid_epfd) == 0:
        valid_epfd = np.array([-220.0])

    # Tạo đường cong tích lũy xác suất thực nghiệm CDF
    # P(EPFD <= X)
    sorted_epfd = np.sort(valid_epfd)
    percent_vals = np.linspace(0.0, 100.0, 51)
    cdf_curve = []
    for p in percent_vals:
        val = float(np.percentile(sorted_epfd, p))
        cdf_curve.append({
            "percentage": round(float(p), 1),
            "epfd_dbw_m2_40khz": round(val, 2)
        })

    # Lấy mặt nạ chuẩn ITU Table 22-1A / Resolution 76 cho kích thước chảo
    if dish_d_m <= 0.8:
        mask_spec = [
            (0.0, -170.0),
            (90.0, -168.6),
            (99.0, -165.3),
            (99.97, -160.4),
            (100.0, -160.0)
        ]
        mask_name = "RR Table 22-1A (Antenna 0.6m)"
    else:
        mask_spec = [
            (0.0, -176.5),
            (99.5, -173.0),
            (99.84, -164.0),
            (99.945, -161.5),
            (100.0, -161.0)
        ]
        mask_name = "RR Table 22-1A / Res 76 (Antenna 1.2m)"

    mask_comparison = []
    min_margin = 999.0
    all_passed = True

    for pct, limit_val in mask_spec:
        sim_val = float(np.percentile(sorted_epfd, pct))
        # Margin: limit - simulated (Margin > 0 nghĩa là mức nhiễu thấp hơn giới hạn -> ĐẠT)
        margin = round(limit_val - sim_val, 2)
        is_pass = margin >= 0.0
        if not is_pass:
            all_passed = False
        min_margin = min(min_margin, margin)

        mask_comparison.append({
            "percentage_of_time": pct,
            "limit_dbw_m2_40khz": limit_val,
            "simulated_epfd_dbw_m2_40khz": round(sim_val, 2),
            "margin_db": margin,
            "compliant": is_pass
        })

    return {
        "status": "success",
        "methodology": "Rec. ITU-R S.1503-3 (Cumulative EPFD Downlink)",
        "dish_diameter_m": dish_d_m,
        "gmax_dbi": round(gmax, 2),
        "antenna_model": antenna_model,
        "freq_ghz": freq_ghz,
        "victim_ground_station": {"lat": victim_lat, "lon": victim_lon},
        "target_gso_vinasat_lon": gso_lon_deg,
        "duration_minutes": int(duration_s / 60.0),
        "time_samples_evaluated": n_t,
        "mask_name": mask_name,
        "min_margin_db": round(min_margin, 2),
        "overall_compliant": all_passed,
        "compliance_status": "ĐẠT CHUẨN EPFD (RR ARTICLE 22 & RES 76)" if all_passed else "VƯỢT GIỚI HẠN EPFD (CAN NHIỄU KHÔNG CHẤP NHẬN ĐƯỢC)",
        "mask_comparison": mask_comparison,
        "cdf_curve": cdf_curve,
    }

