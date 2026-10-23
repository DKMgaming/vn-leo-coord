"""Trợ lý Phản đối Tần số SpaceCom & Soạn thảo Công văn Phối hợp ITU (SpaceCom Assistant).

Cơ sở pháp lý:
- Thể lệ Vô tuyến ITU (ITU Radio Regulations - RR Edition 2024):
  - RR No. 9.7B: Phối hợp bắt buộc giữa mạng GSO FSS và hệ thống NGSO FSS theo Phụ lục 5.
  - RR No. 9.11A: Quy trình phối hợp đa phương áp dụng cho các dịch vụ vệ tinh phân bổ toàn cầu.
  - RR No. 22.2: Hệ thống NGSO không được gây can nhiễu không thể chấp nhận cho mạng GSO.
  - RR No. 9.51 / No. 9.52: Thời hạn và thủ tục thông báo bất đồng ý kiến (Disagreement Comments).
- Chuẩn dữ liệu phần mềm ITU SpaceCom (ITU SpaceCom XML v2.0 format).
- Mẫu công hàm kỹ thuật song ngữ (Việt - Anh) của Cục Tần số Vô tuyến điện (ARFM - VTN).
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import yaml

from .br_ific import load_br_ific_data, calculate_4month_deadline, check_frequency_overlap

ADM_VTN = "VTN"
ADM_VTN_FULL = "Authority of Radio Frequency Management (ARFM), Socialist Republic of Viet Nam"


def get_notice_by_id(notice_id: str) -> Optional[dict]:
    """Tìm thông tin hồ sơ theo ID."""
    data = load_br_ific_data()
    for n in data.get("notices", []):
        if n["id"] == notice_id or n.get("special_section") == notice_id:
            return n
    return None


def generate_spacecom_draft(notice_id: str, ref_date: Optional[date] = None) -> dict:
    """Tạo hồ sơ dự thảo ý kiến phản đối chi tiết cho một thông báo BR IFIC."""
    notice = get_notice_by_id(notice_id)
    if not notice:
        raise ValueError(f"Không tìm thấy hồ sơ công báo với ID: {notice_id}")

    countdown = calculate_4month_deadline(notice["publication_date"], ref_date=ref_date)
    has_overlap, overlaps = check_frequency_overlap(notice.get("frequency_bands", []))
    arc_check = notice.get("coordination_arc_check", {})
    closest_deg = arc_check.get("closest_approach_to_vinasat_deg", 99.0)

    # Các điều khoản viện dẫn
    provisions = ["RR No. 9.7B", "RR No. 9.11A", "RR No. 22.2"]
    victim_sats = [
        {"name": "VINASAT-1", "longitude_deg": 132.0, "status": "In Operation (GSO)"},
        {"name": "VINASAT-2", "longitude_deg": 131.8, "status": "In Operation (GSO)"}
    ]

    justification_vi = (
        f"Mạng vệ tinh {notice['satellite_name']} ({notice['special_section']}, BR IFIC {notice['br_ific_no']}) "
        f"do cơ quan quản lý {notice['notifying_adm']} ({notice.get('org', '')}) thông báo có dải tần phát xạ trùng lấn "
        f"trực tiếp với các băng tần hoạt động của vệ tinh viễn thông quốc gia VINASAT-1 (132°E) và VINASAT-2 (131.8°E). "
        f"Quỹ đạo LEO có góc tiếp cận gần nhất chỉ {closest_deg}° (nằm sâu trong cung phối hợp bắt buộc ±6° theo Thể lệ Vô tuyến RR Phụ lục 5). "
        f"Nguy cơ can nhiễu thẳng hàng (In-line Event) và suy giảm phẩm chất truyền dẫn đối với các đài trái đất tại Việt Nam là rất nghiêm trọng. "
        f"Căn cứ RR No. 9.7B, No. 9.11A và Điều 22 (RR No. 22.2), Việt Nam KHÔNG THỂ CHẤP THUẬN (DISAGREEMENT) hồ sơ này khi chưa có thỏa thuận "
        f"phối hợp kỹ thuật song phương và cam kết áp dụng cơ chế né búp sóng (Beam Blanking)."
    )

    justification_en = (
        f"The administration of Viet Nam (VTN) hereby submits its formal COMMENTS / DISAGREEMENT "
        f"under RR Nos. 9.7B, 9.11A and 9.52 in respect of the NGSO satellite network {notice['satellite_name']} "
        f"({notice['special_section']}, BR IFIC No. {notice['br_ific_no']}) notified by {notice['notifying_adm']} ({notice.get('org', '')}). "
        f"The proposed downlink/uplink frequency assignments directly overlap with the authorized operational frequencies of "
        f"the Vietnamese national GSO networks VINASAT-1 (132.0°E) and VINASAT-2 (131.8°E). "
        f"The orbital trajectory penetrates well within the ±6.0° coordination arc (minimum separation angle: {closest_deg}°), "
        f"causing unacceptable risk of harmful in-line interference to earth stations operating in Viet Nam. "
        f"Pursuant to RR No. 22.2 and Resolution 76 (WRC-19), Viet Nam requests formal bilateral coordination meetings "
        f"and the implementation of operational avoidance angles before any commercial transmissions commence."
    )

    return {
        "status": "ready",
        "notice_id": notice["id"],
        "satellite_name": notice["satellite_name"],
        "notifying_adm": notice["notifying_adm"],
        "org": notice.get("org", ""),
        "br_ific_no": notice["br_ific_no"],
        "special_section": notice["special_section"],
        "publication_date": notice["publication_date"],
        "countdown": countdown,
        "commenting_administration": ADM_VTN,
        "commenting_org_full": ADM_VTN_FULL,
        "finding": "DISAGREEMENT (PHẢN ĐỐI & YÊU CẦU PHỐI HỢP BẮT BUỘC)",
        "applicable_provisions": provisions,
        "victim_networks": victim_sats,
        "closest_separation_deg": closest_deg,
        "overlapping_bands": overlaps,
        "justification_vi": justification_vi,
        "justification_en": justification_en,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def export_spacecom_xml(notice_id: str) -> str:
    """Xuất tệp dữ liệu XML tương thích hoàn toàn với phần mềm ITU SpaceCom v2.0."""
    draft = generate_spacecom_draft(notice_id)
    root = ET.Element("SpaceCom_Comments", attrib={"version": "2.0", "generator": "LEO-COORD-VN"})

    # Header
    hdr = ET.SubElement(root, "Header")
    ET.SubElement(hdr, "Commenting_Administration").text = draft["commenting_administration"]
    ET.SubElement(hdr, "Notifying_Administration").text = draft["notifying_adm"]
    ET.SubElement(hdr, "Target_Satellite_Name").text = draft["satellite_name"]
    ET.SubElement(hdr, "BR_IFIC_Number").text = str(draft["br_ific_no"])
    ET.SubElement(hdr, "Special_Section").text = draft["special_section"]
    ET.SubElement(hdr, "Publication_Date").text = draft["publication_date"]
    ET.SubElement(hdr, "Comment_Deadline").text = draft["countdown"]["deadline_date"]
    ET.SubElement(hdr, "Submission_Date").text = date.today().isoformat()

    # Comment Body
    cmt = ET.SubElement(root, "Comment")
    ET.SubElement(cmt, "Finding").text = "DISAGREEMENT"

    provs = ET.SubElement(cmt, "Invoked_Provisions")
    for p in draft["applicable_provisions"]:
        ET.SubElement(provs, "Provision").text = p

    victims = ET.SubElement(cmt, "Victim_Networks")
    for v in draft["victim_networks"]:
        v_el = ET.SubElement(victims, "Victim_Network")
        ET.SubElement(v_el, "Name").text = v["name"]
        ET.SubElement(v_el, "Orbital_Position").text = f"{v['longitude_deg']}E"
        ET.SubElement(v_el, "Status").text = v["status"]

    ET.SubElement(cmt, "Technical_Justification_EN").text = draft["justification_en"]
    ET.SubElement(cmt, "Technical_Justification_VI").text = draft["justification_vi"]

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
