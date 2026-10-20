"""Kiểm thử module phối hợp tần số."""
import numpy as np
import pytest

from leo_coord.orbits import WalkerConstellation
from leo_coord.coordination import (
    coordination_arc, bands_overlap, pfd_trigger_9_7,
    delta_t_over_t_percent, coordination_triggered_by_delta_t,
    screen_ngso_vs_gso,
)


def test_coordination_arc_values():
    assert coordination_arc(12.0) == pytest.approx(6.0)   # Ku
    assert coordination_arc(4.0) == pytest.approx(7.0)    # C
    assert coordination_arc(20.0) == pytest.approx(8.0)  # Ka


def test_bands_overlap():
    assert bands_overlap((10.7, 12.7), (11.7, 12.2)) is True
    assert bands_overlap((10.7, 11.0), (12.0, 12.7)) is False
    assert bands_overlap((10.7, 12.7), (12.7, 14.0)) is True  # chạm biên


def test_pfd_trigger_9_7():
    v, u = pfd_trigger_9_7(11.0)
    assert v == pytest.approx(-174.5)
    assert "40kHz" in u
    assert pfd_trigger_9_7(6.0) is None


def test_delta_t_over_t_plausible():
    # nạn nhân G/T=20 dB/K, B=1 MHz, f=4 GHz, pfd=-160 dBW/m2/Hz -> ~32%
    dt = delta_t_over_t_percent(-160.0, 4.0, 20.0, 1e6)
    assert dt == pytest.approx(32.0, rel=0.15)
    assert coordination_triggered_by_delta_t(dt) is True
    assert coordination_triggered_by_delta_t(3.0) is False
    assert coordination_triggered_by_delta_t(6.0) is False  # ngưỡng: >6%


def test_screen_ngso_vs_gso_runs():
    w = WalkerConstellation("T", 550.0, 53.0, n_sats=24, n_planes=4)
    pts = [(21.0285, 105.8542, "Ha Noi"), (10.8231, 106.6297, "TP.HCM")]
    r = screen_ngso_vs_gso(w, 12.0, 10.0, 105.5, pts,
                           duration_s=7200.0, dt_s=300.0)
    assert r["coordination_arc_deg"] == pytest.approx(6.0)
    assert isinstance(r["coordination_likely_required"], bool)
    assert len(r["per_point"]) == 2
    assert r["min_separation_deg"] is not None
    # chòm sao dày 550 km chắc chắn có lúc lọt vào cung ±6° nhìn từ VN
    assert r["coordination_likely_required"] is True
    assert len(r["reasons"]) >= 1
