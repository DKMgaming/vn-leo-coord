"""Unit tests cho module leo_coord.n2yo_client."""
from unittest.mock import patch, MagicMock
import json
import pytest

from leo_coord.n2yo_client import (
    N2YOClient,
    get_default_tracked_satellites,
    evaluate_satellite_live,
    VIETNAM_GROUND_STATIONS,
)


def test_default_tracked_satellites():
    sats = get_default_tracked_satellites()
    assert len(sats) >= 5
    ids = [s["norad_id"] for s in sats]
    assert 32767 in ids  # VINASAT-1
    assert 38332 in ids  # VINASAT-2
    assert 25544 in ids  # ISS


def test_vietnam_ground_stations():
    assert "hanoi" in VIETNAM_GROUND_STATIONS
    assert "danang" in VIETNAM_GROUND_STATIONS
    assert "hcmc" in VIETNAM_GROUND_STATIONS
    assert "viettri" in VIETNAM_GROUND_STATIONS
    assert "bacninh" in VIETNAM_GROUND_STATIONS
    assert VIETNAM_GROUND_STATIONS["hanoi"]["lat"] == pytest.approx(21.0285)
    assert VIETNAM_GROUND_STATIONS["viettri"]["lat"] == pytest.approx(21.3283)
    assert VIETNAM_GROUND_STATIONS["viettri"]["lng"] == pytest.approx(105.3566)
    assert VIETNAM_GROUND_STATIONS["bacninh"]["lat"] == pytest.approx(21.136356)
    assert VIETNAM_GROUND_STATIONS["bacninh"]["lng"] == pytest.approx(106.074508)


@patch("urllib.request.urlopen")
def test_get_tle_mock(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "info": {"satname": "VINASAT 1", "satid": 32767},
        "tle": "1 32767U ...\n2 32767 ..."
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = N2YOClient(api_key="TEST_KEY")
    res = client.get_tle(32767)
    assert res["info"]["satname"] == "VINASAT 1"
    assert "tle" in res


@patch("urllib.request.urlopen")
def test_evaluate_satellite_live_mock(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "info": {"satname": "SPACE STATION", "satid": 25544},
        "positions": [{
            "satlatitude": 16.5,
            "satlongitude": 108.0,
            "sataltitude": 420.0,
            "azimuth": 45.0,
            "elevation": 75.0,
            "ra": 100.0,
            "dec": 15.0,
            "timestamp": 1700000000,
            "eclipsed": False
        }]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = N2YOClient(api_key="TEST_KEY")
    res = evaluate_satellite_live(25544, client=client)

    assert res["norad_id"] == 25544
    assert res["orbit_type"] == "LEO"
    assert res["has_coverage_vietnam"] is True
    assert res["max_elevation_deg"] > 10.0
    assert len(res["stations"]) == 5


def test_calculate_look_angles():
    from leo_coord.n2yo_client import calculate_look_angles
    # Vệ tinh ngay trên đỉnh đầu trạm ở độ cao 550km
    el, az, slant, comp = calculate_look_angles(21.03, 105.85, 10, 21.03, 105.85, 550.0)
    assert el == pytest.approx(90.0, abs=0.1)
    assert slant == pytest.approx(550.0, abs=1.0)

    # Vệ tinh chếch về phía bắc
    el_n, az_n, slant_n, comp_n = calculate_look_angles(21.03, 105.85, 10, 22.03, 105.85, 550.0)
    assert el_n < 90.0
    assert az_n == pytest.approx(0.0, abs=0.5)
    assert "N" in comp_n


@patch("urllib.request.urlopen")
def test_satellite_orbit_track_sgp4(mock_urlopen):
    from leo_coord.n2yo_client import get_satellite_orbit_track

    # Mock TLE của Trạm Vũ Trụ Quốc Tế (ISS - NORAD 25544)
    iss_tle = (
        "1 25544U 98067A   26116.51234567  .00016717  00000+0  10270-3 0  9993\r\n"
        "2 25544  51.6412 110.1234 0005432  65.1234  45.1234 15.50123456456789"
    )
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "info": {"satname": "SPACE STATION", "satid": 25544},
        "tle": iss_tle
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = N2YOClient(api_key="TEST_KEY")
    res = get_satellite_orbit_track(25544, client=client, n_steps=60)

    assert res["status"] == "success"
    assert res["norad_id"] == 25544
    assert res["method"] == "SGP4_TLE"
    assert res["period_min"] > 80.0
    assert res["inclination_deg"] == pytest.approx(51.64, abs=0.1)
    assert len(res["points"]) >= 50
    assert "lat" in res["points"][0]
    assert "lon" in res["points"][0]
    assert "alt_km" in res["points"][0]


@patch("urllib.request.urlopen")
def test_satellite_orbit_track_analytic_fallback(mock_urlopen):
    from leo_coord.n2yo_client import get_satellite_orbit_track

    # TLE lỗi -> rơi về Analytic Keplerian
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "error": "TLE not available"
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = N2YOClient(api_key="TEST_KEY")
    res = get_satellite_orbit_track(99999, client=client, n_steps=45)

    assert res["status"] == "success"
    assert res["norad_id"] == 99999
    assert res["method"] in ["ANALYTIC_KEPLERIAN", "GSO_CIRCULAR"]
    assert len(res["points"]) >= 30


