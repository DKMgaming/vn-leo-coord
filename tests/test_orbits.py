"""Kiểm thử module quỹ đạo."""
import math
import numpy as np
import pytest

from leo_coord.orbits import (
    CircularOrbit, WalkerConstellation, TLEConstellation,
    gmst_rad, eci_to_ecef, subpoint, elevation_and_range,
    R_EARTH, MU,
)


def test_orbital_period_550km():
    orb = CircularOrbit(550.0, 53.0, 0.0, 0.0)
    assert orb.period_s == pytest.approx(95.53 * 60.0, abs=30.0)


def test_eci_equatorial_t0():
    orb = CircularOrbit(550.0, 0.0, 0.0, 0.0)
    p = orb.eci(0.0)
    assert p[0] == pytest.approx(R_EARTH + 550.0, abs=1e-6)
    assert p[1] == pytest.approx(0.0, abs=1e-9)
    assert p[2] == pytest.approx(0.0, abs=1e-9)


def test_eci_quarter_period():
    orb = CircularOrbit(550.0, 0.0, 0.0, 0.0)
    p = orb.eci(orb.period_s / 4.0)
    assert p[0] == pytest.approx(0.0, abs=1e-6)
    assert p[1] == pytest.approx(R_EARTH + 550.0, abs=1e-6)


def test_gmst_increases_with_time():
    g0 = float(gmst_rad(0.0))
    g1 = float(gmst_rad(3600.0))
    # sau 1 giờ GMST tăng ~15.04 độ
    delta = (g1 - g0) % (2 * math.pi)
    assert delta == pytest.approx(math.radians(15.041), abs=math.radians(0.01))


def test_ecef_norm_preserved_equatorial():
    orb = CircularOrbit(550.0, 0.0, 0.0, 0.0)
    eci = orb.eci(np.array([0.0, 1000.0, 5000.0]))
    ecef = eci_to_ecef(eci, np.array([0.0, 1000.0, 5000.0]))
    r = np.linalg.norm(ecef, axis=-1)
    assert np.allclose(r, R_EARTH + 550.0, atol=1e-6)
    lat, lon, alt = subpoint(ecef)
    assert np.allclose(lat, 0.0, atol=1e-9)
    assert np.allclose(alt, 550.0, atol=1e-6)


def test_elevation_zenith_is_90():
    sat = np.array([[R_EARTH + 550.0, 0.0, 0.0]])
    el, rng = elevation_and_range(sat, 0.0, 0.0)
    assert el[0] == pytest.approx(90.0, abs=1e-9)
    assert rng[0] == pytest.approx(550.0, abs=1e-9)


def test_elevation_below_horizon_negative():
    # vệ tinh ở phía đối diện Trái Đất
    sat = np.array([[-(R_EARTH + 550.0), 0.0, 0.0]])
    el, _ = elevation_and_range(sat, 0.0, 0.0)
    assert el[0] < 0.0


def test_walker_counts_and_planes():
    w = WalkerConstellation("T", 550.0, 53.0, n_sats=12, n_planes=3)
    assert w.size == 12
    assert len(set(np.round(np.degrees(w._raan), 6))) == 3


def test_walker_star_spread():
    w = WalkerConstellation("T", 550.0, 97.0, n_sats=12, n_planes=3, kind="star")
    assert w.size == 12
    assert float(np.degrees(w._raan).max()) == pytest.approx(120.0, abs=1e-9)


def test_walker_ecef_shape():
    w = WalkerConstellation("T", 550.0, 53.0, n_sats=12, n_planes=3)
    ecef = w.ecef_positions(np.array([0.0, 60.0, 120.0]))
    assert ecef.shape == (3, 12, 3)
    r = np.linalg.norm(ecef, axis=-1)
    assert np.allclose(r, R_EARTH + 550.0, atol=1e-6)


def _tle_with_checksum(line):
    s = line[:68].ljust(68)
    c = sum(int(ch) if ch.isdigit() else (1 if ch == "-" else 0) for ch in s) % 10
    return s + str(c)


def test_tle_constellation_basic():
    from datetime import datetime, timezone
    l1 = _tle_with_checksum(
        "1 99999U 26001A   26300.50000000  .00016717  00000-0  10270-3 0  9000")
    l2 = _tle_with_checksum(
        "2 99999  51.6416 247.4627 0006703  69.9862  25.2906 15.72125391    10")
    tle = TLEConstellation("TLE-TEST", [(l1, l2)])
    assert tle.size == 1
    # lan truyền quanh epoch của TLE (2026-10-27 12:00 UTC = ngày 300.5)
    epoch = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc).timestamp()
    ecef = tle.ecef_positions(np.array([epoch, epoch + 600.0]))
    assert ecef.shape == (2, 1, 3)
    assert np.all(np.isfinite(ecef))
    alt = np.linalg.norm(ecef, axis=-1) - R_EARTH
    assert 300.0 < alt[0, 0] < 500.0  # quỹ đạo LEO ~420 km
