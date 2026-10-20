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
from typing import Optional, List

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
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

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
METADATA_FILE = UPLOAD_DIR / "documents.json"
DATA_DIR = BASE_DIR.parent / "data"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

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
        {"name": "TP. Hồ Chí Minh (Trạm Nam)", "lat": 10.82, "lon": 106.63, "color": "#fbbf24"}
    ]

    return {
        "period_s": round(period_s, 1),
        "sim_time_sec": round(sim_time_sec, 1),
        "satellites": satellites,
        "orbit_planes": orbit_planes,
        "ref_points": ref_points,
        "footprint_radius_km": round(footprint_radius_km(alt_km, 10.0), 1)
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


# Mount static files

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Hệ thống đang khởi động...</h1>")
