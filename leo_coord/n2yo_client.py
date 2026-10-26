"""Module tích hợp N2YO REST API cho LEO-COORD.

Cung cấp các chức năng giám sát vệ tinh thực địa:
- Tra cứu TLE (Two-Line Element) mới nhất từ danh mục NORAD/Space-Track.
- Lấy tọa độ thực tế (vĩ độ, kinh độ, cao độ, phương vị, góc ngẩng) theo thời gian thực.
- Quét các vệ tinh đang bay qua không phận trạm mặt đất Việt Nam (Hà Nội, Đà Nẵng, TP.HCM).
- Dự báo lịch liên lạc vô tuyến (Radio Passes) cho các vệ tinh quan tâm.
- Tích hợp bộ nhớ đệm (Caching) theo TTL để bảo toàn hạn ngạch Rate Limit của API Key.
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from leo_coord.config import load_config

# Trạm mặt đất trọng điểm Việt Nam
VIETNAM_GROUND_STATIONS = {
    "hanoi": {
        "id": "hanoi",
        "name": "Trạm Hà Nội",
        "lat": 21.0285,
        "lng": 105.8542,
        "alt_m": 15.0,
        "region": "Miền Bắc",
        "color": "#38bdf8"
    },
    "danang": {
        "id": "danang",
        "name": "Trạm Đà Nẵng",
        "lat": 16.0544,
        "lng": 108.2022,
        "alt_m": 10.0,
        "region": "Miền Trung",
        "color": "#34d399"
    },
    "hcmc": {
        "id": "hcmc",
        "name": "Trạm TP.HCM",
        "lat": 10.8231,
        "lng": 106.6297,
        "alt_m": 12.0,
        "region": "Miền Nam",
        "color": "#fbbf24"
    },
    "viettri": {
        "id": "viettri",
        "name": "Trạm Việt Trì",
        "lat": 21.3283,
        "lng": 105.3566,
        "alt_m": 20.0,
        "region": "Phú Thọ / Miền Bắc",
        "color": "#a855f7"
    },
    "bacninh": {
        "id": "bacninh",
        "name": "Trạm Bắc Ninh",
        "lat": 21.136356,
        "lng": 106.074508,
        "alt_m": 15.0,
        "region": "Bắc Ninh / Miền Bắc",
        "color": "#ec4899"
    }
}

# Cache trong bộ nhớ {cache_key: (timestamp, data)}
_CACHE: Dict[str, tuple[float, Any]] = {}


class N2YOClient:
    """Client giao tiếp với N2YO REST API v1."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.timeout = timeout
        cfg = {}
        try:
            cfg = load_config().get("n2yo", {})
        except Exception:
            pass

        self.api_key = (
            api_key
            or os.getenv("N2YO_API_KEY")
            or cfg.get("api_key", "5XSJVZ-WE8V38-D5V3WP-5VDA")
        )
        self.base_url = cfg.get("base_url", "https://api.n2yo.com/rest/v1/satellite")
        self.ttl_positions = cfg.get("cache_ttl_positions_s", 30)
        self.ttl_tle = cfg.get("cache_ttl_tle_s", 3600)

    def _get_from_cache(self, key: str, ttl: float) -> Optional[Any]:
        if key in _CACHE:
            ts, val = _CACHE[key]
            if time.time() - ts < ttl:
                return val
            del _CACHE[key]
        return None

    def _set_cache(self, key: str, val: Any) -> None:
        _CACHE[key] = (time.time(), val)

    def _request(self, endpoint_path: str, cache_ttl: Optional[float] = None) -> Dict[str, Any]:
        """Thực hiện HTTP GET tới N2YO API kèm quản lý cache."""
        cache_key = f"n2yo:{endpoint_path}"
        if cache_ttl and cache_ttl > 0:
            cached = self._get_from_cache(cache_key, cache_ttl)
            if cached is not None:
                return cached

        # N2YO format: path&apiKey=...
        sep = "&" if "?" not in endpoint_path else "&"
        url = f"{self.base_url}/{endpoint_path}{sep}apiKey={self.api_key}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "LEO-COORD-MissionControl/1.0",
                "Accept": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e), "status": "failed"}

        if isinstance(data, dict) and "error" in data:
            return data

        if cache_ttl and cache_ttl > 0:
            self._set_cache(cache_key, data)

        return data

    def get_tle(self, norad_id: int) -> Dict[str, Any]:
        """Lấy bộ phần tử quỹ đạo 2 dòng (TLE) của vệ tinh theo mã NORAD ID."""
        return self._request(f"tle/{norad_id}", cache_ttl=self.ttl_tle)

    def get_positions(
        self,
        norad_id: int,
        observer_lat: float,
        observer_lng: float,
        observer_alt: float = 0.0,
        seconds: int = 1
    ) -> Dict[str, Any]:
        """Lấy tọa độ vệ tinh và góc phương vị/ngẩng so với vị trí quan sát."""
        sec = max(1, min(int(seconds), 300))
        path = f"positions/{norad_id}/{observer_lat:.4f}/{observer_lng:.4f}/{observer_alt:.1f}/{sec}"
        return self._request(path, cache_ttl=self.ttl_positions)

    def get_satellites_above(
        self,
        observer_lat: float,
        observer_lng: float,
        observer_alt: float = 0.0,
        search_radius_deg: float = 45.0,
        category_id: int = 0
    ) -> Dict[str, Any]:
        """Quét danh sách các vệ tinh đang bay qua trên đầu vị trí quan sát."""
        radius = max(1.0, min(float(search_radius_deg), 90.0))
        cat = int(category_id)
        path = f"above/{observer_lat:.4f}/{observer_lng:.4f}/{observer_alt:.1f}/{radius:.0f}/{cat}"
        # Cache kết quả quét 60s
        return self._request(path, cache_ttl=60.0)

    def get_radio_passes(
        self,
        norad_id: int,
        observer_lat: float,
        observer_lng: float,
        observer_alt: float = 0.0,
        days: int = 2,
        min_elevation: int = 10
    ) -> Dict[str, Any]:
        """Dự báo lịch thu phát sóng vô tuyến (Radio Passes) qua trạm."""
        d = max(1, min(int(days), 10))
        el = max(0, min(int(min_elevation), 90))
        path = f"radiopasses/{norad_id}/{observer_lat:.4f}/{observer_lng:.4f}/{observer_alt:.1f}/{d}/{el}"
        # Radio passes ít thay đổi trong 1 giờ, cache 1800s để bảo vệ quota 100 req/ngày
        return self._request(path, cache_ttl=1800.0)


