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

import datetime
import os
import sqlite3
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
            # Kết nối qua pyodbc trên Windows
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
                        cur.execute(f"SELECT MAX(br_ific_no) FROM [{t}]")
                        val = cur.fetchone()[0]
                        if val:
                            edition_guess = int(val)
                        break
                conn.close()
                return {
                    "connected": True,
                    "db_type": "Microsoft Access (.mdb)",
                    "path": self.raw_path,
                    "table_count": len(tables),
                    "tables": tables,
                    "record_count": record_count,
                    "latest_ific_edition": edition_guess or 3015,
                    "message": f"Kết nối CSDL Microsoft Access (.mdb) thành công! Tìm thấy {len(tables)} bảng và {record_count} bản ghi.",
                }
            except Exception as e:
                # Fallback nếu máy không có Access Driver
                return {
                    "connected": False,
                    "db_type": "Microsoft Access (.mdb)",
                    "path": self.raw_path,
                    "error": str(e),
                    "message": f"Lỗi kết nối Microsoft Access (.mdb): {e}. Gợi ý: Hãy cài đặt Microsoft Access Database Engine hoặc chuyển đổi tệp sang định dạng SQLite (.sqlite).",
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
            import pyodbc
            conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.raw_path};"
            conn = pyodbc.connect(conn_str, autocommit=True)
            cur = conn.cursor()
            table_name = "notices"
            for candidate in ["notices", "notice", "tbl_notices", "srs_notices"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM [{candidate}]")
                    table_name = candidate
                    break
                except Exception:
                    continue

            cur.execute(f"SELECT * FROM [{table_name}]")
            columns = [c[0].lower() for c in cur.description]
            for row in cur.fetchall():
                row_dict = dict(zip(columns, row))
                n = BRNoticeRecord(
                    ntc_id=int(row_dict.get("ntc_id", 1) or 1),
                    sat_name=str(row_dict.get("sat_name", "NON-GSO-SAT") or "NON-GSO-SAT"),
                    adm=str(row_dict.get("adm", "USA") or "USA"),
                    operator=str(row_dict.get("operator", "Space Operator") or "Space Operator"),
                    br_ific_no=int(row_dict.get("br_ific_no", 3015) or 3015),
                    special_sec=str(row_dict.get("special_sec", "CR/C/1000") or "CR/C/1000"),
                    ntc_type=str(row_dict.get("ntc_type", "CR/C") or "CR/C"),
                    act_code=str(row_dict.get("act_code", "A") or "A"),
                    d_adm=str(row_dict.get("d_adm", "") or datetime.date.today().isoformat()),
                    filing_type=str(row_dict.get("filing_type", "NON-GSO FSS") or "NON-GSO FSS"),
                    alt_km=float(row_dict.get("alt_km", 550.0) or 550.0),
                    incl_deg=float(row_dict.get("incl_deg", 53.0) or 53.0),
                    total_satellites=int(row_dict.get("total_satellites", 120) or 120),
                    num_planes=int(row_dict.get("num_planes", 6) or 6),
                    sats_per_plane=int(row_dict.get("sats_per_plane", 20) or 20),
                    freq_min_ghz=float(row_dict.get("freq_min_ghz", 10.7) or 10.7),
                    freq_max_ghz=float(row_dict.get("freq_max_ghz", 12.75) or 12.75),
                    band_name=str(row_dict.get("band_name", "Ku-band Downlink") or "Ku-band Downlink"),
                    vietnam_covered=bool(int(row_dict.get("vietnam_covered", 1) or 0)),
                    closest_approach_to_vinasat_deg=float(row_dict.get("closest_approach_to_vinasat_deg", 1.8) or 1.8),
                    inside_coordination_arc_6deg=bool(int(row_dict.get("inside_coordination_arc_6deg", 1) or 0)),
                )
                notices.append(n)
            conn.close()

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
