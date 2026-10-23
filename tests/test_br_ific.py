"""Kiểm thử mô-đun quét công báo quốc tế ITU BR IFIC và bộ lọc 3 lớp bảo vệ Vinasat."""
from datetime import date
import pytest

from leo_coord.br_ific import (
    load_br_ific_data,
    check_frequency_overlap,
    calculate_4month_deadline,
    scan_br_ific_notices
)


def test_load_br_ific_data():
    data = load_br_ific_data()
    assert "notices" in data
    assert len(data["notices"]) >= 5
    ids = [n["id"] for n in data["notices"]]
    assert "USASAT-NGSO-3-MOD" in ids
    assert "CHNSAT-NGSO-1" in ids


def test_frequency_overlap_starlink():
    # Starlink Ku phát 10.7-12.7 GHz chồng lấn Vinasat Ku (10.95-12.75 GHz)
    bands = [{"band_name": "Ku DL", "freq_range_ghz": [10.7, 12.7]}]
    has_overlap, overlaps = check_frequency_overlap(bands)
    assert has_overlap is True
    assert len(overlaps) == 1
    assert overlaps[0]["overlap_range_ghz"] == [10.95, 12.7]


def test_frequency_overlap_vhf():
    # Kineis IoT phát 0.4 GHz không chồng lấn Vinasat (C & Ku)
    bands = [{"band_name": "VHF MSS", "freq_range_ghz": [0.401, 0.403]}]
    has_overlap, overlaps = check_frequency_overlap(bands)
    assert has_overlap is False
    assert len(overlaps) == 0


def test_calculate_4month_deadline():
    # Thử nghiệm với ngày tham chiếu giả định
    pub_date = "2026-08-01"
    ref_date_normal = date(2026, 8, 15)  # Sau 14 ngày -> còn ~108 ngày -> MONITORING
    d_norm = calculate_4month_deadline(pub_date, ref_date=ref_date_normal)
    assert d_norm["status"] == "MONITORING"
    assert d_norm["days_remaining"] > 90

    # Sau 100 ngày -> còn ~22 ngày -> URGENT_ACTION
    ref_date_urgent = date(2026, 11, 10)
    d_urg = calculate_4month_deadline(pub_date, ref_date=ref_date_urgent)
    assert d_urg["status"] == "URGENT_ACTION"
    assert 0 < d_urg["days_remaining"] <= 30

    # Sau 130 ngày -> hết hạn -> EXPIRED
    ref_date_exp = date(2026, 12, 15)
    d_exp = calculate_4month_deadline(pub_date, ref_date=ref_date_exp)
    assert d_exp["status"] == "EXPIRED"
    assert d_exp["days_remaining"] < 0


def test_scan_br_ific_notices():
    scan_res = scan_br_ific_notices(ref_date=date(2026, 10, 23))
    assert scan_res["status"] == "success"
    assert scan_res["total_notices_scanned"] >= 5
    # Starlink và Guowang phải được phân loại HIGH_RISK (cần phản đối)
    notices = {n["id"]: n for n in scan_res["notices"]}
    assert notices["USASAT-NGSO-3-MOD"]["risk_level"] == "HIGH_RISK"
    assert notices["CHNSAT-NGSO-1"]["risk_level"] == "HIGH_RISK"
    assert "RR No. 9.7B" in notices["USASAT-NGSO-3-MOD"]["applicable_provisions"]

    # Kineis IoT (VHF) không chồng lấn tần số -> LOW_RISK
    assert notices["FRASAT-LEO-IOT"]["risk_level"] == "LOW_RISK"
