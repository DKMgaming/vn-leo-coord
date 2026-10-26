"""Backend FastAPI cho Web App LEO-COORD.
Hỗ trợ 2 Tab chính:
- Tab 1: Bản đồ 3D vệ tinh & Các chức năng kỹ thuật phân tích chòm sao LEO
- Tab 2: Quản lý & tải lên tài liệu/tham luận (Word, Excel, PDF, PPTX)
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yaml

from leo_coord.config import load_config
from leo_coord.orbits import WalkerConstellation
from leo_coord.coverage import coverage_grid, point_stats, footprint_radius_km
from leo_coord.pfd import check_downlink_pfd
from leo_coord.epfd import single_entry_epfd_down
from leo_coord.coordination import screen_ngso_vs_gso
from leo_coord.milestones import res35_schedule, evaluate, warehousing_flag
from leo_coord.report import build_html
from leo_coord import database as db
from leo_coord.n2yo_client import (
    N2YOClient,
    get_default_tracked_satellites,
    evaluate_satellite_live,
    VIETNAM_GROUND_STATIONS,
    calculate_look_angles,
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
METADATA_FILE = UPLOAD_DIR / "documents.json"
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR.parent / "out"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="LEO-COORD Mission Control",
    description="Hệ thống quản lý tần số, quỹ đạo chòm sao vệ tinh LEO & Kho tư liệu tham luận",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_documents_meta() -> List[dict]:
    if not METADATA_FILE.exists():
        # Tạo dữ liệu mẫu ban đầu
        initial = [
            {
                "id": "doc-01",
                "title": "Báo cáo Chiến lược Quản lý Tần số và Quỹ đạo Chòm sao LEO tại Việt Nam",
                "author": "Cục Tần số Vô tuyến điện - Ban Công nghệ Vũ trụ",
                "category": "Chiến lược & Chính sách",
                "file_type": "pdf",
                "filename": "chien_luoc_leo_vietnam.pdf",
                "original_filename": "Chien_luoc_LEO_VietNam_2026.pdf",
                "file_size": 2450000,
                "upload_date": "2026-10-15 09:30",
                "summary": "Tổng hợp kinh nghiệm quốc tế (FCC, ITU, Ofcom) và đề xuất lộ trình phối hợp, cấp phép băng tần Ku/Ka cho các chòm sao Starlink, OneWeb tại Việt Nam."
            },
            {
                "id": "doc-02",
                "title": "Bảng tính toán Mô hình Can nhiễu PFD và EPFD giữa NGSO và GSO (Băng Ku/Ka)",
                "author": "Phòng Kỹ thuật & Tiêu chuẩn Phổ tần",
                "category": "Kỹ thuật & Tính toán",
                "file_type": "xlsx",
                "filename": "tinh_toan_pfd_epfd_mau.xlsx",
                "original_filename": "Mo_hinh_PFD_EPFD_Article21_22.xlsx",
                "file_size": 890000,
                "upload_date": "2026-10-17 14:15",
                "summary": "Bảng tính chi tiết tham số quỹ đạo 120 vệ tinh, tính toán góc phân tách địa tĩnh, ngưỡng suy giảm PFD và xác suất bảo vệ vệ tinh Vinasat-1/2."
            },
            {
                "id": "doc-03",
                "title": "Tham luận: Cơ chế Chống Xí phần Tần số theo Nghị quyết ITU Res 35 (WRC-19)",
                "author": "ThS. Nguyễn Văn An - Chuyên gia Phối hợp Tần số Quốc tế",
                "category": "Quy định Quốc tế (ITU)",
                "file_type": "docx",
                "filename": "nghi_quyet_res35_wrc19.docx",
                "original_filename": "Tham_luan_Res35_WRC19_ITU.docx",
                "file_size": 1250000,
                "upload_date": "2026-10-18 10:00",
                "summary": "Đánh giá các mốc kiểm tra triển khai vệ tinh (10% sau 2 năm, 50% sau 5 năm, 100% sau 7 năm) và biện pháp giám sát thực tế bằng radar/TLE."
            },
            {
                "id": "doc-04",
                "title": "Slide Báo cáo Hội nghị: Xu hướng Phát triển Chòm sao Vệ tinh Tầm thấp Toàn cầu",
                "author": "Viện Công nghệ Không gian & Viễn thông",
                "category": "Thuyết trình & Hội thảo",
                "file_type": "pptx",
                "filename": "slide_chom_sao_leo_hoi_nghi.pptx",
                "original_filename": "Presentation_LEO_Constellations_2026.pptx",
                "file_size": 5600000,
                "upload_date": "2026-10-19 16:20",
                "summary": "Bài trình bày tổng quan cấu trúc mạng Walker Star/Delta, kết nối liên vệ tinh ISL băng quang học và xu hướng Direct-to-Cell trên smartphone."
            }
        ]
        METADATA_FILE.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")
        # Tạo file mẫu giả lập trong thư mục uploads
        for item in initial:
            sample_file = UPLOAD_DIR / item["filename"]
            if not sample_file.exists():
                sample_file.write_text(f"Nội dung mẫu của tài liệu: {item['title']}\nTác giả: {item['author']}\n", encoding="utf-8")
        return initial

    try:
        return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_documents_meta(docs: List[dict]):
    METADATA_FILE.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/constellation/default")
def get_default_constellation():
    """Lấy thông số chòm sao mặc định từ file YAML."""
    demo_file = DATA_DIR / "demo" / "constellation_demo.yaml"
    if demo_file.exists():
        spec = yaml.safe_load(demo_file.read_text(encoding="utf-8"))
        return spec
    return {
        "name": "DEMO_LEO_KU",
        "alt_km": 550.0,
        "inc_deg": 53.0,
        "n_sats": 120,
        "n_planes": 6,
        "phasing": 1,
        "kind": "delta",
        "downlink": {"band_ghz": "10.7-12.7", "freq_ghz": 11.7, "eirp_dbw_per_mhz": 10.0}
    }


@app.post("/api/assess")
def run_assessment(payload: dict):
    """Thực hiện đánh giá toàn diện chòm sao và trả về kết quả JSON."""
    from leo_coord.cli import build_assessment
    cfg = load_config()
    alt_km = float(payload.get("alt_km", 550.0))
    inc_deg = float(payload.get("inc_deg", 53.0))
    n_sats = int(payload.get("n_sats", 120))
    n_planes = int(payload.get("n_planes", 6))
    kind = payload.get("kind", "delta")
    phasing = int(payload.get("phasing", 1))
    name = payload.get("name", "LEO_ASSESSMENT")

    freq_ghz = float(payload.get("freq_ghz", 11.7))
    eirp = float(payload.get("eirp_dbw_per_mhz", 10.0))
    gso_lon = float(payload.get("gso_lon", 105.5))
    dish_d_m = float(payload.get("dish_d_m", 1.2))

    w = WalkerConstellation(name, alt_km, inc_deg, n_sats, n_planes, phasing, kind)
    spec = {
        "name": name,
        "alt_km": alt_km,
        "inc_deg": inc_deg,
        "n_sats": n_sats,
        "n_planes": n_planes,
        "kind": kind,
        "phasing": phasing,
        "downlink": {
            "band_ghz": f"{freq_ghz-1.0:.1f}-{freq_ghz+1.0:.1f}",
            "freq_ghz": freq_ghz,
            "eirp_dbw_per_mhz": eirp
        }
    }
    biu_str = payload.get("biu_deadline", "2024-03-01")
    biu = date.fromisoformat(biu_str) if biu_str else date(2024, 3, 1)
    deps = [
        (date(2025, 6, 1), max(1, int(n_sats * 0.12))),
        (date(2028, 12, 1), max(1, int(n_sats * 0.49)))
    ]

    a = build_assessment(w, spec, cfg, gso_lon=gso_lon, biu_deadline=biu,
                         deployments=deps, dish_d_m=dish_d_m)

    # Sinh và ghi báo cáo HTML
    try:
        html = build_html(a)
        out = BASE_DIR.parent / "out" / "bao_cao.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
    except Exception as e:
        print("Lỗi ghi báo cáo HTML:", e)

    a["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return a


@app.get("/api/orbits/state")
def get_orbit_state(alt_km: float = 550.0, inc_deg: float = 53.0, n_sats: int = 120,
                    n_planes: int = 6, phasing: int = 1, kind: str = "delta",
                    sim_time_sec: float = 0.0):
    """Tính toán vị trí 3D chính xác của toàn bộ vệ tinh và đường bay cho bản đồ số 3D."""
    from leo_coord.orbits import subpoint
    import numpy as np

    w = WalkerConstellation("SIM", alt_km, inc_deg, n_sats, n_planes, phasing, kind)
    period_s = w.period_s

    # Lấy vị trí ECEF tại thời điểm sim_time_sec
    ecef = w.ecef_positions(sim_time_sec)[0]  # shape (S, 3)
    lats, lons, alts = subpoint(ecef)

    satellites = []
    base, extra = divmod(n_sats, n_planes)
    idx = 0
    for p in range(n_planes):
        count = base + (1 if p < extra else 0)
        for s in range(count):
            satellites.append({
                "id": f"SAT-P{p+1}-{s+1:02d}",
                "plane": p + 1,
                "sat_in_plane": s + 1,
                "lat": round(float(lats[idx]), 2),
                "lon": round(float(lons[idx]), 2),
                "alt_km": round(float(alts[idx]), 1),
            })
            idx += 1

    # Tính đường cong quỹ đạo (sample points cho từng mặt phẳng)
    orbit_planes = []
    spread = 360.0 if kind == "delta" else 180.0
    for p_idx in range(n_planes):
        raan = np.radians(p_idx * spread / n_planes)
        points = []
        inc_rad = np.radians(inc_deg)
        for theta in np.linspace(0, 2 * np.pi, 60):
            x_orb = np.cos(theta)
            y_orb = np.sin(theta)
            x = x_orb * np.cos(raan) - y_orb * np.cos(inc_rad) * np.sin(raan)
            y = x_orb * np.sin(raan) + y_orb * np.cos(inc_rad) * np.cos(raan)
            z = y_orb * np.sin(inc_rad)
            points.append([round(float(x), 4), round(float(z), 4), round(float(y), 4)])
        orbit_planes.append({
            "plane_index": p_idx + 1,
            "raan_deg": round(float(np.degrees(raan)), 1),
            "points": points
        })

    ref_points = [
        {"name": "Hà Nội (Trạm Bắc)", "lat": 21.03, "lon": 105.85, "color": "#38bdf8"},
        {"name": "Đà Nẵng (Trạm Trung)", "lat": 16.05, "lon": 108.20, "color": "#34d399"},
        {"name": "TP. Hồ Chí Minh (Trạm Nam)", "lat": 10.82, "lon": 106.63, "color": "#fbbf24"},
        {"name": "Việt Trì (Trạm Phú Thọ)", "lat": 21.33, "lon": 105.36, "color": "#a855f7"},
        {"name": "Bắc Ninh (Trạm Kinh Bắc)", "lat": 21.14, "lon": 106.07, "color": "#ec4899"}
    ]

    return {
        "period_s": round(period_s, 1),
        "sim_time_sec": round(sim_time_sec, 1),
        "satellites": satellites,
        "orbit_planes": orbit_planes,
        "ref_points": ref_points,
        "footprint_radius_km": round(footprint_radius_km(alt_km, 10.0), 1)
    }


# ================= ITU GIBC BENCHMARK & ANTENNA PATTERNS (PHASE 1) =================

@app.get("/api/benchmark/gibc")
def get_gibc_benchmark():
    """Lấy kết quả đối chuẩn kỹ thuật giữa LEO-COORD và phần mềm ITU GIBC v10.0."""
    from leo_coord.reference import reference_dir
    from leo_coord.pfd import benchmark_against_gibc
    import yaml

    bench_file = reference_dir() / "itu_gibc_benchmarks.yaml"
    if not bench_file.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp đối chuẩn itu_gibc_benchmarks.yaml")
    
    raw = yaml.safe_load(bench_file.read_text(encoding="utf-8"))
    results = []
    tol = raw.get("benchmark_metadata", {}).get("tolerance_db", 0.05)
    
    for tv in raw.get("test_vectors", []):
        evaluated = benchmark_against_gibc(tv, tolerance_db=tol)
        results.append({
            "id": tv.get("id"),
            "name": tv.get("name"),
            "operator": tv.get("operator"),
            "category": tv.get("category"),
            "itu_filing_ref": tv.get("itu_filing_ref"),
            "band_range": tv.get("band_range"),
            "freq_ghz": tv.get("freq_ghz"),
            "alt_km": tv.get("alt_km"),
            "n_sats": tv.get("n_sats"),
            "eirp_dbw_per_mhz": tv.get("eirp_dbw_per_mhz"),
            "passed": evaluated["passed"],
            "max_diff_db": evaluated["max_diff_db"],
            "tolerance_db": tol,
            "calc": evaluated["calc"],
            "expected": evaluated["expected"]
        })

    return {
        "metadata": raw.get("benchmark_metadata", {}),
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r["passed"]),
        "results": results
    }


@app.get("/api/antenna/patterns")
def get_antenna_patterns(theta_max_deg: float = 30.0, step_deg: float = 0.2):
    """Tính toán giản đồ búp sóng ăng-ten thực tế theo Khuyến nghị ITU-R S.1428, S.672 và S.580."""
    from leo_coord.antenna import itu_r_s1428_pattern, itu_r_s672_pattern, itu_r_s580_pattern
    import numpy as np

    th = np.arange(0.0, float(theta_max_deg) + float(step_deg) / 2.0, float(step_deg))
    g_s1428 = itu_r_s1428_pattern(th, g_max_dbi=35.0, theta_3db_deg=2.5, l_s_db=20.0)
    g_s672 = itu_r_s672_pattern(th, g_max_dbi=42.0, theta_3db_deg=1.5, l_s_db=20.0)
    g_s580 = itu_r_s580_pattern(th, d_m=1.2, freq_ghz=11.7)

    return {
        "theta_deg": [round(float(x), 2) for x in th],
        "patterns": {
            "s1428_leo_phased_array": {
                "name": "Rec. ITU-R S.1428 (LEO Phased Array)",
                "g_max_dbi": 35.0,
                "hpbw_deg": 2.5,
                "values": [round(float(x), 2) for x in g_s1428]
            },
            "s672_gso_satellite": {
                "name": "Rec. ITU-R S.672 (GSO Vinasat-1/2)",
                "g_max_dbi": 42.0,
                "hpbw_deg": 1.5,
                "values": [round(float(x), 2) for x in g_s672]
            },
            "s580_earth_station": {
                "name": "Rec. ITU-R S.580 (Earth Station Dish 1.2m)",
                "dish_d_m": 1.2,
                "freq_ghz": 11.7,
                "values": [round(float(x), 2) for x in g_s580]
            }
        }
    }


@app.get("/api/antenna/in-line-check")
def check_in_line_event(
    sat_lat: float,
    sat_lon: float,
    sat_alt_km: float = 550.0,
    station: str = "danang",
    gso_lon: float = 132.0,
    eirp_leo: float = 15.0
):
    """Đánh giá nguy cơ can nhiễu thẳng hàng In-line Event với Vinasat từ trạm mặt đất."""
    from leo_coord.antenna import evaluate_in_line_event
    st = VIETNAM_GROUND_STATIONS.get(station.lower(), VIETNAM_GROUND_STATIONS["danang"])
    res = evaluate_in_line_event(
        sat_lat=sat_lat,
        sat_lon=sat_lon,
        sat_alt_km=sat_alt_km,
        gs_lat=st["lat"],
        gs_lon=st["lng"],
        gso_lon_deg=gso_lon,
        eirp_leo_dbw_per_mhz=eirp_leo
    )
    res["station"] = st
    return res


# ================= ITU RR APPENDIX 7 & GATEWAY COORDINATION API =================

@app.get("/api/appendix7/summary")
def get_appendix7_summary(
    freq_ghz: float = 28.5,
    eirp_density: float = 48.0,
    beam_azimuth: float = 180.0,
    beam_elev: float = 25.0
):
    """Lấy dữ liệu thẩm định toàn diện Phụ lục 7 cho 7 đài trái đất và Gateway tại Việt Nam."""
    from leo_coord.appendix7 import evaluate_vietnam_stations_appendix7
    return evaluate_vietnam_stations_appendix7(
        freq_ghz=freq_ghz,
        eirp_density_dbw_per_mhz=eirp_density,
        beam_azimuth_deg=beam_azimuth,
        beam_elev_deg=beam_elev
    )


@app.get("/api/appendix7/contours")
def get_appendix7_contours(
    freq_ghz: float = 28.5,
    eirp_density: float = 48.0
):
    """Lấy danh sách các đường viền phối hợp (Coordination Contours) của các trạm mặt đất."""
    from leo_coord.appendix7 import load_appendix7_params, calculate_coordination_contour
    params = load_appendix7_params()
    st_dict = params.get("vietnam_stations", {})
    results = []
    for key, data in st_dict.items():
        c = calculate_coordination_contour(
            lat_deg=float(data["lat"]),
            lon_deg=float(data["lon"]),
            freq_ghz=freq_ghz,
            eirp_density_dbw_per_mhz=eirp_density,
            step_deg=10.0
        )
        c["key"] = key
        c["name"] = data.get("name", key)
        c["type"] = data.get("type", "ground_station")
        results.append(c)
    return {"stations": results}


@app.post("/api/appendix7/evaluate-gateway")
def evaluate_custom_gateway(payload: dict):
    """Đánh giá vùng phối hợp và khả năng cùng tồn tại 5G cho một trạm Gateway tùy chỉnh."""
    from leo_coord.appendix7 import (
        calculate_coordination_contour,
        evaluate_coexistence_5g_fs,
        check_cross_border_encroachment
    )
    name = str(payload.get("name", "Custom Gateway"))
    lat = float(payload.get("lat", 21.0))
    lon = float(payload.get("lon", 105.8))
    freq_ghz = float(payload.get("freq_ghz", 28.5))
    eirp_density = float(payload.get("eirp_density_dbw_per_mhz", 48.0))
    beam_az = float(payload.get("beam_azimuth_deg", 180.0))
    beam_el = float(payload.get("beam_elev_deg", 25.0))
    clutter_db = float(payload.get("clutter_loss_db", 15.0))

    contour = calculate_coordination_contour(
        lat_deg=lat,
        lon_deg=lon,
        freq_ghz=freq_ghz,
        eirp_density_dbw_per_mhz=eirp_density,
        beam_azimuth_deg=beam_az,
        beam_elev_deg=beam_el,
        clutter_loss_db=clutter_db,
        step_deg=10.0
    )

    border = check_cross_border_encroachment(
        station_name=name,
        lat_deg=lat,
        lon_deg=lon,
        max_contour_distance_km=contour["max_distance_km"]
    )

    coex = evaluate_coexistence_5g_fs(
        freq_ghz=freq_ghz,
        gateway_eirp_dbw_per_mhz=eirp_density
    )

    return {
        "gateway": {
            "name": name,
            "lat": lat,
            "lon": lon,
            "freq_ghz": freq_ghz,
            "eirp_density_dbw_per_mhz": eirp_density,
            "beam_azimuth_deg": beam_az,
            "beam_elev_deg": beam_el,
        },
        "contour": contour,
        "border_encroachment": border,
        "coexistence_5g": coex,
    }


# ================= ITU BR IFIC SCANNER & SPACECOM OBJECTION ASSISTANT (PHASE 3) =================

@app.get("/api/br-ific/scan")
def get_br_ific_scan():
    """Quét dữ liệu công báo quốc tế ITU BR IFIC với bộ lọc 3 lớp bảo vệ Vinasat."""
    from leo_coord.br_ific import scan_br_ific_notices
    return scan_br_ific_notices()


@app.post("/api/br-ific/sync")
def sync_br_ific_endpoint():
    """Kích hoạt đồng bộ công báo BR IFIC mới nhất từ cổng thông tin ITU Space Systems."""
    from leo_coord.br_ific import sync_br_ific_notices_online
    return sync_br_ific_notices_online()


@app.get("/api/spacecom/draft-comment/{notice_id}")
def get_spacecom_draft_comment(notice_id: str):
    """Tạo dự thảo hồ sơ phản đối kỹ thuật theo chuẩn ITU SpaceCom."""
    from leo_coord.spacecom import generate_spacecom_draft
    try:
        return generate_spacecom_draft(notice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/spacecom/download-comment/{notice_id}")
def download_spacecom_comment_xml(notice_id: str):
    """Tải tệp XML phản đối chuẩn ITU SpaceCom để nạp trực tiếp vào phần mềm ITU."""
    from fastapi.responses import Response
    from leo_coord.spacecom import export_spacecom_xml
    try:
        xml_content = export_spacecom_xml(notice_id)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f'attachment; filename="SpaceCom_Objection_{notice_id}.xml"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/epfd/s1503-simulation")
def get_s1503_simulation(
    alt_km: float = 550.0,
    inc_deg: float = 53.0,
    n_sats: int = 120,
    n_planes: int = 6,
    freq_ghz: float = 11.7,
    eirp_dbw_per_mhz: float = 10.0,
    dish_d_m: float = 1.2,
    station: str = "danang",
    gso_lon: float = 132.0,
    duration_min: int = 60
):
    """Mô phỏng đường cong tích lũy xác suất EPFD CDF theo Rec. ITU-R S.1503 và kiểm chuẩn Res 76."""
    from leo_coord.orbits import WalkerConstellation
    from leo_coord.epfd import simulate_s1503_cumulative_epfd

    st = VIETNAM_GROUND_STATIONS.get(station.lower(), VIETNAM_GROUND_STATIONS["danang"])
    w = WalkerConstellation("SIM_S1503", alt_km, inc_deg, n_sats, n_planes, 1, "delta")
    res = simulate_s1503_cumulative_epfd(
        constellation=w,
        eirp_dbw_per_mhz=eirp_dbw_per_mhz,
        freq_ghz=freq_ghz,
        victim_lat=st["lat"],
        victim_lon=st["lng"],
        gso_lon_deg=gso_lon,
        dish_d_m=dish_d_m,
        duration_s=float(duration_min * 60),
        dt_s=60.0
    )
    res["station_name"] = st["name"]
    return res


# ================= ITU APPENDIX 4 (SPACECAP) & MULTI-AI-AGENT REGULATORY COUNCIL (PHASE 4) =================

@app.get("/api/spacecap/samples")
def get_spacecap_samples_endpoint():
    """Lấy danh sách các hồ sơ mẫu theo chuẩn ITU RR Phụ lục 4 (SpaceCap Format)."""
    from leo_coord.spacecap import load_spacecap_samples, validate_appendix4_completeness
    samples = load_spacecap_samples()
    res = []
    for s in samples:
        v = validate_appendix4_completeness(s)
        d = s.to_dict()
        d["validation"] = v
        res.append(d)
    return {"total": len(res), "filings": res}


@app.post("/api/spacecap/parse")
def parse_spacecap_endpoint(payload: Dict[str, Any]):
    """Bóc tách và kiểm tra tính hợp lệ của hồ sơ Phụ lục 4 SpaceCap tùy chỉnh."""
    from leo_coord.spacecap import parse_appendix4_json, validate_appendix4_completeness
    try:
        filing = parse_appendix4_json(payload)
        val = validate_appendix4_completeness(filing)
        res = filing.to_dict()
        res["validation"] = val
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi phân tích cú pháp Phụ lục 4: {str(e)}")


@app.get("/api/spacecap/download-xml/{filing_id}")
def download_spacecap_xml_endpoint(filing_id: str):
    """Xuất hồ sơ mạng vệ tinh theo chuẩn XML ITU SpaceCap v2.0."""
    from fastapi.responses import Response
    from leo_coord.spacecap import get_filing_by_id, export_appendix4_xml
    filing = get_filing_by_id(filing_id)
    if not filing:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ {filing_id}")
    xml_str = export_appendix4_xml(filing)
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="SpaceCap_AP4_{filing.name}.xml"'}
    )


@app.get("/api/multi-agent/filings")
def get_multi_agent_filings_endpoint():
    """
    Lấy danh sách hồ sơ mạng vệ tinh từ Công báo Quốc tế ITU BR IFIC (Realtime)
    phục vụ cho việc chọn hồ sơ thẩm định của Hội đồng Multi-AI-Agent.
    """
    from leo_coord.spacecap import get_all_available_filings
    filings = get_all_available_filings()
    items = []
    for f in filings:
        sa = f.service_area if isinstance(f.service_area, dict) else {}
        covers_vn = bool(sa.get("vietnam_covered", True))
        inside_arc = bool(sa.get("inside_coordination_arc_6deg", True))
        closest_appr = sa.get("closest_approach_to_vinasat_deg", 1.8)

        # Đánh giá rủi ro sơ bộ
        has_ku = any(10.7 <= b.freq_min_ghz <= 12.75 for b in f.frequency_assignments)
        has_ka = any(17.7 <= b.freq_min_ghz <= 30.0 for b in f.frequency_assignments)
        if covers_vn and inside_arc and (has_ku or has_ka):
            risk_badge = "🔴 NGUY CƠ CAO (CẦN PHỐI HỢP)"
            risk_level = "HIGH"
        elif covers_vn or inside_arc or has_ku or has_ka:
            risk_badge = "🟠 TRUNG BÌNH (CẦN THEO DÕI)"
            risk_level = "MEDIUM"
        else:
            risk_badge = "🟢 AN TOÀN (MIỄN TRỪ PHỐI HỢP)"
            risk_level = "LOW"

        items.append({
            "id": f.id,
            "name": f.name,
            "notifying_adm": f.notifying_adm,
            "operator": f.operator,
            "br_ific_no": f.br_ific_ref,
            "special_section": f.special_section,
            "total_satellites": f.total_satellites,
            "alt_km": f.planes[0].altitude_km if f.planes else 550.0,
            "service_area_covers_vietnam": covers_vn,
            "inside_coordination_arc": inside_arc,
            "closest_approach_deg": closest_appr,
            "risk_level": risk_level,
            "risk_badge": risk_badge,
            "is_real_itu_br_ific": sa.get("is_real_itu_br_ific", False),
            "display_label": f"[BR IFIC {f.br_ific_ref}] {f.name} ({f.notifying_adm} / {f.operator} - {f.total_satellites:,} vệ tinh) - {risk_badge}"
        })

    return {
        "status": "success",
        "source": "ITU Radiocommunication Bureau — BR IFIC (Space Services)",
        "total": len(items),
        "filings": items,
    }


@app.post("/api/multi-agent/sync-itu")
def sync_multi_agent_itu_endpoint():
    """
    Kích hoạt đồng bộ các ấn phẩm công báo ITU BR IFIC mới nhất thời gian thực.
    Cập nhật thời hạn 4 tháng (RR 9.51/9.52) và làm mới danh sách hồ sơ thẩm định.
    """
    from leo_coord.br_ific import sync_br_ific_notices_online
    from leo_coord.spacecap import get_all_available_filings
    sync_res = sync_br_ific_notices_online()
    filings = get_all_available_filings()
    return {
        "status": "success",
        "sync_info": sync_res,
        "total_filings_available": len(filings),
        "message": f"Đã đồng bộ dữ liệu thời gian thực từ Công báo ITU BR IFIC (Số mới nhất: {sync_res['latest_br_ific_in_database']})."
    }


@app.post("/api/multi-agent/convene")
def convene_multi_agent_council_endpoint(payload: Optional[Dict[str, Any]] = Body(default_factory=dict)):
    """
    Triệu tập Hội đồng Trợ lý AI Đa tác nhân Thẩm định Cấp phép & Phối hợp Quốc tế.
    Payload: {"filing_id": "CHNSAT-NGSO-1", "llm_config": {...}} hoặc dữ liệu hồ sơ AP4 tùy chỉnh.
    """
    from leo_coord.spacecap import get_filing_by_id, parse_appendix4_json, get_all_available_filings
    from leo_coord.multi_agent import MultiAgentCouncil

    try:
        payload = payload or {}
        filing_id = payload.get("filing_id")
        if filing_id:
            filing = get_filing_by_id(filing_id)
            if not filing:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ {filing_id}")
        elif "name" in payload or "orbit" in payload:
            filing = parse_appendix4_json(payload)
        else:
            # Default to first available ITU filing
            all_f = get_all_available_filings()
            filing = all_f[0]

        llm_cfg = payload.get("llm_config")
        council = MultiAgentCouncil(filing, llm_config=llm_cfg)
        dossier = council.convene_council()
        return dossier.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thẩm định hội đồng: {str(e)}")


@app.get("/api/multi-agent/export-markdown/{filing_id}")
def export_multi_agent_dossier_markdown(filing_id: str):
    """Xuất toàn văn Báo cáo Thẩm định Kỹ thuật & Pháp lý Song ngữ định dạng Markdown."""
    from fastapi.responses import PlainTextResponse
    from leo_coord.spacecap import get_filing_by_id
    from leo_coord.multi_agent import MultiAgentCouncil

    filing = get_filing_by_id(filing_id)
    if not filing:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ {filing_id}")

    council = MultiAgentCouncil(filing)
    dossier = council.convene_council()

    md = f"""# BÁO CÁO THẨM ĐỊNH KỸ THUẬT & PHÁP LÝ QUỐC TẾ (ITU & VIỆT NAM)
