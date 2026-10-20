"""Kiểm thử CSDL phối hợp tần số vệ tinh quốc gia."""
from datetime import date

import pytest

from leo_coord import database as db


@pytest.fixture
def dbpath(tmp_path):
    p = tmp_path / "coord.db"
    db.init_db(p)
    return str(p)


def test_add_and_list_filing(dbpath):
    fid = db.add_filing(dbpath, network_name="VN-LEO-1", administration="VTN",
                        n_sats_filed=648, operator="DemoSat",
                        bands="10.7-12.7 GHz", alt_km=550.0, inc_deg=53.0,
                        status="COORDINATION", biu_deadline="2031-03-01")
    assert fid == 1
    rows = db.list_filings(dbpath)
    assert len(rows) == 1 and rows[0]["network_name"] == "VN-LEO-1"
    with pytest.raises(Exception):
        db.add_filing(dbpath, network_name="VN-LEO-1", administration="VTN",
                      n_sats_filed=10)  # trùng tên


def test_invalid_status_rejected(dbpath):
    with pytest.raises(ValueError):
        db.add_filing(dbpath, network_name="X", administration="VTN",
                      n_sats_filed=10, status="KHONG_HOP_LE")


def test_deployment_and_milestones(dbpath):
    db.add_filing(dbpath, network_name="VN-LEO-1", administration="VTN",
                  n_sats_filed=648, biu_deadline="2024-03-01")
    db.report_deployment(dbpath, "VN-LEO-1", "2025-06-01", 70, source="test")
    db.report_deployment(dbpath, "VN-LEO-1", "2028-12-01", 320, source="test")
    out = db.milestone_status(dbpath, today=date(2030, 1, 1))
    assert len(out) == 1
    ms = out[0]["milestones"]
    assert ms[0]["status"] == "DAT"          # 70 >= 65 trước 2026-03-01
    assert ms[1]["status"] == "TRE_HAN"      # 320 < 324
    assert ms[2]["status"] == "CHUA_DEN_HAN"


def test_deployment_unknown_filing(dbpath):
    with pytest.raises(ValueError):
        db.report_deployment(dbpath, "KHONG_TON_TAI", "2025-01-01", 5)


def test_coordination_cases(dbpath):
    db.add_filing(dbpath, network_name="VN-LEO-1", administration="VTN",
                  n_sats_filed=100)
    cid = db.add_coordination_case(dbpath, "VN-LEO-1", "GSO-KU-105E",
                                   band="10.7-12.7 GHz",
                                   trigger="cung ±6° (Appendix 5)",
                                   notes="test")
    assert cid == 1
    rows = db.list_coordination_cases(dbpath, "VN-LEO-1")
    assert len(rows) == 1 and rows[0]["other_system"] == "GSO-KU-105E"


def test_export_csv(dbpath, tmp_path):
    db.add_filing(dbpath, network_name="VN-LEO-1", administration="VTN",
                  n_sats_filed=100)
    out = tmp_path / "filings.csv"
    p = db.export_filings_csv(dbpath, out)
    assert p.exists()
    assert "VN-LEO-1" in p.read_text(encoding="utf-8")