def get_default_tracked_satellites() -> List[Dict[str, Any]]:
    """Lấy danh sách các vệ tinh trọng điểm đã định cấu hình."""
    cfg = {}
    try:
        cfg = load_config().get("n2yo", {})
    except Exception:
        pass

    default_list = [
        {"norad_id": 32767, "name": "VINASAT-1", "category": "GSO", "band": "C/Ku", "operator": "VNPT (Việt Nam)", "role": "Viễn thông Quốc gia"},
        {"norad_id": 38332, "name": "VINASAT-2", "category": "GSO", "band": "C/Ku", "operator": "VNPT (Việt Nam)", "role": "Viễn thông Quốc gia"},
        {"norad_id": 39160, "name": "VNREDSAT-1", "category": "LEO", "band": "X/S", "operator": "VAST (Việt Nam)", "role": "Quan sát Trái đất"},
        {"norad_id": 25544, "name": "ISS (Trạm Vũ trụ)", "category": "LEO", "band": "VHF/UHF/Ku", "operator": "NASA/Roscosmos", "role": "Trạm nghiên cứu"},
        {"norad_id": 44714, "name": "STARLINK-1008", "category": "LEO", "band": "Ku/Ka", "operator": "SpaceX", "role": "Chòm sao Băng rộng LEO"},
        {"norad_id": 44057, "name": "ONEWEB-0012", "category": "LEO", "band": "Ku/Ka", "operator": "Eutelsat OneWeb", "role": "Chòm sao Băng rộng LEO"},
    ]
    return cfg.get("tracked_satellites", default_list)


