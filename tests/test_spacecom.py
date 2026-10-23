"""Kiểm thử mô-đun Trợ lý Phản đối Tần số SpaceCom (ITU SpaceCom Assistant)."""
from datetime import date
import pytest
import xml.etree.ElementTree as ET

from leo_coord.spacecom import generate_spacecom_draft, export_spacecom_xml


def test_generate_spacecom_draft():
    draft = generate_spacecom_draft("USASAT-NGSO-3-MOD", ref_date=date(2026, 10, 23))
    assert draft["status"] == "ready"
    assert draft["commenting_administration"] == "VTN"
    assert draft["notifying_adm"] == "USA"
    assert "DISAGREEMENT" in draft["finding"]
    assert "RR No. 9.7B" in draft["applicable_provisions"]
    assert "RR No. 22.2" in draft["applicable_provisions"]
    # Kiểm tra có 2 mạng Vinasat được bảo vệ
    victim_names = [v["name"] for v in draft["victim_networks"]]
    assert "VINASAT-1" in victim_names
    assert "VINASAT-2" in victim_names
    assert len(draft["justification_vi"]) > 100
    assert len(draft["justification_en"]) > 100


def test_export_spacecom_xml():
    xml_str = export_spacecom_xml("CHNSAT-NGSO-1")
    assert "<?xml" in xml_str
    assert "<SpaceCom_Comments" in xml_str
    # Kiểm tra tính hợp lệ cú pháp XML
    root = ET.fromstring(xml_str)
    assert root.tag == "SpaceCom_Comments"
    header = root.find("Header")
    assert header.find("Commenting_Administration").text == "VTN"
    assert header.find("Notifying_Administration").text == "CHN"
    comment = root.find("Comment")
    assert comment.find("Finding").text == "DISAGREEMENT"
    provs = [p.text for p in comment.find("Invoked_Provisions").findall("Provision")]
    assert "RR No. 9.7B" in provs
    assert "RR No. 22.2" in provs


def test_generate_draft_invalid_id():
    with pytest.raises(ValueError):
        generate_spacecom_draft("NON_EXISTENT_ID")
