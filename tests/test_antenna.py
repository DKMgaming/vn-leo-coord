"""Kiểm thử mô hình búp sóng ăng-ten thực tế theo Khuyến nghị ITU-R (S.1428, S.672, S.580)."""
import pytest
import numpy as np

from leo_coord.antenna import (
    itu_r_s1428_pattern,
    itu_r_s672_pattern,
    itu_r_s580_pattern,
    calculate_in_line_geometry,
    evaluate_in_line_event,
)


def test_s1428_main_beam_and_sidelobes():
    g_max = 35.0
    hpbw = 2.5
    l_s = 20.0

    # 1. Đỉnh búp sóng chính tại theta = 0
    assert itu_r_s1428_pattern(0.0, g_max, hpbw, l_s) == pytest.approx(g_max)

    # 2. Tại góc nửa công suất (HPBW / 2 = 1.25 deg): độ lợi giảm 3 dB so với đỉnh
    # 12 * (1.25 / 2.5)^2 = 12 * 0.25 = 3.0 dB
    g_half = itu_r_s1428_pattern(1.25, g_max, hpbw, l_s)
    assert g_half == pytest.approx(g_max - 3.0)

    # 3. Tại góc HPBW (2.5 deg): độ lợi giảm 12 dB
    g_hpbw = itu_r_s1428_pattern(2.5, g_max, hpbw, l_s)
    assert g_hpbw == pytest.approx(g_max - 12.0)

    # 4. Búp sóng phụ gần: đạt mức sàn plateau g_max - l_s
    theta_plateau = 1.5 * hpbw
    g_plateau = itu_r_s1428_pattern(theta_plateau, g_max, hpbw, l_s)
    assert g_plateau == pytest.approx(g_max - l_s)

    # 5. Búp sóng phụ xa: giảm dần và không thấp hơn g_min (-10 dBi)
    g_far = itu_r_s1428_pattern(90.0, g_max, hpbw, l_s, g_min_dbi=-10.0)
    assert g_far >= -10.0
    assert g_far < g_plateau

    # 6. Hỗ trợ mảng numpy
    arr = itu_r_s1428_pattern(np.array([0.0, 1.25, 2.5]), g_max, hpbw, l_s)
    assert len(arr) == 3
    assert arr[0] > arr[1] > arr[2]


def test_s672_gso_satellite_pattern():
    g_max = 42.0
    hpbw = 1.5
    l_s = 20.0

    assert itu_r_s672_pattern(0.0, g_max, hpbw, l_s) == pytest.approx(g_max)
    # Tại góc 0.75 độ (nửa HPBW): giảm 3 dB
    assert itu_r_s672_pattern(0.75, g_max, hpbw, l_s) == pytest.approx(g_max - 3.0)
    # Tại góc 15 độ: xa búp sóng chính
    assert itu_r_s672_pattern(15.0, g_max, hpbw, l_s) < g_max - l_s


def test_s580_earth_station_pattern():
    d_m = 1.2
    freq_ghz = 11.7

    g_peak = itu_r_s580_pattern(0.0, d_m=d_m, freq_ghz=freq_ghz)
    # Chảo 1.2m ở 11.7 GHz có độ lợi đỉnh khoảng 40 - 43 dBi
    assert 39.0 <= g_peak <= 44.0

    # Tại góc lệch 10 độ: 29 - 25*log10(10) = 4 dBi
    g_10 = itu_r_s580_pattern(10.0, d_m=d_m, freq_ghz=freq_ghz)
    assert g_10 == pytest.approx(4.0, abs=0.1)

    # Tại góc lệch 30 độ: -3.5 dBi
    assert itu_r_s580_pattern(30.0, d_m=d_m, freq_ghz=freq_ghz) == pytest.approx(-3.5)

    # Tại góc lệch 90 độ: -10 dBi
    assert itu_r_s580_pattern(90.0, d_m=d_m, freq_ghz=freq_ghz) == pytest.approx(-10.0)

    # Khả năng phân biệt không gian (Spatial Discrimination) lớn hơn 35 dB tại góc 10 độ
    assert (g_peak - g_10) > 35.0


def test_in_line_event_critical_alignment():
    # Giả lập trạm mặt đất Đà Nẵng (16.05°N, 108.20°E) hướng nhìn Vinasat-1 (132°E)
    # Đặt vệ tinh LEO gần như thẳng hàng trên đường ngắm giữa trạm và Vinasat
    # Đường ngắm từ Đà Nẵng tới Vinasat (GSO 132°E) có góc phương vị khoảng 115°, góc ngẩng ~57°
    # Ta chọn một điểm LEO có cự ly góc lệch cực nhỏ (< 0.5 độ)
    gs_lat, gs_lon = 16.0544, 108.2022
    
    # 1. Trường hợp vệ tinh LEO ở rất xa đường ngắm (ví dụ vĩ độ cao 60°N)
    res_safe = evaluate_in_line_event(
        sat_lat=60.0, sat_lon=108.2, sat_alt_km=550.0,
        gs_lat=gs_lat, gs_lon=gs_lon, gso_lon_deg=132.0
    )
    assert res_safe["risk_level"] == "SAFE"
    assert res_safe["beam_blanking_required"] is False
    assert res_safe["separation_angle_deg"] > 10.0

    # 2. Trường hợp vệ tinh LEO thẳng hàng trên đường ngắm (In-line Event)
    # Tọa độ hình học chính xác tính được từ Đà Nẵng tới Vinasat (132°E): lat ~ 14.4827°, lon ~ 110.7661°
    res_critical = evaluate_in_line_event(
        sat_lat=14.4827, sat_lon=110.7661, sat_alt_km=550.0,
        gs_lat=gs_lat, gs_lon=gs_lon, gso_lon_deg=132.0
    )
    assert res_critical["risk_level"] == "CRITICAL_IN_LINE"
    assert res_critical["beam_blanking_required"] is True
    assert res_critical["separation_angle_deg"] < 0.1

    # 3. Trường hợp vệ tinh LEO nằm trong cung phối hợp (góc kẹp ~3.6 độ <= 6 độ)
    res_coord = evaluate_in_line_event(
        sat_lat=14.4827 + 0.35, sat_lon=110.7661, sat_alt_km=550.0,
        gs_lat=gs_lat, gs_lon=gs_lon, gso_lon_deg=132.0
    )
    assert res_coord["risk_level"] == "COORDINATION_ZONE"
    assert res_coord["beam_blanking_required"] is False
    assert 2.0 < res_coord["separation_angle_deg"] <= 6.0
