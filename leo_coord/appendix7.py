"""Xác định Vùng Phối Hợp Đài Trái Đất theo Thể Lệ Vô Tuyến ITU RR Phụ Lục 7 (Appendix 7).

Mô phỏng phương pháp luận của công cụ chuẩn ITU AP7Capture v10.0:
- Chế độ 1 (Mode 1): Lan truyền trong điều kiện thời tiết bình thường (tán xạ tầng đối lưu,
  ống dẫn sóng, hấp thụ khí quyển theo ITU-R P.620-7 và P.676-13).
- Chế độ 2 (Mode 2): Lan truyền do tán xạ thủy thạch/tán xạ mưa (ITU-R P.620-7 và P.837-7).
- Đánh giá khả năng cùng tồn tại giữa đài Gateway LEO (băng Ka 27.5-29.5 GHz / 17.7-19.7 GHz)
  và hệ thống thông tin di động 5G mmWave / Tuyến vi ba số mặt đất (Rec. ITU-R M.2101).
- Kiểm tra khả năng xâm lấn qua biên giới các quốc gia lân cận (Lào, Campuchia, Trung Quốc)
  để kích hoạt thủ tục phối hợp quốc tế theo RR No. 9.17 và No. 9.18.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import yaml

from .orbits import R_EARTH

REF_DIR = Path(__file__).resolve().parent.parent / "data" / "reference"
PARAMS_FILE = REF_DIR / "appendix7_params.yaml"


def load_appendix7_params() -> dict:
    """Nạp file tham số quy chuẩn ITU RR Appendix 7."""
    if PARAMS_FILE.exists():
        return yaml.safe_load(PARAMS_FILE.read_text(encoding="utf-8"))
    return {}


def destination_point(lat_deg: float, lon_deg: float, distance_km: float, bearing_deg: float) -> Tuple[float, float]:
    """Tính tọa độ (lat, lon) của điểm đến từ điểm xuất phát theo cự ly và góc phương vị (Great Circle)."""
    phi1 = math.radians(lat_deg)
    lam1 = math.radians(lon_deg)
    brng = math.radians(bearing_deg)
    delta = distance_km / R_EARTH

    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(brng)
    )
    lam2 = lam1 + math.atan2(
        math.sin(brng) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2)
    )

    lat2 = math.degrees(phi2)
    lon2 = (math.degrees(lam2) + 540.0) % 360.0 - 180.0
    return lat2, lon2


def atmospheric_attenuation_rate(freq_ghz: float) -> float:
    """Hệ số suy hao riêng do khí quyển gamma_a = gamma_o + gamma_w (dB/km) theo Rec. ITU-R P.676."""
    f = float(freq_ghz)
    # Xấp xỉ chuẩn ITU-R P.676 cho vùng nhiệt đới Việt Nam (T=27°C, 15 g/m3 hơi nước)
    if f < 15.0:
        gamma_o = 0.010
        gamma_w = 0.012 * (f / 10.0) ** 2
    elif f < 25.0:
        # Gần vạch cộng hưởng hơi nước 22.2 GHz
        gamma_o = 0.015
        gamma_w = 0.08 + 0.12 * math.exp(-((f - 22.2) ** 2) / 6.0)
    elif f < 35.0:
        # Băng Ka (27-30 GHz)
        gamma_o = 0.025
        gamma_w = 0.14 + 0.006 * (f - 28.0)
    else:
        gamma_o = 0.05
        gamma_w = 0.20
    return max(0.015, gamma_o + gamma_w)


def mode1_coordination_distance(
    freq_ghz: float,
    eirp_density_dbw_per_mhz: float,
    horizon_gain_dbi: float = -10.0,
    p_percent: float = 0.01,
    horizon_elev_deg: float = 0.0,
    rx_threshold_dbw_per_mhz: float = -143.0,
    clutter_loss_db: float = 0.0,
) -> float:
    """Tính cự ly phối hợp Chế độ 1 (Mode 1: Clear-air propagation) theo ITU RR Appendix 7 & Rec. ITU-R P.620.

    L_req(p) = EIRP_density + G_horizon - rx_threshold - clutter_loss
    L_trans(d) = L_bfs(d) + gamma_a * d + A_duct_tropo(p)
    """
    f = max(1.0, float(freq_ghz))
    # Suy hao truyền sóng yêu cầu
    l_req = eirp_density_dbw_per_mhz + horizon_gain_dbi - rx_threshold_dbw_per_mhz - clutter_loss_db

    gamma_a = atmospheric_attenuation_rate(f)
    # Hiệu chỉnh góc ngẩng đường chân trời
    theta_h = max(0.0, float(horizon_elev_deg))
    horizon_loss = 20.0 * math.log10(1.0 + 0.5 * theta_h) if theta_h > 0 else 0.0

    # Lặp tìm cự ly d sao cho L_trans(d) = l_req
    # Cự ly tối thiểu theo quy định ITU RR Appendix 7 là 25 km, tối đa 500 km
    d_low, d_high = 25.0, 500.0
    for _ in range(30):
        d_mid = (d_low + d_high) / 2.0
        # Free-space loss
        l_bfs = 92.45 + 20.0 * math.log10(f) + 20.0 * math.log10(d_mid)
        # Suy hao tầng đối lưu và ống dẫn sóng
        # Tỷ lệ thời gian p = 0.01%
        duct_term = 12.0 * math.log10(1.0 / max(0.001, p_percent))
        l_trans = l_bfs + gamma_a * d_mid + horizon_loss + duct_term

        if l_trans < l_req:
            d_low = d_mid
        else:
            d_high = d_mid

    res = (d_low + d_high) / 2.0
    return float(np.clip(res, 25.0, 500.0))


def mode2_rain_scatter_distance(
    freq_ghz: float,
    rain_rate_mm_h: float = 100.0,
    rain_height_km: float = 4.8,
    beam_azimuth_deg: float = 180.0,
    beam_elev_deg: float = 25.0,
    azimuth_deg: float = 0.0,
    p_percent: float = 0.01,
) -> float:
    """Tính cự ly phối hợp Chế độ 2 (Mode 2: Hydrometeor / Rain-scatter) theo ITU RR Appendix 7 & Rec. ITU-R P.620.

    Tâm vùng tán xạ mưa bị lệch khỏi đài trái đất dọc theo búp sóng chính:
    delta_d = h_R / tan(epsilon)
    """
    f = float(freq_ghz)
    eps_rad = math.radians(max(5.0, min(85.0, beam_elev_deg)))
    h_r = float(rain_height_km)

    # Độ dịch tâm hình tán xạ mưa dọc theo hướng búp sóng chính
    delta_d = h_r / math.tan(eps_rad)  # km

    # Bán kính tán xạ mưa cơ sở theo tần số và lượng mưa Việt Nam (Zone P/N: R0.01 = 100 mm/h)
    # Băng Ka (28 GHz) có tán xạ mạnh hơn nhưng suy hao do mưa cao hơn, cự ly quanh 80-180 km
    base_r = 135.0 * (1.0 + 0.1 * math.log10(rain_rate_mm_h / 50.0)) - 1.2 * (f - 18.0)
    base_r = max(40.0, min(240.0, base_r))

    # Tọa độ cực tương đối của tâm mưa so với trạm
    psi_rad = math.radians(azimuth_deg - beam_azimuth_deg)

    # Khoảng cách từ đài trái đất đến đường viền tán xạ mưa theo góc phương vị azimuth_deg
    # Giải phương trình hình tròn lệch tâm: (x - dx)^2 + y^2 = R^2
    # r^2 - 2 r dx cos(psi) + dx^2 - R^2 = 0
    cos_psi = math.cos(psi_rad)
    disc = (delta_d * cos_psi) ** 2 - (delta_d ** 2 - base_r ** 2)
    if disc >= 0:
        r2 = delta_d * cos_psi + math.sqrt(disc)
    else:
        r2 = base_r

    return float(np.clip(r2, 25.0, 350.0))


def calculate_coordination_contour(
    lat_deg: float,
    lon_deg: float,
    freq_ghz: float = 28.5,
    eirp_density_dbw_per_mhz: float = 48.0,
    beam_azimuth_deg: float = 180.0,
    beam_elev_deg: float = 25.0,
    horizon_gain_dbi: float = -10.0,
    clutter_loss_db: float = 0.0,
    step_deg: float = 5.0,
) -> dict:
    """Xác định đa giác Đường viền phối hợp (Coordination Contour) tổng hợp (Mode 1 & Mode 2).

    d_c(alpha) = max(d_1(alpha), d_2(alpha)) với mọi góc phương vị alpha in [0, 360).
    Trả về cấu trúc dữ liệu GeoJSON và các chỉ số diện tích, cự ly cực đại/cực tiểu.
    """
    angles = np.arange(0.0, 360.0, step_deg)
    contour_points = []
    poly_coords = []

    d1_const = mode1_coordination_distance(
        freq_ghz=freq_ghz,
        eirp_density_dbw_per_mhz=eirp_density_dbw_per_mhz,
        horizon_gain_dbi=horizon_gain_dbi,
        clutter_loss_db=clutter_loss_db
    )

    for az in angles:
        d2 = mode2_rain_scatter_distance(
            freq_ghz=freq_ghz,
            beam_azimuth_deg=beam_azimuth_deg,
            beam_elev_deg=beam_elev_deg,
            azimuth_deg=az
        )
        dc = max(d1_const, d2)
        p_lat, p_lon = destination_point(lat_deg, lon_deg, dc, az)

        contour_points.append({
            "azimuth_deg": round(float(az), 1),
            "distance_km": round(float(dc), 2),
            "mode1_km": round(float(d1_const), 2),
            "mode2_km": round(float(d2), 2),
            "lat": round(p_lat, 6),
            "lon": round(p_lon, 6),
        })
        poly_coords.append([round(p_lon, 6), round(p_lat, 6)])

    # Khép kín đa giác
    if poly_coords:
        poly_coords.append(poly_coords[0])

    distances = [p["distance_km"] for p in contour_points]
    max_d = max(distances)
    min_d = min(distances)
    mean_d = sum(distances) / len(distances)
    # Diện tích xấp xỉ hình đa giác: pi * r_eff^2
    area_sq_km = math.pi * (mean_d ** 2)

    return {
        "station_lat": lat_deg,
        "station_lon": lon_deg,
        "freq_ghz": freq_ghz,
        "eirp_density_dbw_per_mhz": eirp_density_dbw_per_mhz,
        "beam_azimuth_deg": beam_azimuth_deg,
        "beam_elev_deg": beam_elev_deg,
        "clutter_loss_db": clutter_loss_db,
        "max_distance_km": round(max_d, 2),
        "min_distance_km": round(min_d, 2),
        "mean_distance_km": round(mean_d, 2),
        "area_sq_km": round(area_sq_km, 1),
        "contour_points": contour_points,
        "geojson_geometry": {
            "type": "Polygon",
            "coordinates": [poly_coords]
        }
    }


def evaluate_coexistence_5g_fs(
    freq_ghz: float = 28.5,
    gateway_eirp_dbw_per_mhz: float = 48.0,
    suburban_clutter_db: float = 15.0,
    urban_clutter_db: float = 25.0,
) -> dict:
    """Đánh giá khả năng cùng tồn tại giữa Gateway LEO băng Ka (28 GHz) và mạng di động 5G / Vi ba mặt đất.

    Theo Khuyến nghị Rec. ITU-R M.2101 và 3GPP TR 38.815:
    - Ngưỡng bảo vệ trạm gốc 5G gNodeB: I/N = -6 dB.
    - Mức nhiễu cực đại cho phép I_limit = -143.0 dBW/MHz.
    """
    f = float(freq_ghz)
    i_limit = -143.0  # dBW/MHz
    # Suy hao truyền sóng yêu cầu
    l_req_raw = gateway_eirp_dbw_per_mhz - i_limit  # dB

    gamma_a = atmospheric_attenuation_rate(f)

    def calc_distance(clutter_db: float) -> float:
        l_needed = l_req_raw - clutter_db
        # Tìm cự ly qua free space + atmospheric
        d = 1.0
        while d < 150.0:
            l_bfs = 92.45 + 20.0 * math.log10(f) + 20.0 * math.log10(d)
            if l_bfs + gamma_a * d >= l_needed:
                return round(d, 2)
            d += 0.2
        return round(d, 2)

    dist_los = calc_distance(0.0)
    dist_suburban = calc_distance(suburban_clutter_db)
    dist_urban = calc_distance(urban_clutter_db)

    # Đánh giá mức độ khả thi
    status = "CHUNG_SONG_TOT" if dist_suburban <= 25.0 else "CAN_QUY_HOACH_VI_TRI"
    recommendation = (
        f"Khoảng cách cách ly bảo vệ (Exclusion Zone) khuyến nghị: "
        f"{dist_urban:.1f} km (Khu vực đô thị có che chắn) đến {dist_suburban:.1f} km (Khu vực ngoại thành). "
        f"Tại vùng nông thôn tầm nhìn thẳng cần cự ly {dist_los:.1f} km. "
        "Khuyến nghị bố trí đài Gateway tại khu công nghiệp ngoại thành, tránh khu dân cư mật độ 5G cao."
    )

    return {
        "freq_ghz": freq_ghz,
        "gateway_eirp_density_dbw_per_mhz": gateway_eirp_dbw_per_mhz,
        "coexisting_network": "Mobile 5G mmWave (3GPP n257/n258: 26.5 - 29.5 GHz) & Fixed Links",
        "protection_criterion": "I/N = -6.0 dB (RR Appendix 7 & Rec. ITU-R M.2101)",
        "i_limit_dbw_per_mhz": i_limit,
        "isolation_loss_required_db": round(l_req_raw, 1),
        "separation_distance_km": {
            "rural_los": dist_los,
            "suburban": dist_suburban,
            "urban": dist_urban,
        },
        "coexistence_status": status,
        "recommendation": recommendation,
    }


def check_cross_border_encroachment(
    station_name: str,
    lat_deg: float,
    lon_deg: float,
    max_contour_distance_km: float,
    station_key: Optional[str] = None,
) -> dict:
    """Kiểm tra đường viền phối hợp của đài trái đất có vượt qua biên giới đất liền quốc gia hay không.

    Nếu cự ly đường viền phối hợp > khoảng cách đến đường biên giới,
    Việt Nam cần thực hiện thủ tục phối hợp quốc tế theo Thể lệ Vô tuyến RR No. 9.17 / 9.18.
    """
    params = load_appendix7_params()
    st_meta = params.get("vietnam_stations", {})

    # Khoảng cách tối thiểu tới biên giới các nước (km)
    border_dists = {}
    if station_key and station_key in st_meta:
        border_dists = st_meta[station_key].get("min_dist_to_border_km", {})
    else:
        # Ước tính danh định dựa trên vĩ độ/kinh độ
        if lat_deg > 20.5:
            border_dists = {"china": 120.0, "laos": 100.0}
        elif lat_deg > 14.5:
            border_dists = {"laos": 70.0}
        else:
            border_dists = {"cambodia": 65.0}

    encroached_countries = []
    details = []

    for country, dist_km in border_dists.items():
        if max_contour_distance_km > dist_km:
            overflow_km = round(max_contour_distance_km - dist_km, 1)
            encroached_countries.append(country.upper())
            details.append({
                "country": country.upper(),
                "dist_to_border_km": dist_km,
                "contour_reach_km": max_contour_distance_km,
                "overflow_km": overflow_km,
                "regulatory_action": f"Bắt buộc phối hợp tần số với {country.upper()} theo RR No. 9.17"
            })

    requires_coordination = len(encroached_countries) > 0

    return {
        "station_name": station_name,
        "lat": lat_deg,
        "lon": lon_deg,
        "max_contour_distance_km": max_contour_distance_km,
        "requires_international_coordination": requires_coordination,
        "affected_administrations": encroached_countries,
        "itu_articles": ["RR No. 9.17", "RR No. 9.18", "RR Appendix 7"],
        "coordination_details": details,
        "summary": (
            f"Vùng phối hợp vượt qua biên giới {', '.join(encroached_countries)}. Cần gửi thông báo phối hợp quốc tế."
            if requires_coordination else
            "Vùng phối hợp nằm hoàn toàn trong lãnh thổ/lãnh hải Việt Nam. Không cần thủ tục phối hợp biên giới."
        )
    }


def evaluate_vietnam_stations_appendix7(
    freq_ghz: float = 28.5,
    eirp_density_dbw_per_mhz: float = 48.0,
    beam_azimuth_deg: float = 180.0,
    beam_elev_deg: float = 25.0,
) -> dict:
    """Thực hiện đánh giá toàn diện Phụ lục 7 cho 7 đài trái đất và Gateway đại diện tại Việt Nam."""
    params = load_appendix7_params()
    st_dict = params.get("vietnam_stations", {})

    station_results = []
    for key, data in st_dict.items():
        lat = float(data["lat"])
        lon = float(data["lon"])
        name = data.get("name", key)

        contour = calculate_coordination_contour(
            lat_deg=lat,
            lon_deg=lon,
            freq_ghz=freq_ghz,
            eirp_density_dbw_per_mhz=eirp_density_dbw_per_mhz,
            beam_azimuth_deg=beam_azimuth_deg,
            beam_elev_deg=beam_elev_deg
        )

        border_check = check_cross_border_encroachment(
            station_name=name,
            lat_deg=lat,
            lon_deg=lon,
            max_contour_distance_km=contour["max_distance_km"],
            station_key=key
        )

        station_results.append({
            "key": key,
            "name": name,
            "type": data.get("type", "ground_station"),
            "lat": lat,
            "lon": lon,
            "elev_m": data.get("elev_m", 15.0),
            "max_distance_km": contour["max_distance_km"],
            "min_distance_km": contour["min_distance_km"],
            "area_sq_km": contour["area_sq_km"],
            "requires_coordination": border_check["requires_international_coordination"],
            "affected_administrations": border_check["affected_administrations"],
            "contour": contour,
            "border_check": border_check
        })

    coexistence_5g = evaluate_coexistence_5g_fs(
        freq_ghz=freq_ghz,
        gateway_eirp_dbw_per_mhz=eirp_density_dbw_per_mhz
    )

    return {
        "standard": "ITU Radio Regulations Appendix 7 & Rec. ITU-R P.620-7",
        "benchmark_tool": "ITU AP7Capture v10.0",
        "freq_ghz": freq_ghz,
        "eirp_density_dbw_per_mhz": eirp_density_dbw_per_mhz,
        "beam_azimuth_deg": beam_azimuth_deg,
        "beam_elev_deg": beam_elev_deg,
        "total_stations_evaluated": len(station_results),
        "stations": station_results,
        "coexistence_5g_fs": coexistence_5g,
    }
