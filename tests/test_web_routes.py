"""Kiểm thử route xem báo cáo HTML đầy đủ trên web app."""
from web.app import app, view_assessment_report, OUT_DIR, index_page


def test_routes_registered():
    route_paths = [route.path for route in app.routes]
    assert "/out/bao_cao.html" in route_paths
    assert "/report" in route_paths
    assert "/" in route_paths
    # Kiểm tra mount /out
    out_mount = any(getattr(r, "path", None) == "/out" for r in app.routes)
    assert out_mount


def test_index_page():
    res = index_page()
    assert res.status_code == 200
    assert "LEO-COORD" in res.body.decode("utf-8")


def test_view_report_out_route():
    res = view_assessment_report()
    assert res.status_code == 200
    assert "text/html" in res.media_type
    content = res.body.decode("utf-8")
    assert "<!DOCTYPE html>" in content or "<html" in content


def test_view_report_autogenerates_if_missing(tmp_path, monkeypatch):
    test_out = tmp_path / "out"
    test_out.mkdir()
    monkeypatch.setattr("web.app.OUT_DIR", test_out)

    report_file = test_out / "bao_cao.html"
    assert not report_file.exists()

    res = view_assessment_report()
    assert res.status_code == 200
    assert report_file.exists()
    assert report_file.stat().st_size > 0
    content = res.body.decode("utf-8")
    assert "BÁO CÁO THẨM ĐỊNH" in content or "<!DOCTYPE html>" in content


def test_appendix7_endpoints_registered():
    route_paths = [route.path for route in app.routes]
    assert "/api/appendix7/summary" in route_paths
    assert "/api/appendix7/contours" in route_paths
    assert "/api/appendix7/evaluate-gateway" in route_paths


def test_appendix7_summary_function():
    from web.app import get_appendix7_summary
    res = get_appendix7_summary(freq_ghz=28.5, eirp_density=48.0)
    assert res["total_stations_evaluated"] == 7
    assert len(res["stations"]) == 7
    assert "coexistence_5g_fs" in res


def test_appendix7_contours_function():
    from web.app import get_appendix7_contours
    res = get_appendix7_contours(freq_ghz=28.5, eirp_density=48.0)
    assert "stations" in res
    assert len(res["stations"]) == 7
    for st in res["stations"]:
        assert "contour_points" in st
        assert len(st["contour_points"]) > 10


def test_appendix7_evaluate_gateway_function():
    from web.app import evaluate_custom_gateway
    payload = {
        "name": "Gateway Viettel Hoa Lac",
        "lat": 20.985,
        "lon": 105.525,
        "freq_ghz": 28.5,
        "eirp_density_dbw_per_mhz": 48.0
    }
    res = evaluate_custom_gateway(payload)
    assert res["gateway"]["name"] == "Gateway Viettel Hoa Lac"
    assert "contour" in res
    assert "border_encroachment" in res
    assert "coexistence_5g" in res


def test_phase3_endpoints_registered():
    route_paths = [route.path for route in app.routes]
    assert "/api/br-ific/scan" in route_paths
    assert "/api/spacecom/draft-comment/{notice_id}" in route_paths
    assert "/api/spacecom/download-comment/{notice_id}" in route_paths
    assert "/api/epfd/s1503-simulation" in route_paths


def test_br_ific_scan_endpoint():
    from web.app import get_br_ific_scan
    res = get_br_ific_scan()
    assert res["status"] == "success"
    assert res["total_notices_scanned"] >= 5
    assert res["total_high_risk_objections_needed"] >= 2


def test_spacecom_draft_endpoint():
    from web.app import get_spacecom_draft_comment
    res = get_spacecom_draft_comment("USASAT-NGSO-3-MOD")
    assert res["status"] == "ready"
    assert res["commenting_administration"] == "VTN"
    assert "DISAGREEMENT" in res["finding"]


def test_epfd_s1503_simulation_endpoint():
    from web.app import get_s1503_simulation
    res = get_s1503_simulation(duration_min=10, dish_d_m=1.2, station="danang")
    assert res["status"] == "success"
    assert "mask_comparison" in res
    assert "cdf_curve" in res


def test_phase4_endpoints_registered():
    route_paths = [route.path for route in app.routes]
    assert "/api/spacecap/samples" in route_paths
    assert "/api/spacecap/parse" in route_paths
    assert "/api/spacecap/download-xml/{filing_id}" in route_paths
    assert "/api/multi-agent/convene" in route_paths
    assert "/api/multi-agent/export-markdown/{filing_id}" in route_paths


