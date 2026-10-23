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



