from pathlib import Path
from leo_coord.spacecap import (
    load_spacecap_samples,
    parse_appendix4_json,
    validate_appendix4_completeness,
    export_appendix4_xml,
    Appendix4Filing,
)


def test_load_spacecap_samples():
    samples = load_spacecap_samples()
    assert len(samples) >= 3
    names = [s.name for s in samples]
    assert "STARLINK-GEN2-C-1" in names
    assert "GW-A59" in names
    assert "ONEWEB-PHASE2" in names

    starlink = next(s for s in samples if s.name == "STARLINK-GEN2-C-1")
    assert starlink.notifying_adm == "USA"
    assert starlink.total_satellites == 29988
    assert len(starlink.planes) >= 2
    assert len(starlink.frequency_assignments) >= 2


def test_validate_appendix4_completeness():
    samples = load_spacecap_samples()
    starlink = samples[0]
    validation = validate_appendix4_completeness(starlink)
    assert validation["is_complete_ap4"] is True
    assert validation["passed_checks"] == validation["total_checks"]
    assert len(validation["missing_fields"]) == 0

    # Incomplete filing
    incomplete = Appendix4Filing(
        id="bad-filing",
        name="",
        notifying_adm="",
        operator="Test",
        br_ific_ref=0,
        special_section="",
    )
    inv_val = validate_appendix4_completeness(incomplete)
    assert inv_val["is_complete_ap4"] is False
    assert len(inv_val["missing_fields"]) > 0


def test_parse_appendix4_json():
    raw_json = """
    {
      "id": "test-ngso-1",
      "name": "TEST-SAT-NGSO",
      "notifying_adm": "VTN",
      "operator": "VNPT",
      "br_ific_ref": 3050,
      "special_section": "CR/C/7000",
      "orbit": {
        "constellation_type": "Walker Delta",
        "total_satellites": 72,
        "orbital_period_min": 98.0,
        "planes": [
          {"plane_id": 1, "altitude_km": 600.0, "inclination_deg": 60.0, "satellites_per_plane": 12, "num_planes": 6}
        ]
      },
      "frequency_assignments": [
        {"band_name": "Ka-band", "freq_min_ghz": 18.1, "freq_max_ghz": 18.6, "max_pfd_dbw_m2_1mhz": -118.0}
      ]
    }
    """
    filing = parse_appendix4_json(raw_json)
    assert filing.name == "TEST-SAT-NGSO"
    assert filing.total_satellites == 72
    assert len(filing.planes) == 1
    assert filing.planes[0].altitude_km == 600.0
    assert filing.planes[0].satellites_per_plane == 12
    assert len(filing.frequency_assignments) == 1


def test_export_appendix4_xml():
    samples = load_spacecap_samples()
    filing = samples[0]
    xml_str = export_appendix4_xml(filing)
    assert "<spacecap_filing" in xml_str
    assert "<satellite_name>STARLINK-GEN2-C-1</satellite_name>" in xml_str
    assert "<total_satellites>29988</total_satellites>" in xml_str
    assert "</spacecap_filing>" in xml_str
