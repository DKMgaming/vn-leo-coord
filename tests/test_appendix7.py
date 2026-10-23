"""Kiểm thử mô-đun Phụ lục 7 Thể lệ Vô tuyến ITU (RR Appendix 7 / AP7Capture)."""
import pytest
from leo_coord.appendix7 import (
    load_appendix7_params,
    destination_point,
    atmospheric_attenuation_rate,
    mode1_coordination_distance,
    mode2_rain_scatter_distance,
    calculate_coordination_contour,
    evaluate_coexistence_5g_fs,
    check_cross_border_encroachment,
    evaluate_vietnam_stations_appendix7,
)


def test_load_params():
    params = load_appendix7_params()
    assert "climate_vietnam" in params
    assert "gateway_bands" in params
    assert "vietnam_stations" in params
    assert params["climate_vietnam"]["rain_rate_001_mm_per_hr"] == 100.0


def test_destination_point():
    lat0, lon0 = 21.0, 105.0
    # Đi về hướng Bắc 111 km xấp xỉ 1 độ vĩ tuyến
    lat1, lon1 = destination_point(lat0, lon0, 111.0, 0.0)
    assert pytest.approx(lat1, abs=0.1) == 22.0
    assert pytest.approx(lon1, abs=0.1) == 105.0


def test_atmospheric_attenuation_rate():
    # Kiểm tra suy hao khí quyển tại các dải tần Ku và Ka
    gamma_ku = atmospheric_attenuation_rate(12.0)
    gamma_ka = atmospheric_attenuation_rate(28.0)
    assert 0.01 < gamma_ku < 0.1
    assert 0.1 < gamma_ka < 0.3


def test_mode1_coordination_distance():
    # Cự ly Mode 1 phải tăng khi EIRP tăng
    d_low = mode1_coordination_distance(28.5, eirp_density_dbw_per_mhz=30.0)
    d_high = mode1_coordination_distance(28.5, eirp_density_dbw_per_mhz=50.0)
    assert 25.0 <= d_low <= 500.0
    assert 25.0 <= d_high <= 500.0
    assert d_high > d_low


def test_mode2_rain_scatter_distance():
    # Cự ly Mode 2 theo hướng búp sóng chính phải lớn hơn hướng ngược lại
    beam_az = 180.0
    d_forward = mode2_rain_scatter_distance(28.5, beam_azimuth_deg=beam_az, azimuth_deg=180.0)
    d_backward = mode2_rain_scatter_distance(28.5, beam_azimuth_deg=beam_az, azimuth_deg=0.0)
    assert d_forward >= d_backward
    assert 25.0 <= d_forward <= 350.0


def test_coordination_contour_polygon():
    # Tạo contour cho trạm Hà Nội
    c = calculate_coordination_contour(
        lat_deg=21.0285,
        lon_deg=105.8542,
        freq_ghz=28.5,
        eirp_density_dbw_per_mhz=48.0,
        step_deg=15.0
    )
    assert "contour_points" in c
    assert len(c["contour_points"]) == 24
    assert c["max_distance_km"] >= c["min_distance_km"]
    assert c["area_sq_km"] > 1000.0

    # Kiểm tra GeoJSON Polygon hợp lệ khép kín
    geo = c["geojson_geometry"]
    assert geo["type"] == "Polygon"
    ring = geo["coordinates"][0]
    assert len(ring) == 25  # 24 điểm + 1 điểm khép kín
    assert ring[0] == ring[-1]


def test_evaluate_coexistence_5g():
    coex = evaluate_coexistence_5g_fs(freq_ghz=28.5, gateway_eirp_dbw_per_mhz=48.0)
    assert "separation_distance_km" in coex
    dists = coex["separation_distance_km"]
    # Khu vực đô thị có che chắn phải có cự ly cách ly nhỏ hơn tầm nhìn thẳng
    assert dists["urban"] < dists["suburban"] < dists["rural_los"]
    assert coex["isolation_loss_required_db"] == pytest.approx(191.0, abs=0.5)


def test_check_cross_border():
    # Trạm Hà Nội có cự ly contour ~130-150 km, vượt biên giới tới Lào (~110 km) hoặc Trung Quốc (~135 km)
    res_encroached = check_cross_border_encroachment("Hà Nội", 21.0285, 105.8542, max_contour_distance_km=145.0, station_key="hanoi")
    assert res_encroached["requires_international_coordination"] is True
    assert "LAOS" in res_encroached["affected_administrations"]

    # Nếu cự ly contour nhỏ (ví dụ 40 km), nằm hoàn toàn trong nước
    res_safe = check_cross_border_encroachment("Hà Nội", 21.0285, 105.8542, max_contour_distance_km=40.0, station_key="hanoi")
    assert res_safe["requires_international_coordination"] is False


def test_evaluate_vietnam_stations():
    res = evaluate_vietnam_stations_appendix7(freq_ghz=28.5, eirp_density_dbw_per_mhz=48.0)
    assert res["total_stations_evaluated"] == 7
    assert len(res["stations"]) == 7
    # Kiểm tra có trạm Quế Dương, Bình Dương, Bắc Ninh, Việt Trì
    keys = [st["key"] for st in res["stations"]]
    for expected in ["hanoi", "danang", "hochiminh", "viettri", "bacninh", "queduong", "binhduong"]:
        assert expected in keys
