"""
Mô-đun Bộ Giải mã CSDL Công báo Quốc tế ITU BR IFIC (SRS.mdb / SQLite Diff Engine)
Giai đoạn 7: Đọc trực tiếp Cơ sở dữ liệu Mạng Thông tin Không gian (Space Network System - SNS/SRS)
từ đĩa công báo BR IFIC (Space Services) định kỳ 2 tuần/lần của ITU dưới dạng tệp Microsoft Access (.mdb)
hoặc SQLite (.sqlite/.db).

Cung cấp:
1. BRDatabaseConnector: Kết nối và trích xuất hồ sơ Phụ lục 4 từ CSDL Access MDB và SQLite.
2. BRDiffEngine: So sánh 2 kỳ công báo (Diff Engine) phát hiện hồ sơ mới, hồ sơ sửa đổi (MOD),
   đánh giá xâm lấn vùng trời Việt Nam và cung quỹ đạo bảo vệ VINASAT-1/2 (131.8°E - 132.0°E).
3. BRConnectionManager: Quản lý trạng thái "Sẵn sàng kết nối" (Live Connection) tới CSDL máy chủ/mạng nội bộ.
"""

from __future__ import annotations

import csv
import datetime
import io
import os
import shutil
import sqlite3
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from leo_coord.spacecap import (
    Appendix4Filing,
    FrequencyAssignment,
    OrbitalPlane,
    save_uploaded_filing,
)

# Thư mục lưu trữ CSDL tham chiếu
REFERENCE_DIR = Path(__file__).resolve().parent.parent / "data" / "reference"
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads" / "srs"


@dataclass
class BRNoticeRecord:
    ntc_id: int
    sat_name: str
    adm: str
    operator: str
    br_ific_no: int
    special_sec: str
    ntc_type: str = "CR/C"
    act_code: str = "A"  # A: Add (Mới), M: Modify (Sửa đổi), S: Suppress (Đình chỉ)
    d_adm: str = ""
    filing_type: str = "NON-GSO FSS"
    alt_km: float = 550.0
    incl_deg: float = 53.0
    total_satellites: int = 120
    num_planes: int = 6
    sats_per_plane: int = 20
    freq_min_ghz: float = 10.7
    freq_max_ghz: float = 12.75
    band_name: str = "Ku-band Downlink"
    vietnam_covered: bool = True
    closest_approach_to_vinasat_deg: float = 1.8
    inside_coordination_arc_6deg: bool = True

    def to_filing(self) -> Appendix4Filing:
        """Chuyển đổi bản ghi công báo sang đối tượng Appendix4Filing chuẩn."""
        filing_id = f"SRS-{self.br_ific_no}-{self.sat_name.replace(' ', '_').upper()}"
        plane = OrbitalPlane(
            plane_id=1,
            altitude_km=self.alt_km,
            inclination_deg=self.incl_deg,
            satellites_per_plane=self.sats_per_plane,
            num_planes=self.num_planes,
        )
        freq = FrequencyAssignment(
            band_name=self.band_name,
            freq_min_ghz=self.freq_min_ghz,
            freq_max_ghz=self.freq_max_ghz,
            polarization="Circular",
            service="FSS",
            max_pfd_dbw_m2_4khz=-146.0 if self.freq_min_ghz < 15.0 else None,
            max_pfd_dbw_m2_1mhz=-115.0 if self.freq_min_ghz >= 15.0 else None,
            allocated_to_vietnam_services=["VINASAT-1", "VINASAT-2"] if self.freq_min_ghz < 15.0 else ["Gateway Quế Dương", "Gateway Bình Dương"],
        )
        sa = {
            "vietnam_covered": self.vietnam_covered,
            "inside_coordination_arc_6deg": self.inside_coordination_arc_6deg,
            "closest_approach_to_vinasat_deg": self.closest_approach_to_vinasat_deg,
            "source_type": "ITU_BR_IFIC_SRS_DB",
            "br_ific_no": self.br_ific_no,
            "action_code": self.act_code,
            "is_real_itu_br_ific": True,
        }
        return Appendix4Filing(
            id=filing_id,
            name=self.sat_name,
            notifying_adm=self.adm,
            operator=self.operator,
            br_ific_ref=self.br_ific_no,
            special_section=self.special_sec,
            filing_type=self.filing_type,
            total_satellites=self.total_satellites,
            planes=[plane],
            frequency_assignments=[freq],
            service_area=sa,
            applicable_itu_provisions=[
                "RR No. 9.7B (GSO vs Non-GSO Coordination)",
                "RR No. 9.51/9.52 (4-Month Objection Window)",
                "RR No. 22.2 (Protection of GSO Systems)",
            ],
        )


# ================= TIỆN ÍCH HỖ TRỢ MDBTOOLS & PANDAS (LINUX/DOCKER) =================

def is_mdbtools_available() -> bool:
    """Kiểm tra xem mdbtools (mdb-tables, mdb-export) có sẵn trong hệ thống (Linux/Docker) không."""
    return shutil.which("mdb-tables") is not None and shutil.which("mdb-export") is not None


