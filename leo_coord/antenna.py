"""Mô hình hóa búp sóng ăng-ten thực tế theo Khuyến nghị ITU-R.

Hiện thực các tiêu chuẩn ITU-R:
- Rec. ITU-R S.1428-1: Giản đồ bức xạ ăng-ten mảng pha (phased array) cho vệ tinh phi địa tĩnh LEO FSS (10.7-12.75 GHz & 17.7-20.2 GHz).
- Rec. ITU-R S.672-4: Giản đồ bức xạ ăng-ten vệ tinh địa tĩnh GSO (Vinasat-1/2).
- Rec. ITU-R S.580-6: Giản đồ bức xạ ăng-ten trạm thu mặt đất GSO FSS.
- Phân tích hình học sự kiện thẳng hàng (In-line Event) và tính toán can nhiễu trên trục ngắm Vinasat.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple, Union
import numpy as np


def itu_r_s1428_pattern(
    theta_deg: Union[float, np.ndarray],
    g_max_dbi: float = 35.0,
    theta_3db_deg: float = 2.5,
    l_s_db: float = 20.0,
    g_min_dbi: float = -10.0
) -> Union[float, np.ndarray]:
    """Giản đồ bức xạ ăng-ten vệ tinh LEO FSS theo Khuyến nghị ITU-R S.1428-1.

    Args:
        theta_deg: Góc lệch trục tính từ đỉnh búp sóng (0 <= theta <= 180 độ).
        g_max_dbi: Độ lợi cực đại tại đỉnh búp sóng chính (dBi).
        theta_3db_deg: Độ rộng búp sóng nửa công suất (Half-Power Beamwidth - HPBW) (độ).
        l_s_db: Mức suy giảm búp sóng phụ so với đỉnh (relative sidelobe level, thường 20-25 dB).
        g_min_dbi: Mức sàn độ lợi nhỏ nhất ở bán cầu sau (dBi).

    Returns:
        Độ lợi bức xạ G(theta) tính bằng dBi.
    """
    is_scalar = np.isscalar(theta_deg)
    th = np.abs(np.atleast_1d(theta_deg).astype(float))

    theta_0 = float(theta_3db_deg)
    # Góc chuyển tiếp từ búp sóng chính sang búp sóng phụ
    theta_b = theta_0 * math.sqrt(l_s_db / 12.0)
    theta_1 = 1.5 * theta_0
    if theta_b > theta_1:
        theta_1 = theta_b * 1.2

    gain = np.zeros_like(th)

    # 1. Búp sóng chính (Main beam)
    mask1 = th <= theta_b
    gain[mask1] = g_max_dbi - 12.0 * ((th[mask1] / theta_0) ** 2)

    # 2. Vùng chuyển tiếp búp sóng phụ cận (Plateau / First sidelobes)
    mask2 = (th > theta_b) & (th <= theta_1)
    gain[mask2] = g_max_dbi - l_s_db

    # 3. Vùng búp sóng phụ xa (Far sidelobes roll-off)
    mask3 = th > theta_1
    val3 = g_max_dbi - l_s_db - 25.0 * np.log10(np.maximum(1e-6, th[mask3] / theta_1))
    gain[mask3] = np.maximum(g_min_dbi, val3)

    return float(gain[0]) if is_scalar else gain


def itu_r_s672_pattern(
    theta_deg: Union[float, np.ndarray],
    g_max_dbi: float = 42.0,
    theta_3db_deg: float = 1.5,
    l_s_db: float = 20.0,
    g_min_dbi: float = 0.0
) -> Union[float, np.ndarray]:
    """Giản đồ bức xạ ăng-ten vệ tinh địa tĩnh GSO theo Khuyến nghị ITU-R S.672-4.

    Thường áp dụng cho búp sóng vệ tinh Vinasat-1/2 chiếu xuống lãnh thổ Việt Nam.
    """
    is_scalar = np.isscalar(theta_deg)
    th = np.abs(np.atleast_1d(theta_deg).astype(float))

    theta_0 = float(theta_3db_deg)
    u = th / theta_0
    u_1 = math.sqrt(l_s_db / 12.0)
    u_2 = 1.5

    gain = np.zeros_like(th)

    # Vùng búp sóng chính
    m1 = u <= u_1
    gain[m1] = g_max_dbi - 12.0 * (u[m1] ** 2)

    # Vùng plateau búp sóng phụ
    m2 = (u > u_1) & (u <= u_2)
    gain[m2] = g_max_dbi - l_s_db

    # Vùng suy giảm xa
    m3 = u > u_2
    val3 = g_max_dbi - l_s_db - 25.0 * np.log10(np.maximum(1e-6, u[m3] / u_2))
    gain[m3] = np.maximum(g_min_dbi, val3)

    return float(gain[0]) if is_scalar else gain


def itu_r_s580_pattern(
    theta_deg: Union[float, np.ndarray],
    d_m: float = 1.2,
    freq_ghz: float = 11.7
) -> Union[float, np.ndarray]:
    """Giản đồ bức xạ ăng-ten trạm thu mặt đất GSO theo Khuyến nghị ITU-R S.580-6.

    Đặc trưng cho khả năng phân biệt góc (Spatial Discrimination) của chảo thu Vinasat
    khi có vệ tinh LEO bay lệch trục góc theta (độ).
    """
    is_scalar = np.isscalar(theta_deg)
    th = np.abs(np.atleast_1d(theta_deg).astype(float))

    # Bước sóng lambda (m)
    wavelength_m = 0.299792458 / freq_ghz
    d_over_lambda = d_m / wavelength_m
    # Độ lợi cực đại lý thuyết với hiệu suất 60%
    g_max_dbi = 20.0 * math.log10(max(1.0, d_over_lambda)) + 10.0 * math.log10(0.6 * (math.pi ** 2))
    theta_min = max(1.0, 100.0 / d_over_lambda)

    gain = np.zeros_like(th)

    # 1. Trong búp sóng chính (theta <= theta_min)
    m1 = th <= theta_min
    gain[m1] = g_max_dbi - 2.5e-3 * ((d_over_lambda * th[m1]) ** 2)

    # 2. Vùng búp sóng phụ cận (theta_min < theta <= 20 deg)
    m2 = (th > theta_min) & (th <= 20.0)
    gain[m2] = 29.0 - 25.0 * np.log10(np.maximum(1e-6, th[m2]))

    # 3. Vùng chuyển tiếp (20 < theta <= 48 deg)
    m3 = (th > 20.0) & (th <= 48.0)
    gain[m3] = -3.5

    # 4. Vùng bán cầu sau (48 < theta <= 180 deg)
    m4 = th > 48.0
    gain[m4] = -10.0

    return float(gain[0]) if is_scalar else gain


def lat_lon_alt_to_ecef(lat_deg: float, lon_deg: float, alt_km: float) -> np.ndarray:
    """Chuyển tọa độ trắc địa (WGS-84 cầu) sang tọa độ trực giao Trái đất ECEF (km)."""
    R_EARTH = 6371.0
    r = R_EARTH + alt_km
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    x = r * math.cos(phi) * math.cos(lam)
    y = r * math.cos(phi) * math.sin(lam)
    z = r * math.sin(phi)
    return np.array([x, y, z], dtype=float)


def calculate_in_line_geometry(
    sat_lat: float,
    sat_lon: float,
    sat_alt_km: float,
    gs_lat: float,
    gs_lon: float,
    gso_lon_deg: float = 132.0
) -> Tuple[float, float, float]:
    """Tính toán hình học góc nhìn từ trạm mặt đất tới LEO và tới vệ tinh GSO (Vinasat).

    Returns:
        (separation_angle_deg, range_to_leo_km, range_to_gso_km)
    """
    p_gs = lat_lon_alt_to_ecef(gs_lat, gs_lon, 0.0)
    p_leo = lat_lon_alt_to_ecef(sat_lat, sat_lon, sat_alt_km)
    # Vệ tinh địa tĩnh GSO (Vinasat-1: 132°E, Vinasat-2: 131.8°E) tại quỹ đạo xích đạo 35786 km
    p_gso = lat_lon_alt_to_ecef(0.0, gso_lon_deg, 35786.0)

    # Vector ngắm từ trạm mặt đất tới LEO và GSO
    v_leo = p_leo - p_gs
    v_gso = p_gso - p_gs

    d_leo = float(np.linalg.norm(v_leo))
    d_gso = float(np.linalg.norm(v_gso))

    # Góc lệch trục theta giữa hai đường ngắm
    cos_theta = np.dot(v_leo, v_gso) / (max(1e-6, d_leo) * max(1e-6, d_gso))
    cos_theta = min(1.0, max(-1.0, float(cos_theta)))
    theta_deg = math.degrees(math.acos(cos_theta))

    return theta_deg, d_leo, d_gso


def evaluate_in_line_event(
    sat_lat: float,
    sat_lon: float,
    sat_alt_km: float,
    gs_lat: float,
    gs_lon: float,
    gso_lon_deg: float = 132.0,
    eirp_leo_dbw_per_mhz: float = 15.0,
    dish_d_m: float = 1.2,
    freq_ghz: float = 11.7
) -> Dict[str, Any]:
    """Đánh giá toàn diện nguy cơ can nhiễu thẳng hàng (In-line Event) giữa LEO và Vinasat.

    Xem xét:
    - Góc phân tách theta giữa hướng nhìn Vinasat và vệ tinh LEO.
    - Độ lợi suy giảm trục lệch của ăng-ten chảo Vinasat theo Rec. ITU-R S.580.
    - Ngưỡng can nhiễu và yêu cầu tắt sóng (Beam Blanking).
    """
    sep_deg, d_leo_km, d_gso_km = calculate_in_line_geometry(
        sat_lat, sat_lon, sat_alt_km, gs_lat, gs_lon, gso_lon_deg
    )

    # Độ lợi ăng-ten trạm thu mặt đất hướng LEO tại góc lệch sep_deg
    g_rx_s580 = float(itu_r_s580_pattern(sep_deg, d_m=dish_d_m, freq_ghz=freq_ghz))
    g_rx_peak = float(itu_r_s580_pattern(0.0, d_m=dish_d_m, freq_ghz=freq_ghz))
    discrimination_db = g_rx_peak - g_rx_s580

    # Mật độ thông lượng công suất PFD của LEO tại trạm mặt đất (dBW/m2/MHz)
    r_m = d_leo_km * 1000.0
    pfd_leo_mhz = eirp_leo_dbw_per_mhz - 10.0 * math.log10(4.0 * math.pi * (r_m ** 2))

    # Diện tích hiệu dụng ăng-ten trạm thu (m2)
    wavelength_m = 0.299792458 / freq_ghz
    # Công suất can nhiễu thu được I_rx (dBW/MHz)
    # I = PFD + G_rx + 10*log10(lambda^2 / 4*pi)
    rx_aperture_gain_factor = 10.0 * math.log10((wavelength_m ** 2) / (4.0 * math.pi))
    i_rx_dbw_mhz = pfd_leo_mhz + g_rx_s580 + rx_aperture_gain_factor

    # Phân loại mức độ cảnh báo theo Thể lệ Vô tuyến ITU
    # - In-line event nghiêm trọng khi góc lệch <= 2 độ (nằm trong búp sóng chính trạm GSO)
    # - Cung phối hợp Appendix 5 khi góc lệch <= 6 độ
    if sep_deg <= 2.0:
        risk_level = "CRITICAL_IN_LINE"
        beam_blanking_required = True
        desc = "CẢNH BÁO NGUY CƠ CAO: Vệ tinh LEO bay cắt ngang trục ngắm Vinasat (In-line Event). Bắt buộc kích hoạt chế độ tắt sóng (Beam Blanking) theo RR No. 22.2!"
    elif sep_deg <= 6.0:
        risk_level = "COORDINATION_ZONE"
        beam_blanking_required = False
        desc = "VÙNG PHỐI HỢP: Vệ tinh LEO nằm trong cung bảo vệ ±6° Vinasat (RR Appendix 5). Yêu cầu giám sát mức PFD và góc lệch."
    else:
        risk_level = "SAFE"
        beam_blanking_required = False
        desc = "AN TOÀN: Vệ tinh LEO nằm ngoài cung phối hợp của mạng vệ tinh Vinasat."

    return {
        "separation_angle_deg": round(sep_deg, 3),
        "distance_to_leo_km": round(d_leo_km, 1),
        "distance_to_gso_km": round(d_gso_km, 1),
        "earth_station_dish_d_m": dish_d_m,
        "earth_station_rx_gain_dbi": round(g_rx_s580, 2),
        "rx_spatial_discrimination_db": round(discrimination_db, 2),
        "pfd_at_ground_dbw_m2_mhz": round(pfd_leo_mhz, 2),
        "received_interference_dbw_mhz": round(i_rx_dbw_mhz, 2),
        "risk_level": risk_level,
        "beam_blanking_required": beam_blanking_required,
        "description": desc
    }
