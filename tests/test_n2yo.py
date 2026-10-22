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
    assert VIETNAM_GROUND_STATIONS["hanoi"]["lat"] == pytest.approx(21.0285)


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
    assert len(res["stations"]) == 3
