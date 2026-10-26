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


def test_parse_appendix4_xml():
    from leo_coord.spacecap import parse_appendix4_xml
    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
    <spacecap_filing xmlns="http://www.itu.int/ITU-R/spacecap" version="2.0">
      <header>
        <satellite_name>TEST-LEO-SAT</satellite_name>
        <notifying_administration>VTN</notifying_administration>
        <operator>VNPT Space</operator>
        <br_ific_number>3020</br_ific_number>
        <special_section>CR/C/9999</special_section>
      </header>
      <orbit>
        <constellation_type>Walker Delta</constellation_type>
        <total_satellites>144</total_satellites>
        <orbital_planes>
          <plane id="1">
            <altitude_km>500.0</altitude_km>
            <inclination_deg>45.0</inclination_deg>
            <satellites_per_plane>12</satellites_per_plane>
            <num_planes>12</num_planes>
          </plane>
        </orbital_planes>
      </orbit>
      <frequency_assignments>
        <assignment>
          <band_name>Ku-band DL</band_name>
          <freq_min_ghz>10.95</freq_min_ghz>
          <freq_max_ghz>12.75</freq_max_ghz>
          <service>FSS</service>
          <max_pfd_4khz>-146.0</max_pfd_4khz>
        </assignment>
      </frequency_assignments>
      <service_area>
        <vietnam_covered>true</vietnam_covered>
        <inside_coordination_arc_6deg>true</inside_coordination_arc_6deg>
        <closest_approach_to_vinasat_deg>1.5</closest_approach_to_vinasat_deg>
      </service_area>
    </spacecap_filing>
    """
    filing = parse_appendix4_xml(sample_xml, filename="sample.xml")
    assert filing.name == "TEST-LEO-SAT"
    assert filing.notifying_adm == "VTN"
    assert filing.operator == "VNPT Space"
    assert filing.br_ific_ref == 3020
    assert filing.total_satellites == 144
    assert len(filing.planes) == 1
    assert filing.planes[0].altitude_km == 500.0
    assert len(filing.frequency_assignments) == 1
    assert filing.frequency_assignments[0].freq_min_ghz == 10.95
    assert filing.service_area.get("is_user_uploaded") is True
    assert filing.service_area.get("vietnam_covered") is True


def test_parse_appendix4_any_formats(tmp_path):
    from leo_coord.spacecap import parse_appendix4_any, save_uploaded_filing, load_uploaded_filings, UPLOADED_FILINGS_DIR
    import leo_coord.spacecap as sc

    # 1. XML
    xml_str = """<spacecap><satellite_name>KORSAT-TEST</satellite_name><notifying_adm>KOR</notifying_adm><total_satellites>50</total_satellites></spacecap>"""
    f_xml = parse_appendix4_any(xml_str, filename="test.xml")
    assert f_xml.name == "KORSAT-TEST"
    assert f_xml.notifying_adm == "KOR"

    # 2. JSON
    json_str = '{"name": "MY-LEO-JSON", "notifying_adm": "USA", "total_satellites": 80}'
    f_json = parse_appendix4_any(json_str, filename="test.json")
    assert f_json.name == "MY-LEO-JSON"

    # 3. Save and Load
    # Patch UPLOADED_FILINGS_DIR to tmp_path for isolated testing
    orig_dir = sc.UPLOADED_FILINGS_DIR
    try:
        sc.UPLOADED_FILINGS_DIR = tmp_path
        saved_path = save_uploaded_filing(f_xml)
        assert saved_path.exists()

        loaded = load_uploaded_filings()
        assert len(loaded) >= 1
        assert any(x.name == "KORSAT-TEST" for x in loaded)
    finally:
        sc.UPLOADED_FILINGS_DIR = orig_dir