def evaluate_satellite_live(norad_id: int, client: Optional[N2YOClient] = None) -> Dict[str, Any]:
    """Tổng hợp phân tích trực tiếp một vệ tinh so với 3 trạm mặt đất Việt Nam.

    Tính toán:
    - Vị trí thực tế thời gian thực (lat, lon, alt).
    - Góc ngẩng (elevation) và góc phương vị (azimuth) tới Hà Nội, Đà Nẵng, TP.HCM.
    - Cự ly xiên Slant Range (km) tới trạm gần nhất.
    - Trạng thái vùng phủ (In-view / Out-of-view, ngưỡng tối thiểu 10 độ).
    - Cảnh báo can nhiễu cung Vinasat GSO +-6 độ nếu vệ tinh LEO có vị trí nhạy cảm.
    """
    c = client or N2YOClient()

    # Lấy vị trí tham chiếu trạm Đà Nẵng làm trung tâm Việt Nam
    dn = VIETNAM_GROUND_STATIONS["danang"]
    pos_res = c.get_positions(norad_id, dn["lat"], dn["lng"], dn["alt_m"], seconds=1)

    if not pos_res or "error" in pos_res or not pos_res.get("positions"):
        msg = pos_res.get("error") if pos_res else None
        if not msg:
            sat_name = (pos_res.get("info", {}) or {}).get("satname") if pos_res else None
            if sat_name:
                msg = f"Vệ tinh '{sat_name}' (NORAD {norad_id}) hiện không còn dữ liệu quỹ đạo trên NORAD/N2YO (vệ tinh này đã giải quỹ đạo, ngừng hoạt động hoặc đã bốc cháy trong khí quyển - Deorbited)."
            else:
                msg = f"Không tìm thấy dữ liệu vị trí cho vệ tinh NORAD ID {norad_id} từ N2YO."
        return {
            "norad_id": norad_id,
            "status": "error",
            "message": msg
        }

    sat_info = pos_res.get("info", {})
    pos = pos_res["positions"][0]

    sat_lat = pos["satlatitude"]
    sat_lng = pos["satlongitude"]
    sat_alt = pos["sataltitude"]
    eclipsed = pos.get("eclipsed", False)

    # Tính toán góc ngẩng và cự ly xiên tới 3 trạm mặt đất Việt Nam
    stations_analysis = []
    max_elevation = -90.0
    nearest_station = None
    min_slant_km = 999999.0

    R_EARTH = 6371.0  # Bán kính Trái Đất (km)

    for st_id, st in VIETNAM_GROUND_STATIONS.items():
        # Gọi N2YO tính góc cho trạm này nếu cần hoặc tính hình học
        # Để tiết kiệm quota, tính hình học cự ly Slant range và góc ngẩng
        d_lat = math.radians(sat_lat - st["lat"])
        d_lon = math.radians(sat_lng - st["lng"])
        lat1 = math.radians(st["lat"])
        lat2 = math.radians(sat_lat)

        # Great-circle central angle (rad)
        haversine = math.sin(d_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2)**2
        central_angle = 2 * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))

        # Slant range law of cosines
        # d^2 = R^2 + (R+h)^2 - 2*R*(R+h)*cos(gamma)
        r1 = R_EARTH
        r2 = R_EARTH + sat_alt
        slant_km = math.sqrt(max(0.0, r1**2 + r2**2 - 2 * r1 * r2 * math.cos(central_angle)))

        # Elevation angle: cos(el) = (r2 / slant) * sin(central_angle)
        # hoặc sin(el) = (r2 * cos(central_angle) - r1) / slant
        sin_el = (r2 * math.cos(central_angle) - r1) / max(1.0, slant_km)
        elevation_deg = math.degrees(math.asin(min(1.0, max(-1.0, sin_el))))

        is_visible = elevation_deg >= 10.0  # Ngưỡng quy chuẩn tối thiểu 10 độ

        stations_analysis.append({
            "station_id": st_id,
            "station_name": st["name"],
            "region": st["region"],
            "elevation_deg": round(elevation_deg, 2),
            "slant_range_km": round(slant_km, 1),
            "is_visible": is_visible
        })

        if elevation_deg > max_elevation:
            max_elevation = elevation_deg
            nearest_station = st["name"]
            min_slant_km = slant_km

    # Đánh giá loại quỹ đạo
    orbit_type = "LEO"
    if sat_alt > 30000:
        orbit_type = "GSO"
    elif sat_alt > 2000:
        orbit_type = "MEO"

    # Kiểm tra cảnh báo can nhiễu cung GSO Vinasat (131.8 - 132 độ E +- 6 độ = 125.8° đến 138°)
    gso_warning = False
    if orbit_type == "GSO" and 125.8 <= sat_lng <= 138.0:
        gso_warning = True

    return {
        "norad_id": norad_id,
        "satname": sat_info.get("satname", f"SAT-{norad_id}"),
        "orbit_type": orbit_type,
        "satlatitude": round(sat_lat, 4),
        "satlongitude": round(sat_lng, 4),
        "sataltitude_km": round(sat_alt, 1),
        "eclipsed": eclipsed,
        "max_elevation_deg": round(max_elevation, 2),
        "nearest_station": nearest_station,
        "min_slant_range_km": round(min_slant_km, 1),
        "has_coverage_vietnam": max_elevation >= 10.0,
        "gso_coordination_zone": gso_warning,
        "stations": stations_analysis,
        "timestamp": pos.get("timestamp", int(time.time()))
    }