def test_spacecap_samples_endpoint():
    from web.app import get_spacecap_samples_endpoint
    res = get_spacecap_samples_endpoint()
    assert res["total"] >= 3
    assert len(res["filings"]) >= 3
    first = res["filings"][0]
    assert "validation" in first
    assert first["validation"]["is_complete_ap4"] is True


def test_multi_agent_convene_endpoint():
    from web.app import convene_multi_agent_council_endpoint
    res = convene_multi_agent_council_endpoint({"filing_id": "starlink-gen2-ap4"})
    assert res["satellite_name"] == "STARLINK-GEN2-C-1"
    assert res["overall_verdict"] == "CONDITIONAL_APPROVAL_WITH_COORDINATION"
    assert len(res["deliberations"]) == 4
    assert len(res["vietnam_pilot_conditions"]) >= 4


def test_multi_agent_filings_endpoint():
    from web.app import get_multi_agent_filings_endpoint
    res = get_multi_agent_filings_endpoint()
    assert res["status"] == "success"
    assert res["total"] >= 6
    assert any(f["id"] == "USASAT-NGSO-3-MOD" for f in res["filings"])
    assert any(f["id"] == "KORSAT-NGSO-KA" for f in res["filings"])


def test_multi_agent_sync_itu_endpoint():
    from web.app import sync_multi_agent_itu_endpoint
    res = sync_multi_agent_itu_endpoint()
    assert res["status"] == "success"
    assert res["total_filings_available"] >= 6
    assert "latest_br_ific_in_database" in res["sync_info"]


def test_spacecap_upload_endpoint():
    import asyncio
    import io
    from starlette.datastructures import UploadFile
    from web.app import upload_spacecap_filing, get_multi_agent_filings_endpoint

    xml_content = """<?xml version="1.0" encoding="utf-8"?>
    <spacecap_filing xmlns="http://www.itu.int/ITU-R/spacecap" version="2.0">
      <header>
        <satellite_name>UPLOAD-TEST-SAT</satellite_name>
        <notifying_administration>VTN</notifying_administration>
        <operator>VNPT Space</operator>
        <br_ific_number>3022</br_ific_number>
      </header>
      <orbit>
        <constellation_type>Walker Delta</constellation_type>
        <total_satellites>60</total_satellites>
        <orbital_planes>
          <plane id="1">
            <altitude_km>550.0</altitude_km>
            <inclination_deg>53.0</inclination_deg>
            <satellites_per_plane>10</satellites_per_plane>
            <num_planes>6</num_planes>
          </plane>
        </orbital_planes>
      </orbit>
      <frequency_assignments>
        <assignment>
          <band_name>Ku-band</band_name>
          <freq_min_ghz>10.7</freq_min_ghz>
          <freq_max_ghz>12.75</freq_max_ghz>
          <service>FSS</service>
          <max_pfd_4khz>-146.0</max_pfd_4khz>
        </assignment>
      </frequency_assignments>
    </spacecap_filing>
    """
    upload_file = UploadFile(filename="upload_test.xml", file=io.BytesIO(xml_content.encode("utf-8")))
    res = asyncio.run(upload_spacecap_filing(upload_file))

    assert res["status"] == "success"
    assert res["filing"]["name"] == "UPLOAD-TEST-SAT"
    assert res["filing"]["total_satellites"] == 60
    assert res["filing"]["is_complete_ap4"] is True

    # Check that it appears in filings list with ⭐ [HỒ SƠ TẢI LÊN]
    res_list = get_multi_agent_filings_endpoint()
    uploaded_item = next((f for f in res_list["filings"] if f["id"] == res["filing"]["id"]), None)
    assert uploaded_item is not None
    assert uploaded_item["is_user_uploaded"] is True
    assert "⭐ [HỒ SƠ TẢI LÊN]" in uploaded_item["display_label"]

    from leo_coord.spacecap import UPLOADED_FILINGS_DIR
    test_json = UPLOADED_FILINGS_DIR / f"{res['filing']['id']}.json"
    if test_json.exists():
        test_json.unlink()


def test_real_satellite_orbit_track_route():
    from web.app import get_satellite_orbit_track_endpoint
    res = get_satellite_orbit_track_endpoint(25544)
    assert res["status"] == "success"
    assert res["norad_id"] == 25544
    assert "points" in res
    assert len(res["points"]) > 20
    assert "lat" in res["points"][0]
    assert "lon" in res["points"][0]





