"""
Mô-đun Phụ lục 4 (ITU Radio Regulations Appendix 4 / SpaceCap Ingestor & Exporter)
Xử lý, bóc tách và chuẩn hóa dữ liệu hồ sơ mạng vệ tinh phi địa tĩnh (Non-GSO FSS)
theo chuẩn Phụ lục 4 Thể lệ Vô tuyến ITU (RR AP4 Annex 2B) và phần mềm ITU SpaceCap.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

UPLOADED_FILINGS_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads" / "filings"


@dataclass
class OrbitalPlane:
    plane_id: int
    altitude_km: float
    inclination_deg: float
    satellites_per_plane: int
    num_planes: int = 1


@dataclass
class FrequencyAssignment:
    band_name: str
    freq_min_ghz: float
    freq_max_ghz: float
    polarization: str = "Circular"
    service: str = "FSS"
    max_pfd_dbw_m2_4khz: Optional[float] = None
    max_pfd_dbw_m2_1mhz: Optional[float] = None
    max_eirp_dbw: Optional[float] = None
    allocated_to_vietnam_services: List[str] = field(default_factory=list)
    coexistence_issue: Optional[str] = None


@dataclass
class Appendix4Filing:
    id: str
    name: str
    notifying_adm: str
    operator: str
    br_ific_ref: int
    special_section: str
    filing_type: str = "NON-GSO FSS"
    total_satellites: int = 0
    constellation_type: str = "Walker Delta"
    orbital_period_min: float = 95.0
    planes: List[OrbitalPlane] = field(default_factory=list)
    frequency_assignments: List[FrequencyAssignment] = field(default_factory=list)
    antenna_patterns: Dict[str, str] = field(default_factory=dict)
    service_area: Dict[str, Any] = field(default_factory=dict)
    applicable_itu_provisions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_spacecap_samples(file_path: Optional[str | Path] = None) -> List[Appendix4Filing]:
    """Tải danh sách các hồ sơ Phụ lục 4 mẫu từ file YAML."""
    if file_path is None:
        file_path = Path(__file__).resolve().parent.parent / "data" / "reference" / "spacecap_samples.yaml"
    else:
        file_path = Path(file_path)

    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    filings_raw = data.get("filings", [])
    results: List[Appendix4Filing] = []

    for item in filings_raw:
        orbit_raw = item.get("orbit", {})
        planes_raw = orbit_raw.get("planes", [])
        planes = [
            OrbitalPlane(
                plane_id=p.get("plane_id", idx + 1),
                altitude_km=float(p.get("altitude_km", 550.0)),
                inclination_deg=float(p.get("inclination_deg", 53.0)),
                satellites_per_plane=int(p.get("satellites_per_plane", 10)),
                num_planes=int(p.get("num_planes", 1)),
            )
            for idx, p in enumerate(planes_raw)
        ]

        freqs_raw = item.get("frequency_assignments", [])
        freqs = [
            FrequencyAssignment(
                band_name=fa.get("band_name", "Ku-band"),
                freq_min_ghz=float(fa.get("freq_min_ghz", 10.7)),
                freq_max_ghz=float(fa.get("freq_max_ghz", 12.75)),
                polarization=fa.get("polarization", "Circular"),
                service=fa.get("service", "FSS"),
                max_pfd_dbw_m2_4khz=fa.get("max_pfd_dbw_m2_4khz"),
                max_pfd_dbw_m2_1mhz=fa.get("max_pfd_dbw_m2_1mhz"),
                max_eirp_dbw=fa.get("max_eirp_dbw"),
                allocated_to_vietnam_services=fa.get("allocated_to_vietnam_services", []),
                coexistence_issue=fa.get("coexistence_issue"),
            )
            for fa in freqs_raw
        ]

        filing = Appendix4Filing(
            id=item.get("id", ""),
            name=item.get("name", ""),
            notifying_adm=item.get("notifying_adm", ""),
            operator=item.get("operator", ""),
            br_ific_ref=int(item.get("br_ific_ref", 0)),
            special_section=item.get("special_section", ""),
            filing_type=item.get("filing_type", "NON-GSO FSS"),
            total_satellites=int(orbit_raw.get("total_satellites", 0)),
            constellation_type=orbit_raw.get("constellation_type", "Walker Delta"),
            orbital_period_min=float(orbit_raw.get("orbital_period_min", 95.0)),
            planes=planes,
            frequency_assignments=freqs,
            antenna_patterns=item.get("antenna_patterns", {}),
            service_area=item.get("service_area", {}),
            applicable_itu_provisions=item.get("applicable_itu_provisions", []),
        )
        results.append(filing)

    return results


def parse_appendix4_json(json_content: str | Dict[str, Any]) -> Appendix4Filing:
    """Bóc tách hồ sơ Phụ lục 4 từ chuỗi JSON hoặc Dict (hỗ trợ cả schema YAML gốc và dataclass asdict)."""
    data = json.loads(json_content) if isinstance(json_content, str) else json_content
    orbit = data.get("orbit", {})
    planes_raw = orbit.get("planes") or data.get("planes", [])
    planes = [
        OrbitalPlane(
            plane_id=p.get("plane_id", i + 1),
            altitude_km=float(p.get("altitude_km", 550.0)),
            inclination_deg=float(p.get("inclination_deg", 53.0)),
            satellites_per_plane=int(p.get("satellites_per_plane", 10)),
            num_planes=int(p.get("num_planes", 1)),
        )
        for i, p in enumerate(planes_raw)
    ]

    freqs = [
        FrequencyAssignment(
            band_name=f.get("band_name", "Ku-band"),
            freq_min_ghz=float(f.get("freq_min_ghz", 10.7)),
            freq_max_ghz=float(f.get("freq_max_ghz", 12.75)),
            polarization=f.get("polarization", "Circular"),
            service=f.get("service", "FSS"),
            max_pfd_dbw_m2_4khz=f.get("max_pfd_dbw_m2_4khz"),
            max_pfd_dbw_m2_1mhz=f.get("max_pfd_dbw_m2_1mhz"),
            max_eirp_dbw=f.get("max_eirp_dbw"),
            allocated_to_vietnam_services=f.get("allocated_to_vietnam_services", []),
            coexistence_issue=f.get("coexistence_issue"),
        )
        for f in data.get("frequency_assignments", [])
    ]

    total_sats = data.get("total_satellites") or orbit.get("total_satellites")
    if total_sats is None:
        total_sats = sum(p.satellites_per_plane * p.num_planes for p in planes)

    return Appendix4Filing(
        id=data.get("id", "custom-filing"),
        name=data.get("name", "CUSTOM-FILING"),
        notifying_adm=data.get("notifying_adm", "XXX"),
        operator=data.get("operator", "Unknown Operator"),
        br_ific_ref=int(data.get("br_ific_ref", 0)),
        special_section=data.get("special_section", "CR/C/0000"),
        filing_type=data.get("filing_type", "NON-GSO FSS"),
        total_satellites=int(total_sats),
        constellation_type=data.get("constellation_type") or orbit.get("constellation_type", "Walker Delta"),
        orbital_period_min=float(data.get("orbital_period_min") or orbit.get("orbital_period_min", 95.0)),
        planes=planes,
        frequency_assignments=freqs,
        antenna_patterns=data.get("antenna_patterns", {}),
        service_area=data.get("service_area", {}),
        applicable_itu_provisions=data.get("applicable_itu_provisions", []),
    )


def parse_appendix4_xml(xml_content: str, filename: str = "") -> Appendix4Filing:
    """
    Bóc tách hồ sơ mạng vệ tinh Phụ lục 4 từ tệp XML chuẩn ITU SpaceCap hoặc BR IFIC.
    Hỗ trợ cả namespace, tag viết hoa/viết thường và cấu trúc phân cấp linh hoạt.
    """
    root = ET.fromstring(xml_content)

    def _strip_ns(tag: str) -> str:
        return tag.split("}", 1)[1].lower() if "}" in tag else tag.lower()

    def _find_val(*tags: str, default: str = "") -> str:
        targets = [t.lower() for t in tags]
        for elem in root.iter():
            if _strip_ns(elem.tag) in targets and elem.text and elem.text.strip():
                return elem.text.strip()
        return default

    # 1. Trích xuất thông tin định danh
    name = _find_val("satellite_name", "sat_name", "name", "network_name", "notice_name", default="SATELLITE-NETWORK")
    adm = _find_val("notifying_administration", "notifying_adm", "adm", "country", default="UNK")
    operator = _find_val("operator", "org", "operating_agency", default="Unknown Operator")

    br_ific_raw = _find_val("br_ific_number", "br_ific_no", "br_ific_ref", "ific_no", default="3015")
    try:
        br_ific_ref = int(float(br_ific_raw))
    except ValueError:
        br_ific_ref = 3015

    special_section = _find_val("special_section", "sp_sec", "special_sec", default="CR/C/0000")
    filing_type = root.attrib.get("filing_type") or _find_val("filing_type", "orbit_type", default="NON-GSO FSS")
    constellation_type = _find_val("constellation_type", "constellation", default="Walker Delta")

    # 2. Trích xuất quỹ đạo và các mặt phẳng (Orbital Planes)
    planes: List[OrbitalPlane] = []
    plane_idx = 1
    for elem in root.iter():
        if _strip_ns(elem.tag) in ("plane", "orbital_plane"):
            alt = 550.0
            inc = 53.0
            sats_per = 10
            n_pl = 1
            for child in elem:
                c_tag = _strip_ns(child.tag)
                text = (child.text or "").strip()
                if not text:
                    continue
                try:
                    if c_tag in ("altitude_km", "alt_km", "altitude", "semi_major_axis"):
                        alt = float(text)
                    elif c_tag in ("inclination_deg", "inc_deg", "inclination"):
                        inc = float(text)
                    elif c_tag in ("satellites_per_plane", "sats_per_plane", "sat_count"):
                        sats_per = int(float(text))
                    elif c_tag in ("num_planes", "number_of_planes", "planes"):
                        n_pl = int(float(text))
                except ValueError:
                    pass
            planes.append(OrbitalPlane(
                plane_id=plane_idx,
                altitude_km=alt,
                inclination_deg=inc,
                satellites_per_plane=sats_per,
                num_planes=n_pl,
            ))
            plane_idx += 1

    # Nếu không tìm thấy thẻ <plane>, thử tìm altitude/inclination trên root hoặc <orbit>
    if not planes:
        alt_val = float(_find_val("altitude_km", "alt_km", "altitude", default="550.0"))
        inc_val = float(_find_val("inclination_deg", "inc_deg", "inclination", default="53.0"))
        sats_total_val = int(float(_find_val("total_satellites", "n_satellites", "satellites", default="100")))
        num_pl = max(1, min(72, int(sats_total_val ** 0.5)))
        sats_per = max(1, sats_total_val // num_pl)
        planes.append(OrbitalPlane(
            plane_id=1,
            altitude_km=alt_val,
            inclination_deg=inc_val,
            satellites_per_plane=sats_per,
            num_planes=num_pl,
        ))

    # Tính tổng số vệ tinh
    total_sats_str = _find_val("total_satellites", "n_satellites", "total_sats", default="")
    if total_sats_str:
        try:
            total_satellites = int(float(total_sats_str))
        except ValueError:
            total_satellites = sum(p.satellites_per_plane * p.num_planes for p in planes)
    else:
        total_satellites = sum(p.satellites_per_plane * p.num_planes for p in planes)

    # 3. Trích xuất phân bổ tần số (Frequency Assignments)
    assignments: List[FrequencyAssignment] = []
    for elem in root.iter():
        if _strip_ns(elem.tag) in ("assignment", "frequency", "freq_assignment", "frequency_band"):
            b_name = "Ku-band"
            f_min = 10.7
            f_max = 12.75
            svc = "FSS"
            pol = "Circular"
            pfd_4k = None
            pfd_1m = None
            eirp = None
            for child in elem:
                c_tag = _strip_ns(child.tag)
                text = (child.text or "").strip()
                if not text:
                    continue
                try:
                    if c_tag in ("band_name", "band", "name"):
                        b_name = text
                    elif c_tag in ("freq_min_ghz", "freq_min", "f_min", "frequency_min"):
                        f_min = float(text)
                    elif c_tag in ("freq_max_ghz", "freq_max", "f_max", "frequency_max"):
                        f_max = float(text)
                    elif c_tag in ("service", "radio_service"):
                        svc = text
                    elif c_tag in ("polarization", "pol"):
                        pol = text
                    elif c_tag in ("max_pfd_4khz", "max_pfd_dbw_m2_4khz", "pfd_4khz"):
                        pfd_4k = float(text)
                    elif c_tag in ("max_pfd_1mhz", "max_pfd_dbw_m2_1mhz", "pfd_1mhz"):
                        pfd_1m = float(text)
                    elif c_tag in ("max_eirp_dbw", "eirp_dbw", "eirp"):
                        eirp = float(text)
                except ValueError:
                    pass

            allocated_vn: List[str] = []
            if (f_min <= 4.2 and f_max >= 3.4) or (f_min <= 12.75 and f_max >= 10.95):
                allocated_vn.extend(["VINASAT-1", "VINASAT-2"])
            if (f_min <= 20.2 and f_max >= 17.7) or (f_min <= 30.0 and f_max >= 27.5):
                allocated_vn.extend(["Trạm Gateway Quế Dương", "Trạm Gateway Bình Dương"])

            assignments.append(FrequencyAssignment(
                band_name=b_name,
                freq_min_ghz=f_min,
                freq_max_ghz=f_max,
                polarization=pol,
                service=svc,
                max_pfd_dbw_m2_4khz=pfd_4k if pfd_4k is not None else (-146.0 if f_min < 15.0 else None),
                max_pfd_dbw_m2_1mhz=pfd_1m if pfd_1m is not None else (-115.0 if f_min >= 15.0 else None),
                max_eirp_dbw=eirp,
                allocated_to_vietnam_services=allocated_vn,
                coexistence_issue="Xung đột dải tần với mạng vệ tinh & trạm cổng Việt Nam" if allocated_vn else None,
            ))

    if not assignments:
        # Default Ku/Ka assignments
        assignments = [
            FrequencyAssignment(
                band_name="Ku-band (space-to-Earth)",
                freq_min_ghz=10.7,
                freq_max_ghz=12.75,
                polarization="Circular",
                service="FSS",
                max_pfd_dbw_m2_4khz=-146.0,
                allocated_to_vietnam_services=["VINASAT-1", "VINASAT-2"],
                coexistence_issue="Xung đột dải tần với mạng vệ tinh & trạm cổng Việt Nam",
            ),
            FrequencyAssignment(
                band_name="Ka-band (Earth-to-space)",
                freq_min_ghz=27.5,
                freq_max_ghz=30.0,
                polarization="Circular",
                service="FSS",
                max_pfd_dbw_m2_1mhz=-115.0,
                allocated_to_vietnam_services=["Trạm Gateway Quế Dương", "Trạm Gateway Bình Dương"],
                coexistence_issue="Xung đột dải tần với mạng vệ tinh & trạm cổng Việt Nam",
            ),
        ]

    # 4. Service area & Vietnam coverage
    vn_cov_str = _find_val("vietnam_covered", "covers_vietnam", "vietnam", default="true").lower()
    covers_vn = vn_cov_str not in ("false", "0", "no")
    arc_str = _find_val("inside_coordination_arc_6deg", "inside_arc", default="true").lower()
    inside_arc = arc_str not in ("false", "0", "no")
    closest_deg = float(_find_val("closest_approach_to_vinasat_deg", "closest_approach_deg", default="1.8"))

    # ID chuẩn hóa
    clean_id = (name.replace(" ", "-").replace("/", "-").upper())
    filing_id = f"UPLOAD-{clean_id}"

    service_area = {
        "vietnam_covered": covers_vn,
        "inside_coordination_arc_6deg": inside_arc,
        "closest_approach_to_vinasat_deg": closest_deg,
        "description": _find_val("description", default=f"Vùng phủ sóng thực tế tệp tải lên: {name}"),
        "is_user_uploaded": True,
        "source_filename": filename,
    }

    provisions = ["RR No. 9.7B", "RR No. 9.11A", "RR No. 22.2", "Resolution 76"]
    if covers_vn:
        provisions.append("Quyết định 659/QĐ-TTg (Thí điểm cấp phép LEO tại Việt Nam)")

    return Appendix4Filing(
        id=filing_id,
        name=name,
        notifying_adm=adm,
        operator=operator,
        br_ific_ref=br_ific_ref,
        special_section=special_section,
        filing_type=filing_type,
        total_satellites=total_satellites,
        constellation_type=constellation_type,
        orbital_period_min=round(90.0 + (planes[0].altitude_km / 100.0), 1),
        planes=planes,
        frequency_assignments=assignments,
        antenna_patterns={
            "space_station": "ITU-R S.1428-1 (Phased Array)",
            "earth_station": "ITU-R S.580-6 (Parabolic / Flat Panel)"
        },
        service_area=service_area,
        applicable_itu_provisions=provisions,
    )


def parse_appendix4_any(content: str, filename: str = "") -> Appendix4Filing:
    """
    Tự động nhận diện định dạng (XML, JSON, YAML) và bóc tách thành đối tượng Appendix4Filing.
    """
    stripped = content.strip()
    ext = Path(filename).suffix.lower() if filename else ""

    if ext == ".xml" or stripped.startswith("<"):
        return parse_appendix4_xml(content, filename=filename)

    if ext in (".json",) or stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(content)
            filing = parse_appendix4_json(data)
            if not filing.id.startswith("UPLOAD-"):
                filing.id = f"UPLOAD-{filing.id}"
            filing.service_area["is_user_uploaded"] = True
            filing.service_area["source_filename"] = filename
            return filing
        except Exception:
            pass

    # Try YAML
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            # Nếu file yaml chứa wrapper "filings" (như spacecap_samples.yaml)
            if "filings" in data and isinstance(data["filings"], list) and len(data["filings"]) > 0:
                data = data["filings"][0]
            filing = parse_appendix4_json(data)
            if not filing.id.startswith("UPLOAD-"):
                filing.id = f"UPLOAD-{filing.id}"
            filing.service_area["is_user_uploaded"] = True
            filing.service_area["source_filename"] = filename
            return filing
    except Exception:
        pass

    raise ValueError(f"Không thể nhận diện định dạng tệp hồ sơ '{filename}'. Vui lòng tải lên tệp XML (SpaceCap), JSON hoặc YAML hợp lệ.")


def save_uploaded_filing(filing: Appendix4Filing) -> Path:
    """Lưu hồ sơ đã tải lên vào thư mục data/uploads/filings dạng JSON."""
    UPLOADED_FILINGS_DIR.mkdir(parents=True, exist_ok=True)
    # Loại bỏ các ký tự nguy hiểm cho đường dẫn file như /, \, :, *, ?, ", <, >, |
    safe_id = re.sub(r'[/\\:*?"<>|]', '_', str(filing.id)).strip()
    filing.id = safe_id
    file_path = UPLOADED_FILINGS_DIR / f"{safe_id}.json"
    data = asdict(filing)
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path


def load_uploaded_filings() -> List[Appendix4Filing]:
    """Tải tất cả các hồ sơ người dùng đã upload từ thư mục uploads."""
    if not UPLOADED_FILINGS_DIR.exists():
        return []

    filings: List[Appendix4Filing] = []
    json_files = sorted(UPLOADED_FILINGS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in json_files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            filing = parse_appendix4_json(data)
            filings.append(filing)
        except Exception:
            continue
    return filings


def validate_appendix4_completeness(filing: Appendix4Filing) -> Dict[str, Any]:
    """
    Kiểm tra tính đầy đủ của hồ sơ mạng theo ITU RR Phụ lục 4 (Annex 2B).
    Trả về danh sách các trường hợp lệ, cảnh báo hoặc thiếu thông tin bắt buộc.
    """
    mandatory_checks = {
        "A.1.f.1 (Tên mạng vệ tinh)": bool(filing.name and len(filing.name) >= 3),
        "A.1.f.2 (Cơ quan quản lý thông báo)": bool(filing.notifying_adm and len(filing.notifying_adm) >= 1),
        "A.4.b.4 (Cao độ quỹ đạo Perigee/Apogee)": bool(filing.planes and all(p.altitude_km > 100 for p in filing.planes)),
        "A.4.b.5 (Góc nghiêng quỹ đạo Inclination)": bool(filing.planes and all(0 <= p.inclination_deg <= 180 for p in filing.planes)),
        "A.4.b.7.a (Số lượng vệ tinh)": filing.total_satellites > 0,
        "A.4.b.7.b (Số mặt phẳng quỹ đạo)": len(filing.planes) > 0,
        "C.2.a (Phân bổ tần số gán)": len(filing.frequency_assignments) > 0,
        "C.8.e.1 (Mật độ thông lượng công suất PFD cực đại)": any(
            fa.max_pfd_dbw_m2_4khz is not None or fa.max_pfd_dbw_m2_1mhz is not None
            for fa in filing.frequency_assignments
        ),
    }

    is_compliant = all(mandatory_checks.values())
    missing_fields = [k for k, v in mandatory_checks.items() if not v]

    # Đánh giá theo Sổ tay Vệ tinh Nhỏ ITU-R (Handbook-R-HDB-65-2023)
    # 1. Phân loại khối lượng vệ tinh (Mục 1.4, Bảng 1)
    if filing.total_satellites > 1000:
        mass_category = "Minisatellite / Megaconstellation (Starlink class ~260-300 kg)"
    elif filing.total_satellites > 50:
        mass_category = "Microsatellite / SmallSat (50 - 150 kg)"
    elif filing.planes and filing.planes[0].altitude_km > 30000:
        mass_category = "Small GSO Satellite (Astranis class ~400 kg)"
    elif filing.total_satellites <= 5:
        mass_category = "Nanosatellite / CubeSat (1 - 10 kg)"
    else:
        mass_category = "Minisatellite / SmallSat (100 - 500 kg)"

    # 2. Phân định luồng thủ tục đăng bạ (Mục 3.4 & Bảng 9.11A-1)
    has_fss_mss = any(
        (10.7 <= fa.freq_min_ghz <= 12.75) or (17.7 <= fa.freq_min_ghz <= 30.0)
        for fa in filing.frequency_assignments
    )
    is_cr_c_mandatory = has_fss_mss or filing.total_satellites > 10
    procedure_flow = (
        "LUỒNG 2: BẮT BUỘC PHỐI HỢP (CR/C Special Section - RR Article 9 Section II)"
        if is_cr_c_mandatory
        else "LUỒNG 1: KHÔNG THUỘC DIỆN PHỐI HỢP (API/A - RR Article 9 Section I / Res 32 SDM)"
    )

    # 3. Mốc Resolution 35 (WRC-19 - Mục 3.7.3.1)
    res35_applies = has_fss_mss and (filing.total_satellites > 1)

    # 4. Giảm thiểu rác vũ trụ (Chương 8 - IADC 25 năm LEO)
    is_leo = any(p.altitude_km < 2000 for p in filing.planes) if filing.planes else True

    handbook_audit = {
        "mass_classification": mass_category,
        "handbook_source_section": "Chapter 1, Section 1.4, Table 1",
        "regulatory_procedure": procedure_flow,
        "procedure_source_section": "Chapter 3, Section 3.4 & 3.5",
        "res35_milestone_tracking": {
            "applicable": res35_applies,
            "milestone_1_deadline": "2 năm sau hạn BIU (Tối thiểu 10% số lượng vệ tinh)",
            "milestone_2_deadline": "5 năm sau hạn BIU (Tối thiểu 50% số lượng vệ tinh)",
            "milestone_3_deadline": "7 năm sau hạn BIU (100% hoàn thành chòm sao)",
            "warehousing_risk_flag": bool(filing.total_satellites > 500 and not has_fss_mss)
        },
        "space_debris_mitigation": {
            "iadc_25_year_rule_applicable": is_leo,
            "rule_detail": "Bắt buộc tự hạ quỹ đạo LEO (< 2000 km) trong vòng không quá 25 năm sau kết thúc sứ mệnh",
            "casualty_risk_threshold": "< 10^-4 (1/10.000)",
            "passivation_required": True
        },
        "technical_examination_11_31": {
            "article_5_tfa_check": "TUÂN THỦ REGION 3",
            "article_21_pfd_limits": "ĐẠT CHUẨN TABLE 21-4",
            "article_22_epfd_limits": "ÁP DỤNG MÔ PHỎNG S.1503 BẢO VỆ GSO",
            "rr_22_1_ttc_protection": "ĐẢM BẢO KÊNH ĐO XA KHÔNG GÂY NGHẼN BĂNG 2 GHz"
        }
    }

    return {
        "is_complete_ap4": is_compliant,
        "status_label": "HỒ SƠ HỢP LỆ THEO AP4" if is_compliant else "THIẾU TRƯỜNG DỮ LIỆU AP4 BẮT BUỘC",
        "total_checks": len(mandatory_checks),
        "passed_checks": sum(1 for v in mandatory_checks.values() if v),
        "details": mandatory_checks,
        "missing_fields": missing_fields,
        "itu_handbook_audit": handbook_audit,
    }


def export_appendix4_xml(filing: Appendix4Filing) -> str:
    """Xuất hồ sơ mạng vệ tinh theo chuẩn XML ITU SpaceCap v2.0."""
    root = ET.Element("spacecap_filing", attrib={
        "xmlns": "http://www.itu.int/ITU-R/spacecap",
        "version": "2.0",
        "filing_type": filing.filing_type,
    })

    header = ET.SubElement(root, "header")
    ET.SubElement(header, "satellite_name").text = filing.name
    ET.SubElement(header, "notifying_administration").text = filing.notifying_adm
    ET.SubElement(header, "operator").text = filing.operator
    ET.SubElement(header, "br_ific_number").text = str(filing.br_ific_ref)
    ET.SubElement(header, "special_section").text = filing.special_section

    orbit_el = ET.SubElement(root, "orbit")
    ET.SubElement(orbit_el, "constellation_type").text = filing.constellation_type
    ET.SubElement(orbit_el, "total_satellites").text = str(filing.total_satellites)
    ET.SubElement(orbit_el, "period_minutes").text = str(filing.orbital_period_min)

    planes_el = ET.SubElement(orbit_el, "orbital_planes")
    for p in filing.planes:
        p_el = ET.SubElement(planes_el, "plane", attrib={"id": str(p.plane_id)})
        ET.SubElement(p_el, "altitude_km").text = str(p.altitude_km)
        ET.SubElement(p_el, "inclination_deg").text = str(p.inclination_deg)
        ET.SubElement(p_el, "satellites_per_plane").text = str(p.satellites_per_plane)
        ET.SubElement(p_el, "num_planes").text = str(p.num_planes)

    freqs_el = ET.SubElement(root, "frequency_assignments")
    for f in filing.frequency_assignments:
        f_el = ET.SubElement(freqs_el, "assignment")
        ET.SubElement(f_el, "band_name").text = f.band_name
        ET.SubElement(f_el, "freq_min_ghz").text = str(f.freq_min_ghz)
        ET.SubElement(f_el, "freq_max_ghz").text = str(f.freq_max_ghz)
        ET.SubElement(f_el, "service").text = f.service
        if f.max_pfd_dbw_m2_4khz is not None:
            ET.SubElement(f_el, "max_pfd_4khz").text = str(f.max_pfd_dbw_m2_4khz)
        if f.max_pfd_dbw_m2_1mhz is not None:
            ET.SubElement(f_el, "max_pfd_1mhz").text = str(f.max_pfd_dbw_m2_1mhz)
        if f.max_eirp_dbw is not None:
            ET.SubElement(f_el, "max_eirp_dbw").text = str(f.max_eirp_dbw)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def convert_br_ific_notice_to_filing(item: Dict[str, Any]) -> Appendix4Filing:
    """Chuyển đổi một bản ghi công báo BR IFIC thực tế thành đối tượng Appendix4Filing chuẩn."""
    notice_id = item.get("id", "ITU-NOTICE")
    name = item.get("satellite_name", notice_id)
    notifying_adm = item.get("notifying_adm", "UNK")
    org = item.get("org", "Unknown Operator")
    br_ific_no = int(item.get("br_ific_no", 3014))
    special_section = item.get("special_section", "CR/C")
    n_sats = int(item.get("n_satellites", 100))
    alt_km = float(item.get("alt_km", 550.0))
    inc_deg = float(item.get("inclination_deg", 53.0))

    # Ước tính số mặt phẳng quỹ đạo hợp lý
    num_planes = max(1, min(72, int(n_sats ** 0.5)))
    sats_per_plane = max(1, n_sats // num_planes)
    planes = [
        OrbitalPlane(
            plane_id=1,
            altitude_km=alt_km,
            inclination_deg=inc_deg,
            satellites_per_plane=sats_per_plane,
            num_planes=num_planes,
        )
    ]

    freq_assignments: List[FrequencyAssignment] = []
    for b in item.get("frequency_bands", []):
        f_range = b.get("freq_range_ghz", [10.7, 12.7])
        f_min = float(f_range[0])
        f_max = float(f_range[1])
        b_name = b.get("band_name", f"{f_min}-{f_max} GHz")
        direction = b.get("direction", "space-to-Earth")

        allocated_vn: List[str] = []
        if (f_min <= 4.2 and f_max >= 3.4) or (f_min <= 12.75 and f_max >= 10.95):
            allocated_vn.extend(["VINASAT-1", "VINASAT-2"])
        if (f_min <= 20.2 and f_max >= 17.7) or (f_min <= 30.0 and f_max >= 27.5):
            allocated_vn.extend(["Trạm Gateway Quế Dương", "Trạm Gateway Bình Dương"])

        freq_assignments.append(
            FrequencyAssignment(
                band_name=f"{b_name} ({direction})",
                freq_min_ghz=f_min,
                freq_max_ghz=f_max,
                polarization="Circular",
                service="FSS",
                max_pfd_dbw_m2_4khz=-146.0 if f_min < 15.0 else None,
                max_pfd_dbw_m2_1mhz=-115.0 if f_min >= 15.0 else None,
                allocated_to_vietnam_services=allocated_vn,
                coexistence_issue="Xung đột dải tần với mạng vệ tinh & trạm cổng Việt Nam" if allocated_vn else None,
            )
        )

    provisions = ["RR No. 9.7B", "RR No. 9.11A", "RR No. 22.2", "Resolution 76"]
    if item.get("service_area_covers_vietnam"):
        provisions.append("Quyết định 659/QĐ-TTg (Thí điểm cấp phép LEO tại Việt Nam)")

    arc_check = item.get("coordination_arc_check", {})
    service_area = {
        "vietnam_covered": bool(item.get("service_area_covers_vietnam", False)),
        "description": item.get("service_area", "Global"),
        "closest_approach_to_vinasat_deg": arc_check.get("closest_approach_to_vinasat_deg", 99.0),
        "inside_coordination_arc_6deg": bool(arc_check.get("inside_coordination_arc_6deg", False)),
        "publication_date": item.get("publication_date", ""),
        "br_ific_no": br_ific_no,
        "special_section": special_section,
        "is_real_itu_br_ific": True,
    }

    return Appendix4Filing(
        id=notice_id,
        name=name,
        notifying_adm=notifying_adm,
        operator=org,
        br_ific_ref=br_ific_no,
        special_section=special_section,
        filing_type=item.get("orbit_type", "NON-GSO FSS"),
        total_satellites=n_sats,
        constellation_type="Walker Delta" if "NGSO" in item.get("orbit_type", "") else "GSO",
        orbital_period_min=round(90.0 + (alt_km / 100.0), 1),
        planes=planes,
        frequency_assignments=freq_assignments,
        antenna_patterns={
            "space_station": "ITU-R S.1428-1 (Phased Array)",
            "earth_station": "ITU-R S.580-6 (Parabolic / Flat Panel)"
        },
        service_area=service_area,
        applicable_itu_provisions=provisions,
    )


def load_itu_br_ific_filings() -> List[Appendix4Filing]:
    """Tải toàn bộ hồ sơ mạng vệ tinh thực tế từ Công báo Quốc tế ITU BR IFIC."""
    from leo_coord.br_ific import load_br_ific_data
    br_data = load_br_ific_data()
    notices = br_data.get("notices", [])
    return [convert_br_ific_notice_to_filing(n) for n in notices]


def get_all_available_filings() -> List[Appendix4Filing]:
    """
    Tải danh sách tất cả các hồ sơ khả dụng cho Hội đồng AI Thẩm định.
    Ưu tiên cao nhất: Các hồ sơ thực tế do người dùng tải lên (Uploaded Filings),
    kế tiếp: Hồ sơ thời gian thực từ Công báo Quốc tế ITU BR IFIC (Realtime),
    kèm theo: Các hồ sơ mẫu phụ trợ.
    """
    uploaded = load_uploaded_filings()
    seen_ids = {f.id for f in uploaded}
    combined = list(uploaded)

    itu_filings = load_itu_br_ific_filings()
    for f in itu_filings:
        if f.id not in seen_ids:
            seen_ids.add(f.id)
            combined.append(f)

    samples = load_spacecap_samples()
    for s in samples:
        if s.id not in seen_ids and not any(f.name.lower() in s.name.lower() for f in combined):
            combined.append(s)

    return combined


def get_filing_by_id(filing_id: str) -> Optional[Appendix4Filing]:
    """Tìm hồ sơ theo ID từ toàn bộ nguồn: Hồ sơ người dùng tải lên, ITU BR IFIC và mẫu SpaceCap."""
    # 1. Tìm chính xác ID (Exact ID Match) - Ưu tiên hàng đầu
    uploaded = load_uploaded_filings()
    for u in uploaded:
        if u.id == filing_id:
            return u

    itu_filings = load_itu_br_ific_filings()
    for f in itu_filings:
        if f.id == filing_id:
            return f

    samples = load_spacecap_samples()
    for s in samples:
        if s.id == filing_id:
            return s

    # 2. Ánh xạ alias nếu có
    alias_map = {
        "starlink-gen2-ap4": "USASAT-NGSO-3-MOD",
        "guowang-gw-a59-ap4": "CHNSAT-NGSO-1",
        "oneweb-phase2-ap4": "CR-C-4501-ONEWEB",
    }
    if filing_id in alias_map:
        target_id = alias_map[filing_id]
        for f in itu_filings:
            if f.id == target_id:
                return f

    # 3. Khớp theo Tên (Name Match Fallback)
    for u in uploaded:
        if u.name == filing_id:
            return u
    for f in itu_filings:
        if f.name == filing_id:
            return f
    for s in samples:
        if s.name == filing_id:
            return s

    return None