**HỘI ĐỒNG TRỢ LÝ AI ĐA TÁC NHÂN (MULTI-AI-AGENT REGULATORY COUNCIL)**
*Cục Tần số Vô tuyến điện (ARFM) - Cơ quan Thường trực Ủy ban Vũ trụ Việt Nam*

---

### THÔNG TIN HỒ SƠ THẨM ĐỊNH
- **Mạng vệ tinh:** {dossier.satellite_name} ({dossier.notifying_adm})
- **Chủ quản / Khai thác:** {dossier.operator}
- **Công báo BR IFIC:** Số {dossier.br_ific_ref}
- **Ngày thẩm định:** {dossier.assessment_date}
- **Kết luận chung (Verdict):** {dossier.verdict_label_vi}
- **Mức độ rủi ro can nhiễu:** {dossier.risk_level}

---

### TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)
{dossier.executive_summary_vi}

#### ENGLISH EXECUTIVE SUMMARY FOR ITU BILATERAL ENGAGEMENT:
{dossier.executive_summary_en}

---

### ĐIỀU KIỆN TIÊN QUYẾT CẤP PHÉP THÍ ĐIỂM (THEO QUYẾT ĐỊNH 659/QĐ-TTg):
{chr(10).join(f"- {c}" for c in dossier.vietnam_pilot_conditions)}

