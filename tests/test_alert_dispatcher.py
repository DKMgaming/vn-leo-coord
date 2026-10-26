"""
Unit tests cho Nhiệm vụ 7.3: Hệ thống Cảnh báo Đa kênh & Đồng hồ Đếm ngược Phân kỳ RR 9.51/9.52.
Kiểm tra:
- Tính toán chính xác 3 chặng quy chuẩn trong 122 ngày (Chặng 1: 1-30d, Chặng 2: 31-90d, Chặng 3: 91-122d)
- Phát cảnh báo đa kênh (Email công vụ, Webhook Telegram / LAN, In-app notification)
- Lưu trữ và truy xuất vết nhật ký kiểm toán cảnh báo (Audit Trail)
- Các endpoint API FastAPI tương ứng.
"""
from datetime import date, timedelta
from pathlib import Path
import pytest

from leo_coord.alert_dispatcher import (
    calculate_rr951_phases,
    dispatch_multi_channel_alert,
    load_alerts_history,
    save_alerts_history,
)
from web.app import (
    app,
    get_rr951_phases_endpoint,
    dispatch_srs_alert_endpoint,
    get_alerts_history_endpoint,
)


def test_calculate_rr951_phases_stage1():
    # Ngày tham chiếu là 10 ngày sau ngày công báo -> Chặng 1
    ref = date(2026, 3, 11)
    res = calculate_rr951_phases("2026-03-01", ref_date=ref)

    assert res["total_days"] == 122
    assert res["days_elapsed"] == 10
    assert res["days_remaining"] == 112
    assert res["current_phase_index"] == 1
    assert res["overall_status"] == "ON_TRACK"
    assert res["phases"][0]["is_active"] is True
    assert res["phases"][1]["is_active"] is False


def test_calculate_rr951_phases_stage2():
    # Ngày tham chiếu là 50 ngày sau ngày công báo -> Chặng 2 (Trình Lãnh đạo Cục)
    ref = date(2026, 4, 20)
    res = calculate_rr951_phases("2026-03-01", ref_date=ref)

    assert res["days_elapsed"] == 50
    assert res["days_remaining"] == 72
    assert res["current_phase_index"] == 2
    assert res["overall_status"] == "UNDER_REVIEW"
    assert res["phases"][0]["is_completed"] is True
    assert res["phases"][1]["is_active"] is True
    assert res["phases"][2]["is_active"] is False


def test_calculate_rr951_phases_stage3():
    # Ngày tham chiếu là 100 ngày sau ngày công báo -> Chặng 3 (Khẩn cấp gửi SpaceCom)
    ref = date(2026, 6, 9)
    res = calculate_rr951_phases("2026-03-01", ref_date=ref)

    assert res["days_elapsed"] == 100
    assert res["days_remaining"] == 22
    assert res["current_phase_index"] == 3
    assert res["overall_status"] == "URGENT_ACTION"
    assert res["phases"][0]["is_completed"] is True
    assert res["phases"][1]["is_completed"] is True
    assert res["phases"][2]["is_active"] is True


def test_calculate_rr951_phases_expired():
    # Ngày tham chiếu là 130 ngày sau -> Quá hạn 4 tháng
    ref = date(2026, 7, 9)
    res = calculate_rr951_phases("2026-03-01", ref_date=ref)

    assert res["current_phase_index"] == 4
    assert res["overall_status"] == "EXPIRED"
    assert res["days_remaining"] < 0


def test_dispatch_multi_channel_alert():
    res = dispatch_multi_channel_alert(
        notice_id="TEST_NOTICE_001",
        network_name="TEST-STARLINK-V",
        notifying_adm="USA",
        publication_date_str="2026-03-01",
        channels=["email", "telegram", "in_app"],
        risk_level="HIGH",
        vietnam_impact=True,
        custom_recipient="chuyenvien.arfm@mic.gov.vn",
        notes="Hồ sơ xâm lấn Vinasat-1, cần gửi phản đối khẩn cấp."
    )

    assert res["success"] is True
    alert = res["alert"]
    assert alert["network_name"] == "TEST-STARLINK-V"
    assert alert["notifying_adm"] == "USA"
    assert len(alert["dispatched_results"]) == 3

    channels_dispatched = [r["channel"] for r in alert["dispatched_results"]]
    assert "email" in channels_dispatched
    assert "webhook" in channels_dispatched
    assert "in_app" in channels_dispatched

    # Kiểm tra lưu vào lịch sử
    history = load_alerts_history()
    assert len(history) > 0
    assert any(a["id"] == alert["id"] for a in history)


def test_api_srs_phases_endpoint():
    data = get_rr951_phases_endpoint("2026-03-01")
    assert data["total_days"] == 122
    assert len(data["phases"]) == 3
    assert "progress_percent" in data


def test_api_srs_alert_dispatch_and_history():
    payload = {
        "notice_id": "API_TEST_002",
        "network_name": "API-KUIPER-V",
        "notifying_adm": "USA",
        "publication_date": "2026-03-01",
        "channels": ["email", "in_app"],
        "custom_recipient": "kiemsoat.arfm@mic.gov.vn",
        "risk_level": "HIGH",
        "vietnam_impact": True,
        "notes": "Kiểm thử API dispatch alert"
    }

    post_data = dispatch_srs_alert_endpoint(payload)
    assert post_data["success"] is True
    alert_id = post_data["alert"]["id"]

    hist_data = get_alerts_history_endpoint()
    assert hist_data["total"] > 0
    ids = [a["id"] for a in hist_data["alerts"]]
    assert alert_id in ids

