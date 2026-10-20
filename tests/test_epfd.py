"""Kiểm thử module EPFD sàng lọc (Article 22)."""
import numpy as np
import pytest

from leo_coord.orbits import WalkerConstellation
from leo_coord.epfd import dish_gmax_dbi, s465_gain_dbi, single_entry_epfd_down


def test_dish_gmax_60cm_12ghz():
    # 0.6m @12GHz, eff 0.6 -> ~35.3 dBi
    assert dish_gmax_dbi(0.6, 12.0) == pytest.approx(35.3, abs=0.3)


def test_s465_envelope():
    gmax = 35.3
    assert float(s465_gain_dbi(0.5, gmax)) == pytest.approx(gmax)
    # 32 - 25log10(2) ≈ 24.47
    assert float(s465_gain_dbi(2.0, gmax)) == pytest.approx(24.47, abs=0.05)
    assert float(s465_gain_dbi(100.0, gmax)) == pytest.approx(-10.0)
    # không vượt quá gmax
    assert float(s465_gain_dbi(1.5, gmax)) <= gmax + 1e-9


def _small_constellation():
    return WalkerConstellation("T", 550.0, 53.0, n_sats=24, n_planes=4)


def test_epfd_linearity_with_eirp():
    w = _small_constellation()
    kw = dict(freq_ghz=12.0, victim_lat=21.0, victim_lon=105.8, gso_lon_deg=105.5,
              dish_d_m=0.6, duration_s=7200.0, dt_s=120.0)
    r1 = single_entry_epfd_down(w, 10.0, **kw)
    r2 = single_entry_epfd_down(w, 20.0, **kw)
    assert r1["n_valid"] > 0 and r2["n_valid"] > 0
    # EPFD tuyến tính theo EIRP: +10 dB EIRP -> +10 dB EPFD
    assert r2["max"] == pytest.approx(r1["max"] + 10.0, abs=0.5)


def test_epfd_percentiles_monotonic():
    w = _small_constellation()
    r = single_entry_epfd_down(w, 10.0, freq_ghz=12.0, victim_lat=21.0,
                               victim_lon=105.8, gso_lon_deg=105.5,
                               duration_s=7200.0, dt_s=120.0)
    vals = list(r["percentiles"].values())
    assert vals == sorted(vals)
    assert r["max"] == pytest.approx(vals[-1])
    assert r["margin_vs_anchor_db"] == pytest.approx(r["anchor_22_1A"] - r["max"])
    assert r["screening_pass"] == (r["max"] <= r["anchor_22_1A"])


def test_epfd_no_visible_sats_graceful():
    # chòm sao xích đạo thấp, nạn nhân ở cực: có thể không có mẫu hợp lệ
    w = WalkerConstellation("T", 550.0, 5.0, n_sats=6, n_planes=2)
    r = single_entry_epfd_down(w, 10.0, freq_ghz=12.0, victim_lat=85.0,
                               victim_lon=0.0, gso_lon_deg=0.0,
                               duration_s=3600.0, dt_s=300.0)
    assert r["n_samples"] == 12
    assert r["n_valid"] <= r["n_samples"]