---

### CĂN CỨ PHÁP LÝ THỂ LỆ VÔ TUYẾN ITU:
{chr(10).join(f"- {g}" for g in dossier.itu_legal_grounds)}

---

### DIỄN BIẾN PHIÊN HỌP HỘI ĐỒNG TRỢ LÝ AI ĐA TÁC NHÂN
"""
    for msg in dossier.deliberations:
        md += f"""
#### {msg['avatar']} {msg['role_title_vi']} ({msg['agent_name']})
**Nhận định kỹ thuật:**
{chr(10).join(f"- {f}" for f in msg['key_findings'])}

**Phát biểu:**
> *"{msg['statement_vi']}"*

**Khuyến nghị hành động:**
{chr(10).join(f"- {r}" for r in msg['recommendations'])}
"""

    return PlainTextResponse(content=md, media_type="text/markdown; charset=utf-8")


@app.post("/api/multi-agent/test-key")
def test_llm_key_endpoint(payload: Optional[Dict[str, Any]] = Body(default_factory=dict)):
    """Kiểm tra tính hợp lệ và độ trễ phản hồi của API Key LLM."""
    from leo_coord.multi_agent import test_llm_connection
    payload = payload or {}
    provider = payload.get("provider", "gemini")
    api_key = (payload.get("api_key") or payload.get("apiKey") or "").strip()
    model = payload.get("model")
    if not api_key:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp API Key để kiểm tra.")
    return test_llm_connection(provider=provider, api_key=api_key, model=model)


# ================= N2YO REAL-TIME SATELLITE TRACKING & COORDINATION =================

@app.get("/api/real-satellites/tracked")
def get_tracked_sats():
    """Lấy danh sách các vệ tinh trọng điểm được cấu hình theo dõi."""
    return {
        "satellites": get_default_tracked_satellites(),
        "stations": list(VIETNAM_GROUND_STATIONS.values())
    }


@app.get("/api/real-satellites/lookup/{norad_id}")
def lookup_real_satellite(norad_id: int):
    """Tra cứu tọa độ thời gian thực, góc ngẩng và khoảng cách tới 3 trạm Việt Nam."""
    result = evaluate_satellite_live(norad_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Lỗi tra cứu vệ tinh"))
    return result


@app.get("/api/real-satellites/tle/{norad_id}")
def get_satellite_tle(norad_id: int):
    """Lấy bộ tham số quỹ đạo TLE hai dòng từ NORAD/N2YO."""
    client = N2YOClient()
    res = client.get_tle(norad_id)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@app.get("/api/real-satellites/above")
def get_satellites_above_station(
    station: str = "hanoi",
    radius_deg: float = 45.0,
    category_id: int = 0,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    alt_m: Optional[float] = None,
    custom_name: Optional[str] = None
):
    """Quét các vệ tinh đang bay qua trạm mặt đất đã chọn (hanoi, danang, hcmc hoặc điểm tùy chỉnh)."""
    if lat is not None and lng is not None:
        st = {
            "id": "custom",
            "name": custom_name or f"Trạm Tùy chỉnh ({lat:.2f}°N, {lng:.2f}°E)",
            "region": "Điểm tham chiếu người dùng",
            "lat": float(lat),
            "lng": float(lng),
            "alt_m": float(alt_m if alt_m is not None else 10.0)
        }
    else:
        st = VIETNAM_GROUND_STATIONS.get(station.lower(), VIETNAM_GROUND_STATIONS["hanoi"])
    client = N2YOClient()
    res = client.get_satellites_above(st["lat"], st["lng"], st["alt_m"], radius_deg, category_id)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    raw_sats = res.get("above", [])
    satellites = []
    for s in raw_sats:
        sat_data = dict(s)
        slat = s.get("satlat")
        slng = s.get("satlng")
        salt = s.get("satalt")
        if slat is not None and slng is not None and salt is not None:
            try:
                el, az, slant_km, compass = calculate_look_angles(
                    obs_lat=st["lat"],
                    obs_lng=st["lng"],
                    obs_alt_m=st["alt_m"],
                    sat_lat=float(slat),
                    sat_lng=float(slng),
                    sat_alt_km=float(salt)
                )
                sat_data["elevation"] = el
                sat_data["azimuth"] = az
                sat_data["azimuth_compass"] = compass
                sat_data["slant_range_km"] = slant_km
            except Exception:
                sat_data["elevation"] = None
                sat_data["azimuth"] = None
                sat_data["azimuth_compass"] = "--"
                sat_data["slant_range_km"] = None
        else:
            sat_data["elevation"] = None
            sat_data["azimuth"] = None
            sat_data["azimuth_compass"] = "--"
            sat_data["slant_range_km"] = None
        satellites.append(sat_data)

    # Sắp xếp vệ tinh có góc ngẩng (Elevation) cao nhất lên đầu
    satellites.sort(
        key=lambda item: item["elevation"] if item.get("elevation") is not None else -999.0,
        reverse=True
    )

    return {
        "station": st,
        "search_radius_deg": radius_deg,
        "satcount": len(satellites),
        "satellites": satellites
    }


@app.get("/api/real-satellites/passes/{norad_id}")
def get_radio_passes_schedule(
    norad_id: int,
    station: str = "danang",
    days: int = 2,
    min_elevation: int = 10,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    alt_m: Optional[float] = None,
    custom_name: Optional[str] = None
):
    """Dự báo lịch liên lạc vô tuyến (Radio passes) qua trạm mặt đất (đặt sẵn hoặc tùy chỉnh)."""
    if lat is not None and lng is not None:
        st = {
            "id": "custom",
            "name": custom_name or f"Trạm Tùy chỉnh ({lat:.2f}°N, {lng:.2f}°E)",
            "region": "Điểm tham chiếu người dùng",
            "lat": float(lat),
            "lng": float(lng),
            "alt_m": float(alt_m if alt_m is not None else 10.0)
        }
    else:
        st = VIETNAM_GROUND_STATIONS.get(station.lower(), VIETNAM_GROUND_STATIONS["danang"])
    client = N2YOClient()
    res = client.get_radio_passes(norad_id, st["lat"], st["lng"], st["alt_m"], days, min_elevation)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return {
        "norad_id": norad_id,
        "satname": res.get("info", {}).get("satname", f"SAT-{norad_id}"),
        "station": st,
        "passescount": res.get("info", {}).get("passescount", 0),
        "passes": res.get("passes", [])
    }


# ================= TAB 2: QUẢN LÝ THAM LUẬN & FILE ĐÍNH KÈM =================

@app.get("/api/documents")
def list_documents():
    """Lấy danh sách các bài tham luận và tài liệu đính kèm."""
    docs = load_documents_meta()
    return docs


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form("Chiến lược & Chính sách"),
    summary: str = Form("")
):
    """Tải lên tài liệu tham luận (.doc, .docx, .xls, .xlsx, .pdf, .ppt, .pptx)."""
    allowed_exts = {".doc", ".docx", ".xls", ".xlsx", ".pdf", ".ppt", ".pptx"}
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng tệp không được hỗ trợ ({ext}). Chỉ chấp nhận: Word (.docx, .doc), Excel (.xlsx, .xls), PDF (.pdf), PowerPoint (.pptx, .ppt)"
        )

    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    saved_filename = f"{doc_id}_{filename}"
    save_path = UPLOAD_DIR / saved_filename

    # Đọc và ghi file
    content = await file.read()
    save_path.write_bytes(content)
    file_size = len(content)

    new_doc = {
        "id": doc_id,
        "title": title.strip() or filename,
        "author": author.strip() or "Khuyết danh",
        "category": category,
        "file_type": ext.lstrip("."),
        "filename": saved_filename,
        "original_filename": filename,
        "file_size": file_size,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary.strip()
    }

    docs = load_documents_meta()
    docs.insert(0, new_doc)
    save_documents_meta(docs)

    return {"status": "success", "message": "Tải tài liệu lên thành công!", "document": new_doc}


@app.get("/api/documents/{doc_id}/download")
def download_document(doc_id: str):
    """Tải xuống tệp tham luận đính kèm."""
    docs = load_documents_meta()
    target = next((d for d in docs if d["id"] == doc_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu!")

    file_path = UPLOAD_DIR / target["filename"]
    if not file_path.exists():
        # Fallback tạo tệp mẫu nếu tệp chưa có
        file_path.write_text(f"Nội dung tài liệu {target['title']}\nTác giả: {target['author']}", encoding="utf-8")

    return FileResponse(
        path=file_path,
        filename=target["original_filename"],
        media_type="application/octet-stream"
    )


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    """Xóa một bài tham luận khỏi danh sách."""
    docs = load_documents_meta()
    target = next((d for d in docs if d["id"] == doc_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu!")

    # Xóa file vật lý
    file_path = UPLOAD_DIR / target["filename"]
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    updated_docs = [d for d in docs if d["id"] != doc_id]
    save_documents_meta(updated_docs)
    return {"status": "success", "message": "Đã xóa tài liệu thành công"}


FEEDBACK_FILE = UPLOAD_DIR / "feedback.json"


def load_feedback() -> dict:
    if not FEEDBACK_FILE.exists():
        return {}
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_feedback(data: dict):
    FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/documents/{doc_id}/feedback")
def get_document_feedback(doc_id: str):
    fb = load_feedback()
    return fb.get(doc_id, [])


@app.post("/api/documents/{doc_id}/feedback")
def post_document_feedback(doc_id: str, payload: dict):
    author = payload.get("author", "Khách mời").strip()
    org = payload.get("organization", "").strip()
    comment = payload.get("comment", "").strip()
    rating = payload.get("rating", "Góp ý chung")

    if not comment:
        raise HTTPException(status_code=400, detail="Vui lòng nhập nội dung góp ý!")

    fb = load_feedback()
    if doc_id not in fb:
        fb[doc_id] = []

    new_fb = {
        "id": f"fb-{uuid.uuid4().hex[:6]}",
        "author": author,
        "organization": org,
        "comment": comment,
        "rating": rating,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    fb[doc_id].append(new_fb)
    save_feedback(fb)
    return {"status": "success", "message": "Gửi góp ý thành công!", "feedback": new_fb}


@app.get("/api/documents/{doc_id}/content")
def get_document_content(doc_id: str):
    docs = load_documents_meta()
    target = next((d for d in docs if d["id"] == doc_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu!")

    # Nếu có content_full lưu sẵn
    if "content_full" in target:
        return {"title": target["title"], "content": target["content_full"]}

    # Đọc từ file nếu là docx/txt
    file_path = UPLOAD_DIR / target["filename"]
    if file_path.exists():
        if target["filename"].endswith(".docx"):
            try:
                import docx
                doc = docx.Document(str(file_path))
                text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                return {"title": target["title"], "content": text}
            except Exception:
                pass
        try:
            return {"title": target["title"], "content": file_path.read_text(encoding="utf-8")}
        except Exception:
            pass

    return {"title": target["title"], "content": target.get("summary", "Nội dung tài liệu.")}


# ================= ITU REGULATORY REFERENCE TABLES API =================

@app.get("/api/reference/registry")
def get_reference_registry():
    """Lấy danh mục Master ITU Reference Tables kèm thông tin pháp lý và thẩm định."""
    from leo_coord import reference as ref
    return ref.load_reference_registry()


@app.get("/api/reference/summary")
def get_reference_summary():
    """Lấy tổng hợp trạng thái thẩm định và độ tin cậy các bảng ITU."""
    from leo_coord import reference as ref
    return ref.get_verification_status_summary()


@app.get("/api/reference/pfd")
def get_reference_pfd():
    """Lấy bảng tham chiếu PFD chuẩn RR Article 21 Table 21-4."""
    from leo_coord import reference as ref
    return ref.load_pfd_reference()


@app.get("/api/reference/epfd")
def get_reference_epfd():
    """Lấy bảng tham chiếu EPFD chuẩn RR Article 22 & Res 76."""
    from leo_coord import reference as ref
    return ref.load_epfd_reference()


@app.get("/api/reference/coordination")
def get_reference_coordination():
    """Lấy bảng tham chiếu Cung phối hợp & Ngưỡng PFD trigger 9.7A/9.7B."""
    from leo_coord import reference as ref
    return ref.load_coordination_reference()


@app.get("/api/reference/milestones")
def get_reference_milestones():
    """Lấy bảng tham chiếu Mốc triển khai Res 35 & Dung sai quỹ đạo Res 8."""
    from leo_coord import reference as ref
    return ref.load_milestones_reference()


@app.get("/api/reference/audit")
def get_reference_audit():
    """Kiểm toán tính toàn vẹn và mức độ tuân thủ của các file tham chiếu ITU."""
    from leo_coord import reference as ref
    return {
        "summary": ref.get_verification_status_summary(),
        "audit_details": ref.audit_reference_tables()
    }


@app.get("/out/bao_cao.html", response_class=HTMLResponse)
@app.get("/report", response_class=HTMLResponse)
def view_assessment_report():
    """Xem báo cáo thẩm định HTML đầy đủ (tự động khởi tạo nếu chưa có file trên đĩa)."""
    report_file = OUT_DIR / "bao_cao.html"
    if not report_file.exists():
        from leo_coord.cli import build_assessment
        cfg = load_config()
        demo_file = DATA_DIR / "demo" / "constellation_demo.yaml"
        if demo_file.exists():
            spec = yaml.safe_load(demo_file.read_text(encoding="utf-8"))
        else:
            spec = {
                "name": "DEMO_LEO_KU",
                "alt_km": 550.0,
                "inc_deg": 53.0,
                "n_sats": 120,
                "n_planes": 6,
                "phasing": 1,
                "kind": "delta",
                "downlink": {"band_ghz": "10.7-12.7", "freq_ghz": 11.7, "eirp_dbw_per_mhz": 10.0}
            }
        w = WalkerConstellation(
            spec["name"], float(spec["alt_km"]), float(spec["inc_deg"]),
            int(spec["n_sats"]), int(spec["n_planes"]), int(spec.get("phasing", 1)), str(spec.get("kind", "delta"))
        )
        biu = date(2024, 3, 1)
        deps = [(date(2025, 6, 1), 14), (date(2028, 12, 1), 59)]
        a = build_assessment(w, spec, cfg, gso_lon=105.5, biu_deadline=biu, deployments=deps, dish_d_m=1.2)
        html = build_html(a)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        report_file.write_text(html, encoding="utf-8")

    return HTMLResponse(content=report_file.read_text(encoding="utf-8"))


# Mount static & output files
app.mount("/out", StaticFiles(directory=str(OUT_DIR)), name="out")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Hệ thống đang khởi động...</h1>")
