"""Kiểm thử module phủ sóng."""
import numpy as np
import pytest

from leo_coord.orbits import WalkerConstellation
from leo_coord.coverage import footprint_radius_km, point_stats, coverage_grid


def test_footprint_radius_550km_10deg():
    # giá trị tham chiếu: ~1657 km
    assert footprint_radius_km(550.0, 10.0) == pytest.approx(1657.0, abs=15.0)


def test_footprint_grows_with_lower_elevation():
    assert footprint_radius_km(550.0, 5.0) > footprint_radius_km(550.0, 10.0)
    assert footprint_radius_km(1200.0, 10.0) > footprint_radius_km(550.0, 10.0)


def test_point_stats_dense_constellation_full_coverage():
    w = WalkerConstellation("T", 550.0, 53.0, n_sats=60, n_planes=6)
    times = np.arange(0.0, 6 * 3600.0, 60.0)
    sat_ecef = w.ecef_positions(times)
    st = point_stats(sat_ecef, times, 21.0, 105.8, min_elev_deg=10.0)
    assert 0.0 <= st["fraction_covered"] <= 1.0
    assert st["mean_sats_visible"] >= 0.0
    assert st["fraction_covered"] > 0.5  # chòm sao dày tại vĩ độ VN
    assert st["max_gap_min"] >= 0.0


def test_point_stats_polar_no_coverage_equatorial_constellation():
    w = WalkerConstellation("T", 550.0, 10.0, n_sats=12, n_planes=3)
    times = np.arange(0.0, 3 * 3600.0, 60.0)
    sat_ecef = w.ecef_positions(times)
    st = point_stats(sat_ecef, times, 80.0, 0.0, min_elev_deg=25.0)
    assert st["fraction_covered"] == pytest.approx(0.0)


def test_coverage_grid_shapes_and_bounds():
    w = WalkerConstellation("T", 550.0, 53.0, n_sats=24, n_planes=4)
    g = coverage_grid(w, (20.0, 22.0, 104.0, 106.0),
                      grid_step_deg=1.0, min_elev_deg=10.0,
                      t0_unix=0.0, duration_s=3600.0, dt_s=120.0)
    assert g["fraction_covered"].shape == (3, 3)
    assert g["mean_sats_visible"].shape == (3, 3)
    assert np.all((g["fraction_covered"] >= 0.0) & (g["fraction_covered"] <= 1.0))
    assert np.all(g["mean_sats_visible"] >= 0.0)