def list_mdb_tables_via_mdbtools(file_path: Path | str) -> List[str]:
    """Sử dụng mdb-tables để liệt kê các bảng trong file Access .mdb."""
    res = subprocess.run(
        ["mdb-tables", "-1", str(file_path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    return [t.strip() for t in res.stdout.splitlines() if t.strip() and not t.strip().startswith("MSys")]


def export_mdb_table_via_mdbtools(file_path: Path | str, table_name: str) -> List[Dict[str, Any]]:
    """Xuất một bảng trong tệp .mdb sang danh sách dict qua mdb-export (tương thích cả khi không có pandas)."""
    res = subprocess.run(
        ["mdb-export", str(file_path), table_name],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    reader = csv.DictReader(io.StringIO(res.stdout))
    return [{str(k).strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()} for row in reader]


def read_mdb_table_to_dataframe(file_path: Path | str, table_name: str) -> Any:
    """Trích xuất bảng .mdb trực tiếp thành pandas DataFrame kết hợp mdbtools (nếu cài pandas)."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("Cần cài đặt pandas ('pip install pandas') để xuất DataFrame.")
    res = subprocess.run(
        ["mdb-export", str(file_path), table_name],
        capture_output=True,
        check=True,
        timeout=60,
    )
    return pd.read_csv(io.BytesIO(res.stdout))


def parse_itu_srs_records(
    notice_rows: List[Dict[str, Any]],
    geo_rows: Optional[List[Dict[str, Any]]] = None,
    non_geo_rows: Optional[List[Dict[str, Any]]] = None,
    orbit_rows: Optional[List[Dict[str, Any]]] = None,
    ssn_rows: Optional[List[Dict[str, Any]]] = None,
    grp_rows: Optional[List[Dict[str, Any]]] = None,
) -> List[BRNoticeRecord]:
    """
    Bóc tách CSDL chuẩn ITU Space Network System (SpaceCap SRS / BR IFIC):
    Liên kết các bảng quan hệ notice, geo, non_geo, orbit, pub_ssn, grp thành các thực thể BRNoticeRecord.
    """
    geo_map: Dict[int, Dict[str, Any]] = {}
    if geo_rows:
        for r in geo_rows:
            try:
                nid = int(r.get("ntc_id", 0))
                if nid and nid not in geo_map:
                    geo_map[nid] = {
                        "sat_name": str(r.get("sat_name") or "").strip(),
                        "long_nom": float(r["long_nom"]) if r.get("long_nom") is not None and str(r["long_nom"]).strip() != "" else None,
                    }
            except Exception:
                continue

    non_geo_map: Dict[int, Dict[str, Any]] = {}
    if non_geo_rows:
        for r in non_geo_rows:
            try:
                nid = int(r.get("ntc_id", 0))
                if nid and nid not in non_geo_map:
                    non_geo_map[nid] = {
                        "sat_name": str(r.get("sat_name") or "").strip(),
                        "nbr_plane": int(float(r["nbr_plane"])) if r.get("nbr_plane") is not None and str(r["nbr_plane"]).strip() != "" else 1,
                    }
            except Exception:
                continue

    orbit_map: Dict[int, Dict[str, Any]] = {}
    if orbit_rows:
        for r in orbit_rows:
            try:
                nid = int(r.get("ntc_id", 0))
                if nid and nid not in orbit_map:
                    orbit_map[nid] = {
                        "alt_km": float(r["apog"]) if r.get("apog") is not None and str(r["apog"]).strip() != "" else 600.0,
                        "incl_deg": float(r["inclin_ang"]) if r.get("inclin_ang") is not None and str(r["inclin_ang"]).strip() != "" else 50.0,
                        "sats_per_plane": int(float(r["nbr_sat_pl"])) if r.get("nbr_sat_pl") is not None and str(r["nbr_sat_pl"]).strip() != "" else 1,
                    }
            except Exception:
                continue

    ssn_map: Dict[int, str] = {}
    if ssn_rows:
        for r in ssn_rows:
            try:
                nid = int(r.get("ntc_id", 0))
                ref = str(r.get("ssn_ref") or "").strip()
                no = str(r.get("ssn_no") or "").strip()
                if nid and nid not in ssn_map and ref:
                    ssn_map[nid] = f"{ref}/{no}" if no else ref
            except Exception:
                continue

    freq_map: Dict[int, Tuple[float, float, str]] = {}
    if grp_rows:
        for r in grp_rows:
            try:
                nid = int(r.get("ntc_id", 0))
                f_min_raw = r.get("freq_min")
                f_max_raw = r.get("freq_max")
                if nid and f_min_raw is not None and str(f_min_raw).strip() != "":
                    f_min = float(f_min_raw) / 1000.0
                    f_max = (float(f_max_raw) if f_max_raw is not None and str(f_max_raw).strip() != "" else float(f_min_raw)) / 1000.0
                    if nid not in freq_map:
                        freq_map[nid] = (f_min, f_max, "")
                    else:
                        cur_min, cur_max, _ = freq_map[nid]
                        freq_map[nid] = (min(cur_min, f_min), max(cur_max, f_max), "")
            except Exception:
                continue

    notices: List[BRNoticeRecord] = []
    for r in notice_rows:
        try:
            nid = int(r.get("ntc_id", 1))
            adm = str(r.get("adm") or "ITU").strip()
            org = str(r.get("ntwk_org") or r.get("operator") or adm).strip()
            ntc_type = str(r.get("ntc_type") or "G").strip().upper()
            act_code = str(r.get("act_code") or "A").strip().upper()
            wic_no = int(float(r.get("wic_no") or r.get("br_ific_no") or 2691))
            d_adm_val = r.get("d_adm") or r.get("d_wic") or r.get("d_rcv")
            d_adm = str(d_adm_val)[:10] if d_adm_val else datetime.date.today().isoformat()

            if nid in non_geo_map:
                sat_name = non_geo_map[nid]["sat_name"] or f"NGSO-{nid}"
                is_gso = False
                orb = orbit_map.get(nid, {})
                alt_km = orb.get("alt_km", 600.0)
                incl_deg = orb.get("incl_deg", 50.0)
                num_planes = non_geo_map[nid].get("nbr_plane", 1) or 1
                sats_per_plane = orb.get("sats_per_plane", 1) or 1
                total_sats = max(1, num_planes * sats_per_plane)
                pos_deg = None
                filing_type = "NON-GSO FSS/MSS"
            elif nid in geo_map:
                sat_name = geo_map[nid]["sat_name"] or f"GSO-{nid}"
                is_gso = True
                alt_km = 35786.0
                incl_deg = 0.0
                num_planes = 1
                sats_per_plane = 1
                total_sats = 1
                pos_deg = geo_map[nid]["long_nom"]
                filing_type = "GSO FSS/BSS"
            else:
                sat_name = str(r.get("sat_name") or f"SAT-{nid}").strip()
                is_gso = (ntc_type == "G")
                alt_km = 35786.0 if is_gso else 600.0
                incl_deg = 0.0 if is_gso else 50.0
                num_planes = 1
                sats_per_plane = 1
                total_sats = 1
                pos_deg = None
                filing_type = "GSO FSS" if is_gso else "NON-GSO FSS"

            ssn = ssn_map.get(nid, str(r.get("special_sec") or f"PART I-S / {wic_no}"))
            f_min, f_max, _ = freq_map.get(nid, (10.7, 12.75, "Ku-band"))

            if is_gso and pos_deg is not None:
                delta_vinasat = min(abs(pos_deg - 132.0), abs(pos_deg - 131.8))
                inside_arc = delta_vinasat <= 6.0
                vn_covered = (70.0 <= pos_deg <= 150.0)
            else:
                delta_vinasat = 1.8
                inside_arc = True
                vn_covered = (incl_deg >= 8.0)

            if f_max <= 3.0:
                band_name = "L/S-band"
            elif f_max <= 8.0:
                band_name = "C-band"
            elif f_max <= 18.0:
                band_name = "Ku-band"
            elif f_max <= 31.0:
                band_name = "Ka-band"
            elif f_max <= 55.0:
                band_name = "Q/V-band"
            else:
                band_name = "EHF-band"

            notices.append(
                BRNoticeRecord(
                    ntc_id=nid,
                    sat_name=sat_name,
                    adm=adm,
                    operator=org,
                    br_ific_no=wic_no,
                    special_sec=ssn,
                    ntc_type=ntc_type,
                    act_code=act_code,
                    d_adm=d_adm,
                    filing_type=filing_type,
                    alt_km=alt_km,
                    incl_deg=incl_deg,
                    total_satellites=total_sats,
                    num_planes=num_planes,
                    sats_per_plane=sats_per_plane,
                    freq_min_ghz=round(f_min, 3),
                    freq_max_ghz=round(f_max, 3),
                    band_name=band_name,
                    vietnam_covered=vn_covered,
                    closest_approach_to_vinasat_deg=round(delta_vinasat, 2),
                    inside_coordination_arc_6deg=inside_arc,
                )
            )
        except Exception:
            continue

    return notices


class BRDatabaseConnector:
    """Bộ kết nối CSDL ITU BR IFIC (hỗ trợ SQLite và Microsoft Access .mdb)."""

    def __init__(self, db_path_or_str: str | Path):
        self.raw_path = str(db_path_or_str).strip()
        self.is_sqlite = False
        self.is_mdb = False
        self.is_odbc = False
        self._detect_type()

    def _detect_type(self) -> None:
        p_lower = self.raw_path.lower()
        if p_lower.startswith("driver=") or p_lower.startswith("dsn="):
            self.is_odbc = True
        elif p_lower.endswith(".sqlite") or p_lower.endswith(".db") or "sqlite" in p_lower:
            self.is_sqlite = True
        elif p_lower.endswith(".mdb") or p_lower.endswith(".accdb"):
            self.is_mdb = True
        else:
            # Kiểm tra tệp thực tế
            p = Path(self.raw_path)
            if p.exists() and p.is_file():
                # Đọc vài byte đầu kiểm tra SQLite header
                try:
                    with open(p, "rb") as f:
                        header = f.read(16)
                    if b"SQLite format 3" in header:
                        self.is_sqlite = True
                    else:
                        self.is_mdb = True
                except Exception:
                    self.is_mdb = True
            else:
                self.is_sqlite = True

    def test_connection(self) -> Dict[str, Any]:
        """Kiểm tra kết nối tới cơ sở dữ liệu và liệt kê các bảng."""
        tables: List[str] = []
        record_count = 0
        edition_guess = None

        if self.is_sqlite:
            try:
                conn = sqlite3.connect(self.raw_path)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
                # Kiểm tra số lượng bản ghi notice
                for t in ["notices", "notice", "tbl_notices", "srs_notices"]:
                    if t in tables:
                        cur.execute(f"SELECT COUNT(*) FROM {t}")
                        record_count = cur.fetchone()[0]
                        cur.execute(f"SELECT MAX(br_ific_no) FROM {t}")
                        val = cur.fetchone()[0]
                        if val:
                            edition_guess = int(val)
                        break
                conn.close()
                return {
                    "connected": True,
                    "db_type": "SQLite",
                    "path": self.raw_path,
                    "table_count": len(tables),
                    "tables": tables,
                    "record_count": record_count,
                    "latest_ific_edition": edition_guess or 3015,
                    "message": f"Kết nối CSDL SQLite thành công! Tìm thấy {len(tables)} bảng và {record_count} bản ghi hồ sơ.",
                }
            except Exception as e:
                return {
                    "connected": False,
                    "db_type": "SQLite",
                    "path": self.raw_path,
                    "error": str(e),
                    "message": f"Không thể kết nối CSDL SQLite: {e}",
                }
        elif self.is_mdb:
            # 1. Thử kết nối qua pyodbc (Windows có cài Microsoft Access Database Engine)
            odbc_err_msg = ""
            try:
                import pyodbc
                conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.raw_path};"
                conn = pyodbc.connect(conn_str, autocommit=True)
                cur = conn.cursor()
                # Liệt kê bảng trong Access
                for row in cur.tables(tableType="TABLE"):
                    t_name = row.table_name
                    if not t_name.startswith("MSys"):
                        tables.append(t_name)
                for t in ["notices", "notice", "tbl_notices", "srs_notices"]:
                    if t in tables:
                        cur.execute(f"SELECT COUNT(*) FROM [{t}]")
                        record_count = cur.fetchone()[0]
                        try:
                            cur.execute(f"SELECT TOP 1 * FROM [{t}]")
                            t_cols = [c[0].lower() for c in cur.description]
                            if "br_ific_no" in t_cols:
                                cur.execute(f"SELECT MAX(br_ific_no) FROM [{t}]")
                                val = cur.fetchone()[0]
                                if val:
                                    edition_guess = int(val)
                            elif "wic_no" in t_cols:
                                cur.execute(f"SELECT MAX(wic_no) FROM [{t}]")
                                val = cur.fetchone()[0]
                                if val:
                                    edition_guess = int(val)
                        except Exception:
                            pass
                        break
                conn.close()
                return {
                    "connected": True,
                    "db_type": "Microsoft Access (.mdb qua pyodbc)",
                    "path": self.raw_path,
                    "table_count": len(tables),
                    "tables": tables,
                    "record_count": record_count,
                    "latest_ific_edition": edition_guess or 3015,
                    "message": f"Kết nối CSDL Microsoft Access (.mdb) qua pyodbc thành công! Tìm thấy {len(tables)} bảng và {record_count} bản ghi.",
                }
            except Exception as e:
                odbc_err_msg = str(e)

            # 2. Fallback sang mdbtools (tiêu chuẩn cho môi trường Linux / Docker)
            if is_mdbtools_available():
                try:
                    tables = list_mdb_tables_via_mdbtools(self.raw_path)
                    for t in ["notices", "notice", "tbl_notices", "srs_notices"]:
                        if t in tables:
                            rows = export_mdb_table_via_mdbtools(self.raw_path, t)
                            record_count = len(rows)
                            for r in rows:
                                if r.get("br_ific_no"):
                                    try:
                                        edition_guess = max(edition_guess or 0, int(r["br_ific_no"]))
                                    except Exception:
                                        pass
                            break
                    return {
                        "connected": True,
                        "db_type": "Microsoft Access (.mdb qua mdbtools)",
                        "path": self.raw_path,
                        "table_count": len(tables),
                        "tables": tables,
                        "record_count": record_count,
                        "latest_ific_edition": edition_guess or 3015,
                        "message": f"Kết nối CSDL Microsoft Access (.mdb) qua mdbtools thành công! Tìm thấy {len(tables)} bảng và {record_count} bản ghi.",
                    }
                except Exception as mdb_err:
                    return {
                        "connected": False,
                        "db_type": "Microsoft Access (.mdb)",
                        "path": self.raw_path,
                        "error": str(mdb_err),
                        "message": f"Lỗi đọc .mdb qua mdbtools: {mdb_err}",
                    }

            # 3. Không có cả pyodbc lẫn mdbtools
            return {
                "connected": False,
                "db_type": "Microsoft Access (.mdb)",
                "path": self.raw_path,
                "error": odbc_err_msg or "No pyodbc or mdbtools available",
                "message": (
                    f"Lỗi kết nối Microsoft Access (.mdb): {odbc_err_msg or 'Thiếu thư viện/driver'}. "
                    "Gợi ý: Trên máy chủ Linux/Docker, hãy cài đặt 'mdbtools' (chạy lệnh 'apt-get update && apt-get install -y mdbtools') "
                    "hoặc chuyển đổi tệp sang định dạng SQLite (.sqlite)."
                ),
            }
        else:
            return {
                "connected": False,
                "db_type": "Unknown",
                "path": self.raw_path,
                "message": "Không nhận diện được định dạng CSDL (cần .sqlite, .db hoặc .mdb).",
            }

    def fetch_notices(self) -> List[BRNoticeRecord]:
        """Trích xuất danh sách tất cả các bản ghi hồ sơ từ CSDL."""
        notices: List[BRNoticeRecord] = []
        if self.is_sqlite:
            conn = sqlite3.connect(self.raw_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            table_name = None
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [r[0] for r in cur.fetchall()]
            for candidate in ["notices", "notice", "tbl_notices", "srs_notices"]:
                if candidate in all_tables:
                    table_name = candidate
                    break
            if not table_name:
                conn.close()
                return []

            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()
            for r in rows:
                col_keys = r.keys()
                n = BRNoticeRecord(
                    ntc_id=int(r["ntc_id"]) if "ntc_id" in col_keys else 1,
                    sat_name=str(r["sat_name"]) if "sat_name" in col_keys else "NON-GSO-SAT",
                    adm=str(r["adm"]) if "adm" in col_keys else "USA",
                    operator=str(r["operator"]) if "operator" in col_keys else "Global Operator",
                    br_ific_no=int(r["br_ific_no"]) if "br_ific_no" in col_keys else 3015,
                    special_sec=str(r["special_sec"]) if "special_sec" in col_keys else "CR/C/1000",
                    ntc_type=str(r["ntc_type"]) if "ntc_type" in col_keys else "CR/C",
                    act_code=str(r["act_code"]) if "act_code" in col_keys else "A",
                    d_adm=str(r["d_adm"]) if "d_adm" in col_keys else datetime.date.today().isoformat(),
                    filing_type=str(r["filing_type"]) if "filing_type" in col_keys else "NON-GSO FSS",
                    alt_km=float(r["alt_km"]) if "alt_km" in col_keys and r["alt_km"] is not None else 550.0,
                    incl_deg=float(r["incl_deg"]) if "incl_deg" in col_keys and r["incl_deg"] is not None else 53.0,
                    total_satellites=int(r["total_satellites"]) if "total_satellites" in col_keys and r["total_satellites"] is not None else 120,
                    num_planes=int(r["num_planes"]) if "num_planes" in col_keys and r["num_planes"] is not None else 6,
                    sats_per_plane=int(r["sats_per_plane"]) if "sats_per_plane" in col_keys and r["sats_per_plane"] is not None else 20,
                    freq_min_ghz=float(r["freq_min_ghz"]) if "freq_min_ghz" in col_keys and r["freq_min_ghz"] is not None else 10.7,
                    freq_max_ghz=float(r["freq_max_ghz"]) if "freq_max_ghz" in col_keys and r["freq_max_ghz"] is not None else 12.75,
                    band_name=str(r["band_name"]) if "band_name" in col_keys and r["band_name"] else "Ku-band Downlink",
                    vietnam_covered=bool(int(r["vietnam_covered"])) if "vietnam_covered" in col_keys else True,
                    closest_approach_to_vinasat_deg=float(r["closest_approach_to_vinasat_deg"]) if "closest_approach_to_vinasat_deg" in col_keys and r["closest_approach_to_vinasat_deg"] is not None else 1.8,
                    inside_coordination_arc_6deg=bool(int(r["inside_coordination_arc_6deg"])) if "inside_coordination_arc_6deg" in col_keys else True,
                )
                notices.append(n)
            conn.close()

        elif self.is_mdb:
            rows_data: List[Dict[str, Any]] = []
            used_odbc = False
            # 1. Thử truy vấn qua pyodbc (Windows có cài Access Database Engine)
            try:
                import pyodbc
                conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.raw_path};"
                conn = pyodbc.connect(conn_str, autocommit=True)
                cur = conn.cursor()
                all_tables = [row.table_name for row in cur.tables(tableType="TABLE") if not row.table_name.startswith("MSys")]

                if "notice" in all_tables and ("geo" in all_tables or "non_geo" in all_tables):
                    # Schema CSDL ITU SpaceCap / BR IFIC chính thống
                    cur.execute("SELECT * FROM [notice]")
                    cols = [c[0].lower() for c in cur.description]
                    notice_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    geo_rows = []
                    if "geo" in all_tables:
                        cur.execute("SELECT * FROM [geo]")
                        cols = [c[0].lower() for c in cur.description]
                        geo_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    non_geo_rows = []
                    if "non_geo" in all_tables:
                        cur.execute("SELECT * FROM [non_geo]")
                        cols = [c[0].lower() for c in cur.description]
                        non_geo_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    orbit_rows = []
                    if "orbit" in all_tables:
                        cur.execute("SELECT * FROM [orbit]")
                        cols = [c[0].lower() for c in cur.description]
                        orbit_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    ssn_rows = []
                    if "pub_ssn" in all_tables:
                        cur.execute("SELECT * FROM [pub_ssn]")
                        cols = [c[0].lower() for c in cur.description]
                        ssn_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    grp_rows = []
                    if "grp" in all_tables:
                        cur.execute("SELECT ntc_id, freq_min, freq_max FROM [grp] WHERE freq_min IS NOT NULL")
                        cols = [c[0].lower() for c in cur.description]
                        grp_rows = [dict(zip(cols, r)) for r in cur.fetchall()]

                    conn.close()
                    return parse_itu_srs_records(notice_rows, geo_rows, non_geo_rows, orbit_rows, ssn_rows, grp_rows)

                # Schema bảng phẳng (notices, tbl_notices...)
                target_tbl = "notices"
                for cand in ["notices", "tbl_notices", "srs_notices", "notice"]:
                    if cand in all_tables:
                        target_tbl = cand
                        break

                cur.execute(f"SELECT * FROM [{target_tbl}]")
                cols = [c[0].lower() for c in cur.description]
                rows_data = [dict(zip(cols, r)) for r in cur.fetchall()]
                conn.close()
                used_odbc = True
            except Exception:
                used_odbc = False

            # 2. Fallback sang mdbtools (Linux / Docker)
            if not used_odbc and is_mdbtools_available():
                try:
                    tables = list_mdb_tables_via_mdbtools(self.raw_path)
                    if "notice" in tables and ("geo" in tables or "non_geo" in tables):
                        notice_rows = export_mdb_table_via_mdbtools(self.raw_path, "notice")
                        geo_rows = export_mdb_table_via_mdbtools(self.raw_path, "geo") if "geo" in tables else []
                        non_geo_rows = export_mdb_table_via_mdbtools(self.raw_path, "non_geo") if "non_geo" in tables else []
                        orbit_rows = export_mdb_table_via_mdbtools(self.raw_path, "orbit") if "orbit" in tables else []
                        ssn_rows = export_mdb_table_via_mdbtools(self.raw_path, "pub_ssn") if "pub_ssn" in tables else []
                        grp_rows = export_mdb_table_via_mdbtools(self.raw_path, "grp") if "grp" in tables else []
                        return parse_itu_srs_records(notice_rows, geo_rows, non_geo_rows, orbit_rows, ssn_rows, grp_rows)

                    target_table = None
                    for candidate in ["notices", "notice", "tbl_notices", "srs_notices"]:
                        if candidate in tables:
                            target_table = candidate
                            break
                    if not target_table and tables:
                        target_table = tables[0]

                    if target_table:
                        rows_data = export_mdb_table_via_mdbtools(self.raw_path, target_table)
                except Exception:
                    pass

            def safe_float(val: Any, default: float) -> float:
                try:
                    return float(val) if val is not None and str(val).strip() != "" else default
                except (ValueError, TypeError):
                    return default

            def safe_int(val: Any, default: int) -> int:
                try:
                    return int(float(val)) if val is not None and str(val).strip() != "" else default
                except (ValueError, TypeError):
                    return default

            for row_dict in rows_data:
                n = BRNoticeRecord(
                    ntc_id=safe_int(row_dict.get("ntc_id"), 1),
                    sat_name=str(row_dict.get("sat_name") or row_dict.get("ntwk_org") or "NON-GSO-SAT").strip(),
                    adm=str(row_dict.get("adm") or "USA").strip(),
                    operator=str(row_dict.get("operator") or row_dict.get("org") or "Space Operator").strip(),
                    br_ific_no=safe_int(row_dict.get("br_ific_no") or row_dict.get("wic_no"), 3015),
                    special_sec=str(row_dict.get("special_sec") or row_dict.get("sec_no") or "CR/C/1000").strip(),
                    ntc_type=str(row_dict.get("ntc_type") or "CR/C").strip(),
                    act_code=str(row_dict.get("act_code") or "A").strip(),
                    d_adm=str(row_dict.get("d_adm") or datetime.date.today().isoformat()).strip(),
                    filing_type=str(row_dict.get("filing_type") or "NON-GSO FSS").strip(),
                    alt_km=safe_float(row_dict.get("alt_km"), 550.0),
                    incl_deg=safe_float(row_dict.get("incl_deg"), 53.0),
                    total_satellites=safe_int(row_dict.get("total_satellites"), 120),
                    num_planes=safe_int(row_dict.get("num_planes"), 6),
                    sats_per_plane=safe_int(row_dict.get("sats_per_plane"), 20),
                    freq_min_ghz=safe_float(row_dict.get("freq_min_ghz"), 10.7),
                    freq_max_ghz=safe_float(row_dict.get("freq_max_ghz"), 12.75),
                    band_name=str(row_dict.get("band_name") or "Ku-band Downlink").strip(),
                    vietnam_covered=bool(safe_int(row_dict.get("vietnam_covered"), 1)),
                    closest_approach_to_vinasat_deg=safe_float(row_dict.get("closest_approach_to_vinasat_deg"), 1.8),
                    inside_coordination_arc_6deg=bool(safe_int(row_dict.get("inside_coordination_arc_6deg"), 1)),
                )
                notices.append(n)

        return notices


class BRDiffEngine:
    """Động cơ so sánh đối soát tự động giữa 2 kỳ công báo BR IFIC (Diff Engine)."""

    @staticmethod
    def compare_notices(
        base_notices: List[BRNoticeRecord],
        target_notices: List[BRNoticeRecord],
        base_label: str = "BR IFIC Kỳ trước",
        target_label: str = "BR IFIC Kỳ mới nhất",
    ) -> Dict[str, Any]:
        """
        So sánh giữa kỳ công báo cũ (base) và kỳ công báo mới (target):
        - Hồ sơ mới xuất bản (New Filings)
        - Hồ sơ sửa đổi (Modified Filings - MOD)
        - Hồ sơ đình chỉ/rút hồ sơ (Suppressed / Cancelled)
        - Cảnh báo hồ sơ ảnh hưởng đến chủ quyền không gian Việt Nam & Vinasat-1/2
        """
        base_map = {n.sat_name.strip().upper(): n for n in base_notices}
        target_map = {n.sat_name.strip().upper(): n for n in target_notices}

        new_filings: List[Dict[str, Any]] = []
        modified_filings: List[Dict[str, Any]] = []
        unchanged_filings: List[Dict[str, Any]] = []
        suppressed_filings: List[Dict[str, Any]] = []
        vietnam_risk_filings: List[Dict[str, Any]] = []

        now_date = datetime.date.today()

        for name, t_not in target_map.items():
            # Tính hạn 4 tháng nộp phản đối RR 9.51/9.52
            days_left = 122
            deadline_str = (now_date + datetime.timedelta(days=days_left)).strftime("%Y-%m-%d")

            is_vn_risk = t_not.vietnam_covered and (t_not.inside_coordination_arc_6deg or t_not.closest_approach_to_vinasat_deg < 6.0)

            record_summary = {
                "sat_name": t_not.sat_name,
                "adm": t_not.adm,
                "operator": t_not.operator,
                "br_ific_no": t_not.br_ific_no,
                "special_sec": t_not.special_sec,
                "act_code": t_not.act_code,
                "total_satellites": t_not.total_satellites,
                "alt_km": t_not.alt_km,
                "incl_deg": t_not.incl_deg,
                "frequency": f"{t_not.freq_min_ghz:.2f} - {t_not.freq_max_ghz:.2f} GHz ({t_not.band_name})",
                "vietnam_covered": t_not.vietnam_covered,
                "closest_approach_vinasat_deg": t_not.closest_approach_to_vinasat_deg,
                "inside_arc_6deg": t_not.inside_coordination_arc_6deg,
                "spacecom_deadline": deadline_str,
                "spacecom_days_left": days_left,
                "is_vietnam_risk": is_vn_risk,
                "filing_id": f"SRS-{t_not.br_ific_no}-{t_not.sat_name.replace(' ', '_').upper()}",
            }

            if is_vn_risk:
                vietnam_risk_filings.append(record_summary)

            if name not in base_map:
                record_summary["diff_type"] = "NEW"
                record_summary["diff_label"] = "HỒ SƠ MỚI XUẤT BẢN"
                new_filings.append(record_summary)
            else:
                b_not = base_map[name]
                changes = []
                if t_not.total_satellites != b_not.total_satellites:
                    changes.append(f"Quy mô vệ tinh: {b_not.total_satellites:,} -> {t_not.total_satellites:,} vệ tinh")
                if abs(t_not.alt_km - b_not.alt_km) > 1.0:
                    changes.append(f"Độ cao: {b_not.alt_km:.0f}km -> {t_not.alt_km:.0f}km")
                if abs(t_not.incl_deg - b_not.incl_deg) > 0.5:
                    changes.append(f"Góc nghiêng: {b_not.incl_deg:.1f}° -> {t_not.incl_deg:.1f}°")
                if abs(t_not.freq_min_ghz - b_not.freq_min_ghz) > 0.05 or abs(t_not.freq_max_ghz - b_not.freq_max_ghz) > 0.05:
                    changes.append(f"Dải tần: {b_not.freq_min_ghz}-{b_not.freq_max_ghz}GHz -> {t_not.freq_min_ghz}-{t_not.freq_max_ghz}GHz")
                if t_not.special_sec != b_not.special_sec:
                    changes.append(f"Mục đặc biệt: {b_not.special_sec} -> {t_not.special_sec}")

                if changes or t_not.act_code == "M":
                    record_summary["diff_type"] = "MOD"
                    record_summary["diff_label"] = "HỒ SƠ SỬA ĐỔI (MOD)"
                    record_summary["changes"] = changes if changes else ["Cập nhật tham số kỹ thuật trong ấn phẩm sửa đổi"]
                    modified_filings.append(record_summary)
                else:
                    record_summary["diff_type"] = "UNCHANGED"
                    unchanged_filings.append(record_summary)

        for name, b_not in base_map.items():
            if name not in target_map:
                suppressed_filings.append({
                    "sat_name": b_not.sat_name,
                    "adm": b_not.adm,
                    "operator": b_not.operator,
                    "br_ific_no": b_not.br_ific_no,
                    "special_sec": b_not.special_sec,
                    "diff_type": "SUPPRESSED",
                    "diff_label": "ĐÃ ĐÌNH CHỈ / RÚT HỒ SƠ",
                    "reason": "Hồ sơ không còn xuất hiện trong ấn phẩm công báo kỳ này",
                })

        return {
            "status": "success",
            "base_label": base_label,
            "target_label": target_label,
            "comparison_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_base_filings": len(base_notices),
                "total_target_filings": len(target_notices),
                "new_count": len(new_filings),
                "modified_count": len(modified_filings),
                "suppressed_count": len(suppressed_filings),
                "unchanged_count": len(unchanged_filings),
                "vietnam_risk_count": len(vietnam_risk_filings),
            },
            "new_filings": new_filings,
            "modified_filings": modified_filings,
            "suppressed_filings": suppressed_filings,
            "vietnam_risk_filings": vietnam_risk_filings,
        }


class BRConnectionManager:
    """Quản lý kết nối trực tiếp (Live Connection) tới CSDL ITU BR IFIC."""

    _instance: Optional[BRConnectionManager] = None

    def __init__(self):
        self.status = "DISCONNECTED"  # DISCONNECTED, READY_TO_CONNECT, CONNECTED, ERROR
        self.active_path: Optional[str] = None
        self.db_type: Optional[str] = None
        self.latest_edition: int = 3015
        self.tables: List[str] = []
        self.total_records: int = 0
        self.cached_notices: List[BRNoticeRecord] = []
        self.last_connected_at: Optional[str] = None

        # Tự động nạp CSDL tham chiếu mặc định nếu có
        self._auto_init_default()

    @classmethod
    def get_instance(cls) -> BRConnectionManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _auto_init_default(self) -> None:
        """Khởi tạo với CSDL mẫu mặc định."""
        default_sqlite = REFERENCE_DIR / "srs_br_ific_3015.sqlite"
        if default_sqlite.exists():
            self.connect(default_sqlite)
        else:
            # Tạo CSDL mẫu mặc định nếu chưa tồn tại
            self.status = "READY_TO_CONNECT"

    def connect(self, db_path_or_str: str | Path) -> Dict[str, Any]:
        """Thực hiện kết nối tới file CSDL hoặc chuỗi kết nối."""
        conn = BRDatabaseConnector(db_path_or_str)
        t_res = conn.test_connection()
        if t_res.get("connected"):
            self.status = "CONNECTED"
            self.active_path = str(db_path_or_str)
            self.db_type = t_res.get("db_type")
            self.latest_edition = t_res.get("latest_ific_edition", 3015)
            self.tables = t_res.get("tables", [])
            self.total_records = t_res.get("record_count", 0)
            self.cached_notices = conn.fetch_notices()
            self.last_connected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {
                "status": "success",
                "connected": True,
                "message": t_res.get("message"),
                "db_type": self.db_type,
                "active_path": self.active_path,
                "edition": self.latest_edition,
                "table_count": len(self.tables),
                "total_records": len(self.cached_notices),
            }
        else:
            self.status = "ERROR"
            return {
                "status": "error",
                "connected": False,
                "message": t_res.get("message", "Lỗi kết nối CSDL"),
                "error": t_res.get("error"),
            }

    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái kết nối trực tiếp hiện thời."""
        return {
            "status": self.status,
            "ready_state": "SẴN SÀNG KẾT NỐI (READY)" if self.status in ["READY_TO_CONNECT", "CONNECTED"] else "CHƯA KẾT NỐI",
            "active_path": self.active_path or "Chưa cấu hình (Đang ở chế độ sẵn sàng)",
            "db_type": self.db_type or "SQLite / Access MDB",
            "latest_edition": self.latest_edition,
            "total_notices": len(self.cached_notices),
            "tables": self.tables,
            "last_connected_at": self.last_connected_at,
            "supports_mdb": True,
            "supports_sqlite": True,
        }

    def get_filings(self) -> List[Appendix4Filing]:
        """Chuyển đổi toàn bộ hồ sơ đang kết nối sang dạng Appendix4Filing."""
        return [n.to_filing() for n in self.cached_notices]


def parse_mdb_or_sqlite_file(file_path: Path | str, original_filename: Optional[str] = None) -> List[Appendix4Filing]:
    """
    Bóc tách tệp .mdb hoặc .sqlite/.db được tải lên, trích xuất tất cả hồ sơ Phụ lục 4,
    lưu vào bộ nhớ và thư mục filings để Hội đồng AI có thể thẩm định ngay lập tức.
    """
    file_path = Path(file_path)
    filename = original_filename or file_path.name

    connector = BRDatabaseConnector(file_path)
    test_res = connector.test_connection()
    if not test_res.get("connected"):
        raise ValueError(f"Không thể đọc cơ sở dữ liệu '{filename}': {test_res.get('message')}")

    notices = connector.fetch_notices()
    if not notices:
        raise ValueError(f"Tệp CSDL '{filename}' hợp lệ nhưng không tìm thấy bản ghi hồ sơ vệ tinh nào trong bảng notices.")

    filings: List[Appendix4Filing] = []
    for n in notices:
        f = n.to_filing()
        f.service_area["is_user_uploaded"] = True
        f.service_area["source_filename"] = filename
        f.service_area["database_type"] = test_res.get("db_type")
        # Lưu vào danh sách uploaded để có thể chọn từ giao diện
        save_uploaded_filing(f)
        filings.append(f)

    # Cập nhật kết nối nếu thành công
    mgr = BRConnectionManager.get_instance()
    mgr.connect(file_path)

    return filings


# ================= HÀM TIỆN ÍCH TẠO CSDL MẪU CHUẨN =================

def ensure_sample_reference_databases() -> Tuple[Path, Path]:
    """
    Tạo hai tệp SQLite mẫu chuẩn mô phỏng số công báo BR IFIC 3014 và 3015
    để hệ thống có thể chạy ngay tính năng Diff Engine và Sẵn sàng kết nối.
    """
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    db_3014 = REFERENCE_DIR / "srs_br_ific_3014.sqlite"
    db_3015 = REFERENCE_DIR / "srs_br_ific_3015.sqlite"

    # 1. CSDL BR IFIC 3014 (Kỳ trước)
    conn14 = sqlite3.connect(db_3014)
    cur14 = conn14.cursor()
    cur14.execute("DROP TABLE IF EXISTS notices;")
    cur14.execute("""
    CREATE TABLE notices (
        ntc_id INTEGER PRIMARY KEY,
        sat_name TEXT,
        adm TEXT,
        operator TEXT,
        br_ific_no INTEGER,
        special_sec TEXT,
        ntc_type TEXT,
        act_code TEXT,
        d_adm TEXT,
        filing_type TEXT,
        alt_km REAL,
        incl_deg REAL,
        total_satellites INTEGER,
        num_planes INTEGER,
        sats_per_plane INTEGER,
        freq_min_ghz REAL,
        freq_max_ghz REAL,
        band_name TEXT,
        vietnam_covered INTEGER,
        closest_approach_to_vinasat_deg REAL,
        inside_coordination_arc_6deg INTEGER
    );
    """)

    notices_3014 = [
        (1, "USASAT-NGSO-3", "USA", "SpaceX Corp", 3014, "CR/C/5920", "CR/C", "A", "2024-01-15", "NON-GSO FSS", 550.0, 53.0, 1584, 72, 22, 10.7, 12.75, "Ku-band Downlink", 1, 1.8, 1),
        (2, "KORSAT-NGSO-KA", "KOR", "KT SAT Corp", 3014, "CR/C/5921", "CR/C", "A", "2024-01-15", "NON-GSO FSS", 1200.0, 85.0, 32, 4, 8, 18.1, 20.2, "Ka-band Downlink", 0, 14.5, 0),
        (3, "CHNSAT-NGSO-1", "CHN", "China Satellite Network Group", 3014, "CR/C/5922", "CR/C", "A", "2024-01-15", "NON-GSO FSS", 508.0, 86.5, 1200, 48, 25, 10.7, 12.75, "Ku-band Downlink", 1, 2.5, 1),
        (4, "F-SAT-LEO", "F", "Eutelsat Group", 3014, "CR/C/5923", "CR/C", "A", "2024-01-15", "NON-GSO FSS", 1200.0, 87.9, 648, 18, 36, 10.7, 12.75, "Ku-band Downlink", 1, 3.2, 1),
    ]
    cur14.executemany("INSERT INTO notices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", notices_3014)
    conn14.commit()
    conn14.close()

    # 2. CSDL BR IFIC 3015 (Kỳ mới nhất: Starlink MOD tăng vệ tinh, Kuiper MỚI xuất hiện, KORSAT giữ nguyên)
    conn15 = sqlite3.connect(db_3015)
    cur15 = conn15.cursor()
    cur15.execute("DROP TABLE IF EXISTS notices;")
    cur15.execute("""
    CREATE TABLE notices (
        ntc_id INTEGER PRIMARY KEY,
        sat_name TEXT,
        adm TEXT,
        operator TEXT,
        br_ific_no INTEGER,
        special_sec TEXT,
        ntc_type TEXT,
        act_code TEXT,
        d_adm TEXT,
        filing_type TEXT,
        alt_km REAL,
        incl_deg REAL,
        total_satellites INTEGER,
        num_planes INTEGER,
        sats_per_plane INTEGER,
        freq_min_ghz REAL,
        freq_max_ghz REAL,
        band_name TEXT,
        vietnam_covered INTEGER,
        closest_approach_to_vinasat_deg REAL,
        inside_coordination_arc_6deg INTEGER
    );
    """)

    notices_3015 = [
        # Hồ sơ MOD: USASAT-NGSO-3 sửa đổi tăng quy mô lên 4,408 vệ tinh theo Table 27 ITU Handbook
        (1, "USASAT-NGSO-3", "USA", "SpaceX Corp", 3015, "CR/C/5920/M1", "CR/C", "M", "2024-02-01", "NON-GSO FSS", 550.0, 53.0, 4408, 72, 61, 10.7, 12.75, "Ku-band Downlink", 1, 1.8, 1),
        # Giữ nguyên: KORSAT-NGSO-KA
        (2, "KORSAT-NGSO-KA", "KOR", "KT SAT Corp", 3015, "CR/C/5921", "CR/C", "A", "2024-01-15", "NON-GSO FSS", 1200.0, 85.0, 32, 4, 8, 18.1, 20.2, "Ka-band Downlink", 0, 14.5, 0),
        # Hồ sơ MOD: CHNSAT-NGSO-1 mở rộng thêm dải tần Ka Gateway
        (3, "CHNSAT-NGSO-1", "CHN", "China Satellite Network Group", 3015, "CR/C/5922/M1", "CR/C", "M", "2024-02-01", "NON-GSO FSS", 508.0, 86.5, 1200, 48, 25, 17.7, 19.7, "Ka-band Gateway Downlink", 1, 2.5, 1),
        # Hồ sơ MỚI: KUIPER-NGSO-V (Amazon Kuiper nộp mới 3,236 vệ tinh chiếu sóng xuống VN)
        (5, "KUIPER-NGSO-V", "USA", "Amazon Kuiper Systems LLC", 3015, "CR/C/6145", "CR/C", "A", "2024-02-01", "NON-GSO FSS", 630.0, 51.9, 3236, 34, 95, 17.7, 20.2, "Ka-band Gateway & User", 1, 1.5, 1),
        # Hồ sơ MỚI: JILIN-1-OPT (Vệ tinh viễn thám nhỏ Trung Quốc SSO 535km)
        (6, "JILIN-1-OPT", "CHN", "Chang Guang Satellite Tech", 3015, "API/A/1420", "API/A", "A", "2024-02-01", "NON-GSO EESS", 535.0, 97.5, 138, 12, 12, 8.025, 8.4, "X-band Earth Exploration", 1, 5.2, 1),
    ]
    cur15.executemany("INSERT INTO notices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", notices_3015)
    conn15.commit()
    conn15.close()

    return db_3014, db_3015
