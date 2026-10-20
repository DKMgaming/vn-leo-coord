"""Kiểm thử module PFD (Article 21)."""
import pytest

from leo_coord.pfd import pfd_limit, pfd_from_eirp, check_downlink_pfd


def test_limit_ku_low_angle():
    lim, unit, x = pfd_limit(11.0, 3.0)
    assert lim == pytest.approx(-150.0)
    assert unit == "dB(W/m2)/4kHz"
    assert x == pytest.approx(0.0)


def test_limit_ku_high_angle():
    lim, unit, _ = pfd_limit(11.0, 90.0)
    assert lim == pytest.approx(-140.0)


def test_limit_ku_mid_angle_ramp():
    # -150 + 0.5*(20-5) = -142.5 /4kHz  (khớp kiểm tra tay trên trang báo cáo)
    lim, _, _ = pfd_limit(11.0, 20.0)
    assert lim == pytest.approx(-142.5)


def test_limit_ka_band():
    lim, unit, _ = pfd_limit(18.0, 3.0)
    assert lim == pytest.approx(-115.0)
    assert unit == "dB(W/m2)/MHz"
    lim2, _, _ = pfd_limit(18.0, 90.0)
    assert lim2 == pytest.approx(-105.0)


def test_ngso_x_reduction():
    # n = 100 -> X = (5/119)*(100-50) ≈ 2.10 dB
    lim_big, _, x = pfd_limit(11.0, 90.0, n_sats=100)
    lim_small, _, _ = pfd_limit(11.0, 90.0, n_sats=50)
    assert x == pytest.approx((5.0 / 119.0) * 50.0, abs=1e-9)
    assert lim_big == pytest.approx(lim_small - x)
    # n > 288: X = (1/69)*(n+402)
    _, _, x2 = pfd_limit(11.0, 90.0, n_sats=500)
    assert x2 == pytest.approx((500.0 + 402.0) / 69.0, abs=1e-9)


def test_pfd_from_eirp_math():
    # EIRP 40 dBW tại 550 km: 40 - 10log10(4π(5.5e5)^2) ≈ -85.8
    assert pfd_from_eirp(40.0, 550.0) == pytest.approx(-85.8, abs=0.1)


def test_check_downlink_structure():
    r = check_downlink_pfd(40.0, 11.0, 550.0, n_sats=120)
    assert set(r) >= {"pfd", "limit", "margin_db", "compliant", "unit"}
    assert r["margin_db"] == pytest.approx(r["limit"] - r["pfd"])
    assert r["compliant"] == (r["margin_db"] >= 0.0)
    # EIRP demo 40 dBW/MHz vượt xa giới hạn -> không đạt (đúng kỳ vọng vật lý)
    assert r["compliant"] is False


def test_unknown_band_raises():
    with pytest.raises(ValueError):
        pfd_limit(2.0, 10.0)