def calculate_look_angles(
    obs_lat: float,
    obs_lng: float,
    obs_alt_m: float,
    sat_lat: float,
    sat_lng: float,
    sat_alt_km: float
) -> tuple[float, float, float, str]:
    """Tính góc ngẩng (elevation_deg), góc phương vị (azimuth_deg), cự ly nghiêng (slant_range_km)

    và hướng la bàn (compass_str) từ trạm mặt đất tới vệ tinh theo hệ quy chiếu Topocentric ENU.
    """
    R_EARTH = 6371.0  # km
    r_obs = R_EARTH + (float(obs_alt_m or 0.0) / 1000.0)
    phi1 = math.radians(float(obs_lat))
    lam1 = math.radians(float(obs_lng))
    x1 = r_obs * math.cos(phi1) * math.cos(lam1)
    y1 = r_obs * math.cos(phi1) * math.sin(lam1)
    z1 = r_obs * math.sin(phi1)

    r_sat = R_EARTH + float(sat_alt_km)
    phi2 = math.radians(float(sat_lat))
    lam2 = math.radians(float(sat_lng))
    x2 = r_sat * math.cos(phi2) * math.cos(lam2)
    y2 = r_sat * math.cos(phi2) * math.sin(lam2)
    z2 = r_sat * math.sin(phi2)

    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1

    # Chuyển đổi sang hệ trục địa phương ENU (East, North, Up) tại trạm quan sát
    east = -math.sin(lam1) * dx + math.cos(lam1) * dy
    north = -math.sin(phi1) * math.cos(lam1) * dx - math.sin(phi1) * math.sin(lam1) * dy + math.cos(phi1) * dz
    up = math.cos(phi1) * math.cos(lam1) * dx + math.cos(phi1) * math.sin(lam1) * dy + math.sin(phi1) * dz

    slant_km = math.sqrt(east * east + north * north + up * up)
    sin_el = max(-1.0, min(1.0, up / max(0.001, slant_km)))
    el_deg = math.degrees(math.asin(sin_el))
    az_deg = (math.degrees(math.atan2(east, north)) + 360.0) % 360.0

    compass_idx = round(az_deg / 45.0) % 8
    compass_names = [
        "B (N)",
        "ĐB (NE)",
        "Đ (E)",
        "ĐN (SE)",
        "N (S)",
        "TN (SW)",
        "T (W)",
        "TB (NW)"
    ]
    compass_str = compass_names[compass_idx]

    return round(el_deg, 2), round(az_deg, 2), round(slant_km, 1), compass_str


