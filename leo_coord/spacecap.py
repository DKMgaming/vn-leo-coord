"""
Mô-đun Phụ lục 4 (ITU Radio Regulations Appendix 4 / SpaceCap Ingestor & Exporter)
Xử lý, bóc tách và chuẩn hóa dữ liệu hồ sơ mạng vệ tinh phi địa tĩnh (Non-GSO FSS)
theo chuẩn Phụ lục 4 Thể lệ Vô tuyến ITU (RR AP4 Annex 2B) và phần mềm ITU SpaceCap.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


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
    """Bóc tách hồ sơ Phụ lục 4 từ chuỗi JSON hoặc Dict."""
    data = json.loads(json_content) if isinstance(json_content, str) else json_content
    orbit = data.get("orbit", {})
    planes_raw = orbit.get("planes", [])
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

    return Appendix4Filing(
        id=data.get("id", "custom-filing"),
        name=data.get("name", "CUSTOM-FILING"),
        notifying_adm=data.get("notifying_adm", "XXX"),
        operator=data.get("operator", "Unknown Operator"),
        br_ific_ref=int(data.get("br_ific_ref", 0)),
        special_section=data.get("special_section", "CR/C/0000"),
        filing_type=data.get("filing_type", "NON-GSO FSS"),
        total_satellites=int(orbit.get("total_satellites", sum(p.satellites_per_plane * p.num_planes for p in planes))),
        constellation_type=orbit.get("constellation_type", "Walker Delta"),
        orbital_period_min=float(orbit.get("orbital_period_min", 95.0)),
        planes=planes,
        frequency_assignments=freqs,
        antenna_patterns=data.get("antenna_patterns", {}),
        service_area=data.get("service_area", {}),
        applicable_itu_provisions=data.get("applicable_itu_provisions", []),
    )


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

    return {
        "is_complete_ap4": is_compliant,
        "status_label": "HỒ SƠ HỢP LỆ THEO AP4" if is_compliant else "THIẾU TRƯỜNG DỮ LIỆU AP4 BẮT BUỘC",
        "total_checks": len(mandatory_checks),
        "passed_checks": sum(1 for v in mandatory_checks.values() if v),
        "details": mandatory_checks,
        "missing_fields": missing_fields,
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
    Ưu tiên 100% hồ sơ thực tế từ Công báo Quốc tế ITU BR IFIC (Realtime),
    kèm theo các hồ sơ phụ trợ mẫu nếu có.
    """
    itu_filings = load_itu_br_ific_filings()
    seen_ids = {f.id for f in itu_filings}
    samples = load_spacecap_samples()
    combined = list(itu_filings)
    for s in samples:
        if s.id not in seen_ids and not any(f.name.lower() in s.name.lower() for f in itu_filings):
            combined.append(s)
    return combined


def get_filing_by_id(filing_id: str) -> Optional[Appendix4Filing]:
    """Tìm hồ sơ theo ID từ toàn bộ nguồn dữ liệu ITU BR IFIC và mẫu SpaceCap."""
    # 1. Tìm chính xác ID trong ITU BR IFIC
    itu_filings = load_itu_br_ific_filings()
    for f in itu_filings:
        if f.id == filing_id or f.name == filing_id:
            return f

    # 2. Tìm chính xác ID trong mẫu SpaceCap
    samples = load_spacecap_samples()
    for s in samples:
        if s.id == filing_id or s.name == filing_id:
            return s

    # 3. Ánh xạ alias nếu có
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

    return None

