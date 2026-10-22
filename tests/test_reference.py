"""Kiểm thử toàn diện module dữ liệu tham chiếu ITU (data/reference/)."""
import pytest
from pathlib import Path

from leo_coord.reference import (
    reference_dir,
    load_reference_registry,
    load_pfd_reference,
    load_epfd_reference,
    load_coordination_reference,
    load_milestones_reference,
    get_verification_status_summary,
    find_pfd_band,
    find_coordination_arc,
    find_pfd_trigger_9_7,
    get_epfd_antenna_curve,
    audit_reference_tables,
)


def test_reference_directory_exists():
    rdir = reference_dir()
    assert rdir.exists() and rdir.is_dir()
    assert (rdir / "itu_reference_registry.yaml").exists()
    assert (rdir / "pfd_limits.yaml").exists()
    assert (rdir / "epfd_limits.yaml").exists()
    assert (rdir / "coordination_arcs.yaml").exists()
    assert (rdir / "milestones_res35.yaml").exists()


def test_registry_loading_and_verification_status():
    reg = load_reference_registry()
    assert "registry_meta" in reg
    assert "tables" in reg
    meta = reg["registry_meta"]
    assert meta["overall_status"] == "ITU-OFFICIAL-VERIFIED"
    assert "ITU Radio Regulations" in meta["rr_edition"]
    assert len(reg["tables"]) >= 6

    # Mọi bảng đều phải có verification_status hợp chuẩn
    for t in reg["tables"]:
        assert "VERIFIED" in t["verification_status"]
        assert t["itu_citation"] != ""
        assert t["file_rel_path"] != ""


def test_verification_status_summary():
    summary = get_verification_status_summary()
    assert summary["total_tables"] >= 6
    assert summary["verified_tables"] == summary["total_tables"]
    assert summary["provisional_tables"] == 0
    assert summary["verification_rate_percent"] == 100.0
    assert summary["overall_status"] == "ITU-OFFICIAL-VERIFIED"


def test_pfd_limits_reference():
    pfd = load_pfd_reference()
    assert pfd["table_metadata"]["verification_status"] == "ITU-OFFICIAL-VERIFIED"
    bands = pfd["bands"]
    assert len(bands) >= 5

    # Kiểm tra dải Ku chính 10.7-11.7 GHz
    ku = find_pfd_band(11.2)
    assert ku["id"] == "PFD-KU-1"
    assert ku["unit"] == "dB(W/m2)/4kHz"
    assert ku["delta_le_5"] == pytest.approx(-150.0)
    assert ku["delta_ge_25"] == pytest.approx(-140.0)
    assert ku["slope"] == pytest.approx(0.5)
    assert ku["ngso_reduction_X_applicable"] is True

    # Kiểm tra dải Ka 17.7-19.3 GHz
    ka = find_pfd_band(18.2)
    assert ka["id"] == "PFD-KA-1"
    assert ka["unit"] == "dB(W/m2)/MHz"
    assert ka["delta_le_5"] == pytest.approx(-115.0)
    assert ka["delta_ge_25"] == pytest.approx(-105.0)

    # Kiểm tra dải C-band 3.4-4.2 GHz
    c_band = find_pfd_band(3.8)
    assert c_band["id"] == "PFD-C-BAND"
    assert c_band["delta_le_5"] == pytest.approx(-152.0)

    # Tần số ngoài dải phải raise ValueError
    with pytest.raises(ValueError):
        find_pfd_band(2.0)


def test_epfd_limits_reference():
    epfd = load_epfd_reference()
    assert epfd["table_metadata"]["verification_status"] == "ITU-OFFICIAL-VERIFIED"

    # Single-entry Ku
    ku = epfd["single_entry_ku"]
    assert ku["never_exceed_hard_ceiling"] == pytest.approx(-160.0)
    assert "antenna_masks" in ku
    assert set(ku["antenna_masks"].keys()) >= {
        "antenna_0_6m", "antenna_1_2m", "antenna_3_0m", "antenna_10_0m"
    }

    # Test lấy curve ăng-ten 1.2m
    curve_1_2m = get_epfd_antenna_curve("antenna_1_2m")
    assert len(curve_1_2m) >= 5
    pct_100 = [pt for pt in curve_1_2m if pt["percentage_of_time"] == 100.0][0]
    assert pct_100["limit_dbw_m2_40khz"] == pytest.approx(-161.0)

    # Aggregate Res 76
    agg = epfd["aggregate_epfd_res76"]
    assert agg["source"].startswith("ITU Resolution 76")
    assert "antenna_60cm" in agg["table_1A_values"]


def test_coordination_arcs_and_triggers_reference():
    coord = load_coordination_reference()
    assert coord["table_metadata"]["verification_status"] == "ITU-OFFICIAL-VERIFIED"

    # Cung phối hợp Appendix 5 Table 5-1
    assert find_coordination_arc(3.8) == pytest.approx(7.0)   # C-band
    assert find_coordination_arc(11.5) == pytest.approx(6.0)  # Ku-band
    assert find_coordination_arc(18.5) == pytest.approx(8.0)  # Ka-band FSS-FSS
    assert find_coordination_arc(21.8) == pytest.approx(12.0) # 21 GHz BSS

    # Ngưỡng kích hoạt No. 9.7A/9.7B
    trig_ku_leo = find_pfd_trigger_9_7(11.5, alt_km=600.0)
    assert trig_ku_leo is not None
    assert trig_ku_leo[0] == pytest.approx(-174.5)
    assert trig_ku_leo[1] == "dB(W/m2)/40kHz"
    assert trig_ku_leo[2] == "TRIG-KU-LOW-ALT"

    trig_ku_meo = find_pfd_trigger_9_7(11.5, alt_km=8000.0)
    assert trig_ku_meo is not None
    assert trig_ku_meo[0] == pytest.approx(-202.0)
    assert trig_ku_meo[2] == "TRIG-KU-HIGH-ALT"

    # Delta T/T 6%
    assert coord["delta_t_over_t"]["trigger_threshold_percent"] == pytest.approx(6.0)


def test_milestones_res35_reference():
    ms = load_milestones_reference()
    assert ms["table_metadata"]["verification_status"] == "ITU-OFFICIAL-VERIFIED"

    # BIU rule
    biu = ms["regulatory_milestones"]["biu_requirement"]
    assert biu["time_limit_years"] == pytest.approx(7.0)

    # Milestones M1, M2, M3
    marks = ms["regulatory_milestones"]["milestones"]
    assert len(marks) == 3
    assert marks[0]["percentage_required"] == pytest.approx(10.0)
    assert marks[0]["deadline_years_after_biu"] == pytest.approx(2.0)
    assert marks[1]["percentage_required"] == pytest.approx(50.0)
    assert marks[1]["deadline_years_after_biu"] == pytest.approx(5.0)
    assert marks[2]["percentage_required"] == pytest.approx(100.0)
    assert marks[2]["deadline_years_after_biu"] == pytest.approx(7.0)

    # Resolution 8 (WRC-23) tolerances
    tol = ms["orbital_tolerances_res8"]
    assert tol["inclination_tolerance"]["limit_deg"] == pytest.approx(1.5)


def test_audit_all_tables_pass():
    audit_results = audit_reference_tables()
    assert len(audit_results) >= 6
    for item in audit_results:
        assert item["file_exists"] is True
        assert item["valid_syntax"] is True
        assert item["items_count"] > 0
        assert item["compliant"] is True
        assert "VERIFIED" in item["verification_status"]