def get_satellite_orbit_track(
    norad_id: int,
    client: Optional[N2YOClient] = None,
    n_steps: int = 90
) -> Dict[str, Any]:
    """Tính toán quỹ đạo 3D toàn phần (Full Orbit Track) của vệ tinh thực tế.

    Sử dụng SGP4 nếu có TLE từ N2YO/NORAD để lan truyền chính xác trong 1 chu kỳ bay.
    Nếu không có TLE, tự động suy diễn mô hình quỹ đạo tròn nghiêng (Analytical Keplerian Orbit).
    Trả về danh sách các điểm tọa độ (lat, lon, alt_km, time) và thông số quỹ đạo.
    """
    from leo_coord.orbits import MU, R_EARTH, OMEGA_EARTH

    c = client or N2YOClient()
    now = time.time()

    # 1. Thử lấy TLE từ N2YO/NORAD
    tle_res = c.get_tle(norad_id)
    sat_name = f"SAT-{norad_id}"
    if isinstance(tle_res, dict) and "info" in tle_res:
        sat_name = tle_res["info"].get("satname", sat_name)

    tle_str = tle_res.get("tle", "") if isinstance(tle_res, dict) else ""
    tle_lines = [line.strip() for line in tle_str.strip().splitlines() if line.strip()]

    # Kiểm tra xem có 2 dòng TLE hợp lệ không
    if len(tle_lines) >= 2:
        try:
            from sgp4.api import Satrec, jday
            from leo_coord.orbits import eci_to_ecef, subpoint

            l1 = tle_lines[0] if tle_lines[0].startswith("1 ") else tle_lines[1]
            l2 = tle_lines[1] if tle_lines[1].startswith("2 ") else (tle_lines[2] if len(tle_lines) > 2 else "")

            if l1.startswith("1 ") and l2.startswith("2 "):
                sat = Satrec.twoline2rv(l1, l2)

                # Tính chu kỳ quỹ đạo (phút)
                mean_motion_rad_min = sat.no_kozai
                period_min = (2.0 * math.pi) / max(1e-6, mean_motion_rad_min)
                inc_deg = math.degrees(sat.inclo)
                ecc = sat.ecco

                # Tính cao độ cực cận và cực viễn xấp xỉ
                semi_major_km = (MU / ((mean_motion_rad_min / 60.0) ** 2)) ** (1.0 / 3.0)
                perigee_km = semi_major_km * (1.0 - ecc) - R_EARTH
                apogee_km = semi_major_km * (1.0 + ecc) - R_EARTH

                # Lan truyền SGP4 dọc theo 1 chu kỳ hoàn chỉnh
                jd0, _ = jday(1970, 1, 1, 0, 0, 0.0)
                step_s = (period_min * 60.0) / max(30, n_steps)
                points = []

                for i in range(n_steps + 1):
                    t_sec = now + i * step_s
                    jd = jd0 + t_sec / 86400.0
                    e, r, _ = sat.sgp4(jd, 0.0)
                    if e == 0:
                        ecef = eci_to_ecef(r, t_sec)
                        lat, lon, alt = subpoint(ecef)
                        points.append({
                            "lat": round(float(lat), 3),
                            "lon": round(float(lon), 3),
                            "alt_km": round(float(alt), 1),
                            "t_sec": int(t_sec)
                        })

                if len(points) >= 20:
                    return {
                        "status": "success",
                        "norad_id": norad_id,
                        "satname": sat_name,
                        "method": "SGP4_TLE",
                        "period_min": round(period_min, 1),
                        "inclination_deg": round(inc_deg, 2),
                        "apogee_km": round(max(0.0, apogee_km), 1),
                        "perigee_km": round(max(0.0, perigee_km), 1),
                        "eccentricity": round(ecc, 5),
                        "points_count": len(points),
                        "points": points
                    }
        except Exception:
            pass

    # 2. Phương án dự phòng: Mô hình quỹ đạo giải tích (Keplerian Analytic Orbit)
    live_eval = evaluate_satellite_live(norad_id, client=c)
    sat_lat = float(live_eval.get("satlatitude", 16.0))
    sat_lon = float(live_eval.get("satlongitude", 108.0))
    sat_alt = float(live_eval.get("sataltitude_km", 550.0))
    sat_name = live_eval.get("satname", sat_name)

    is_gso = sat_alt > 30000.0
    if is_gso:
        points = []
        for l in range(-180, 181, 4):
            points.append({
                "lat": 0.0,
                "lon": float(l),
                "alt_km": round(sat_alt, 1),
                "t_sec": int(now)
            })
        return {
            "status": "success",
            "norad_id": norad_id,
            "satname": sat_name,
            "method": "GSO_CIRCULAR",
            "period_min": 1436.1,
            "inclination_deg": 0.0,
            "apogee_km": round(sat_alt, 1),
            "perigee_km": round(sat_alt, 1),
            "eccentricity": 0.0,
            "points_count": len(points),
            "points": points
        }

    # LEO/MEO Analytic Orbit
    a = R_EARTH + sat_alt
    n = math.sqrt(MU / (a ** 3))
    period_min = (2.0 * math.pi / n) / 60.0
    inc_deg = max(abs(sat_lat) + 2.0, 51.6 if abs(sat_lat) < 51.0 else 97.5)
    inc_rad = math.radians(inc_deg)

    sin_u = max(-1.0, min(1.0, math.sin(math.radians(sat_lat)) / max(0.01, math.sin(inc_rad))))
    u0 = math.asin(sin_u)
    raan_rad = math.radians(sat_lon) - math.atan2(math.cos(inc_rad) * math.sin(u0), math.cos(u0))

    points = []
    step_s = (period_min * 60.0) / max(30, n_steps)
    for i in range(n_steps + 1):
        t_sec = now + i * step_s
        u = u0 + n * (i * step_s)
        xp = a * math.cos(u)
        yp = a * math.sin(u)
        ci, si = math.cos(inc_rad), math.sin(inc_rad)
        cr, sr = math.cos(raan_rad), math.sin(raan_rad)
        x_eci = xp * cr - yp * ci * sr
        y_eci = xp * sr + yp * ci * cr
        z_eci = yp * si

        theta_earth = OMEGA_EARTH * (i * step_s)
        x_ecef = x_eci * math.cos(theta_earth) + y_eci * math.sin(theta_earth)
        y_ecef = -x_eci * math.sin(theta_earth) + y_eci * math.cos(theta_earth)
        z_ecef = z_eci

        r_norm = math.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)
        pt_lat = math.degrees(math.asin(max(-1.0, min(1.0, z_ecef / r_norm))))
        pt_lon = math.degrees(math.atan2(y_ecef, x_ecef))

        points.append({
            "lat": round(pt_lat, 3),
            "lon": round(pt_lon, 3),
            "alt_km": round(sat_alt, 1),
            "t_sec": int(t_sec)
        })

    return {
        "status": "success",
        "norad_id": norad_id,
        "satname": sat_name,
        "method": "ANALYTIC_KEPLERIAN",
        "period_min": round(period_min, 1),
        "inclination_deg": round(inc_deg, 2),
        "apogee_km": round(sat_alt, 1),
        "perigee_km": round(sat_alt, 1),
        "eccentricity": 0.0,
        "points_count": len(points),
        "points": points
    }

