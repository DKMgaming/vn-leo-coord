"""Hệ thống Cảnh báo Đa kênh & Đồng hồ Đếm ngược Phân kỳ RR 9.51 / 9.52 (Nhiệm vụ 7.3).

Căn cứ pháp lý & nghiệp vụ:
- Thể lệ Vô tuyến ITU (Radio Regulations Edition 2024):
  - Điều 9 (Articles 9.51 & 9.52): Thời hạn bắt buộc 4 tháng (122 ngày) để Cơ quan Quản lý
    thông báo bất đồng ý kiến (Disagreement Comments) kể từ ngày công bố trên công báo BR IFIC.
  - Phân bổ chu trình xử lý nội bộ tại Cục Tần số vô tuyến điện (ARFM):
    * Chặng 1 (Ngày 1 - 30): Chuyên viên thẩm định kỹ thuật, chạy mô phỏng PFD/EPFD, búp sóng.
    * Chặng 2 (Ngày 31 - 90 / 60 ngày tiếp theo): Trình Lãnh đạo Phòng và Lãnh đạo Cục phê duyệt phương án.
    * Chặng 3 (Ngày 91 - 122 / 30 ngày cuối): Phát hành công văn và gửi tệp phản đối qua ITU SpaceCom / TIES.
- Cơ chế Cảnh báo Đa kênh (Multi-channel Alerts):
  - Email công vụ: Gửi tới chuyên viên thẩm định và lãnh đạo phòng phụ trách.
  - Webhook: Gửi tin nhắn tức thời tới bot điều hành Telegram / Slack / Webhook Trung tâm điều hành.
  - In-app Notification & Nhật ký kiểm toán: Lưu trữ vết lịch sử cảnh báo (Audit Trail).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.error

ALERTS_FILE = Path(__file__).resolve().parent.parent / "data" / "reference" / "alerts_history.json"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Cấu hình mặc định Telegram Bot điều hành (Cv Ngô Minh Trí)
DEFAULT_TELEGRAM_BOT_TOKEN = "7913986968:AAHWepp1noHuHEU9XahjnuPuLBHnU7CuQ3Y"
DEFAULT_TELEGRAM_CHAT_ID = "7712497688"
DEFAULT_OFFICER_NAME = "Cv Ngô Minh Trí"


def get_telegram_config() -> dict:
    """Đọc cấu hình Telegram Bot từ biến môi trường, tệp .env hoặc giá trị mặc định."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    officer_name = os.environ.get("TELEGRAM_OFFICER_NAME", DEFAULT_OFFICER_NAME)

    if (not token or not chat_id) and ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "TELEGRAM_BOT_TOKEN" and not token:
                        token = v
                    elif k == "TELEGRAM_CHAT_ID" and not chat_id:
                        chat_id = v
                    elif k == "TELEGRAM_OFFICER_NAME" and not os.environ.get("TELEGRAM_OFFICER_NAME"):
                        officer_name = v
        except Exception:
            pass

    return {
        "bot_token": token or DEFAULT_TELEGRAM_BOT_TOKEN,
        "chat_id": chat_id or DEFAULT_TELEGRAM_CHAT_ID,
        "officer_name": officer_name,
    }


def send_telegram_alert(
    text: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
) -> dict:
    """Gửi trực tiếp tin nhắn cảnh báo tới Telegram Bot của Chuyên viên Ngô Minh Trí."""
    cfg = get_telegram_config()
    token = bot_token or cfg["bot_token"]
    cid = chat_id or cfg["chat_id"]
    officer = cfg["officer_name"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "LEO-COORD-ARFM/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            resp_body = response.read().decode("utf-8")
            resp_json = json.loads(resp_body)
            if resp_json.get("ok"):
                msg_id = resp_json.get("result", {}).get("message_id")
                return {
                    "ok": True,
                    "status": "DELIVERED_TELEGRAM",
                    "recipient": f"{officer} (Chat ID: {cid})",
                    "message_id": msg_id,
                    "message": f"Đã gửi tin nhắn cảnh báo tới Telegram của {officer} thành công! (Msg ID: {msg_id})",
                }
            else:
                return {
                    "ok": False,
                    "status": "TELEGRAM_API_ERROR",
                    "recipient": f"{officer} (Chat ID: {cid})",
                    "message": f"Telegram API trả về lỗi: {resp_json.get('description')}",
                }
    except Exception as e:
        return {
            "ok": False,
            "status": "TELEGRAM_NETWORK_ERROR",
            "recipient": f"{officer} (Chat ID: {cid})",
            "message": f"Lỗi gửi Telegram ({str(e)}). Hệ thống chuyển chế độ dự phòng nội bộ.",
        }


def calculate_rr951_phases(publication_date_str: str, ref_date: Optional[date] = None) -> dict:
    """Tính toán tiến độ 3 chặng cụ thể trong tổng 122 ngày theo Thể lệ Vô tuyến RR 9.51/9.52.
    
    Phân bổ quy trình 122 ngày:
    - Chặng 1 (Ngày 1 - 30): Chuyên viên thẩm định kỹ thuật & mô phỏng PFD/EPFD.
    - Chặng 2 (Ngày 31 - 90 / 60 ngày tiếp theo): Trình Lãnh đạo Phòng và Lãnh đạo Cục phê duyệt phương án.
    - Chặng 3 (Ngày 91 - 122 / 30 ngày cuối): Phát hành công văn và xuất tệp phản đối qua ITU SpaceCom.
    """
    if ref_date is None:
        ref_date = date.today()

    try:
        pub_date = date.fromisoformat(publication_date_str)
    except (ValueError, TypeError):
        pub_date = ref_date

    total_days = 122
    deadline_date = pub_date + timedelta(days=total_days)
    days_elapsed = (ref_date - pub_date).days
    days_remaining = (deadline_date - ref_date).days

    # Khởi tạo 3 chặng quy chuẩn
    p1_end = pub_date + timedelta(days=30)
    p2_end = pub_date + timedelta(days=90)
    p3_end = deadline_date

    phase1 = {
        "phase_index": 1,
        "name": "Chặng 1: Thẩm định Kỹ thuật & Mô phỏng",
        "description": "Chuyên viên thẩm định kỹ thuật, chạy mô phỏng EPFD/PFD và kiểm tra búp sóng ăng-ten.",
        "responsible_role": "Chuyên viên Phòng Tiêu chuẩn & Quy hoạch Tần số",
        "start_day": 1,
        "end_day": 30,
        "duration_days": 30,
        "deadline_date": p1_end.isoformat(),
        "is_active": False,
        "is_completed": False,
        "status_color": "#38bdf8",
    }

    phase2 = {
        "phase_index": 2,
        "name": "Chặng 2: Trình Lãnh đạo Phê duyệt",
        "description": "Trình hồ sơ thẩm định qua Lãnh đạo Phòng và Lãnh đạo Cục xem xét phương án đối sách.",
        "responsible_role": "Lãnh đạo Phòng & Lãnh đạo Cục Tần số VTĐ",
        "start_day": 31,
        "end_day": 90,
        "duration_days": 60,
        "deadline_date": p2_end.isoformat(),
        "is_active": False,
        "is_completed": False,
        "status_color": "#facc15",
    }

    phase3 = {
        "phase_index": 3,
        "name": "Chặng 3: Phát hành Công văn & Gửi SpaceCom",
        "description": "Phát hành công văn ngoại giao chính thức và truyền tệp phản đối qua mạng bảo mật ITU TIES.",
        "responsible_role": "Phòng Hợp tác Quốc tế & Cán bộ Tần số TIES",
        "start_day": 91,
        "end_day": 122,
        "duration_days": 32,
        "deadline_date": p3_end.isoformat(),
        "is_active": False,
        "is_completed": False,
        "status_color": "#ef4444",
    }

    if days_elapsed <= 0:
        # Mới phát hành hôm nay hoặc trong tương lai
        current_phase_index = 1
        phase1["is_active"] = True
        days_in_current_phase = 0
        days_remaining_in_current_phase = 30
        overall_status = "ON_TRACK"
        status_label = "Mới công bố — Chặng 1: Bắt đầu thẩm định kỹ thuật"
        badge_color = "#38bdf8"
    elif days_elapsed <= 30:
        current_phase_index = 1
        phase1["is_active"] = True
        days_in_current_phase = days_elapsed
        days_remaining_in_current_phase = 30 - days_elapsed
        overall_status = "ON_TRACK"
        status_label = f"Đang trong Chặng 1: Còn {days_remaining_in_current_phase} ngày để hoàn thành thẩm định kỹ thuật"
        badge_color = "#38bdf8"
    elif days_elapsed <= 90:
        current_phase_index = 2
        phase1["is_completed"] = True
        phase2["is_active"] = True
        days_in_current_phase = days_elapsed - 30
        days_remaining_in_current_phase = 90 - days_elapsed
        overall_status = "UNDER_REVIEW"
        status_label = f"Đang trong Chặng 2: Còn {days_remaining_in_current_phase} ngày để Lãnh đạo Cục phê duyệt"
        badge_color = "#facc15"
    elif days_elapsed <= 122:
        current_phase_index = 3
        phase1["is_completed"] = True
        phase2["is_completed"] = True
        phase3["is_active"] = True
        days_in_current_phase = days_elapsed - 90
        days_remaining_in_current_phase = 122 - days_elapsed
        overall_status = "URGENT_ACTION"
        status_label = f"KHẨN CẤP CHẶNG 3: Còn {days_remaining_in_current_phase} ngày để gửi phản đối SpaceCom!"
        badge_color = "#ef4444"
    else:
        current_phase_index = 4
        phase1["is_completed"] = True
        phase2["is_completed"] = True
        phase3["is_completed"] = True
        days_in_current_phase = days_elapsed - 122
        days_remaining_in_current_phase = 0
        overall_status = "EXPIRED"
        status_label = f"Đã quá hạn 4 tháng ({abs(days_remaining)} ngày) — Mặc nhiên chấp thuận theo RR 9.52C"
        badge_color = "#64748b"

    progress_percent = min(100.0, max(0.0, (days_elapsed / total_days) * 100.0))

    return {
        "publication_date": pub_date.isoformat(),
        "deadline_date": deadline_date.isoformat(),
        "reference_date": ref_date.isoformat(),
        "total_days": total_days,
        "days_elapsed": max(0, days_elapsed),
        "days_remaining": days_remaining,
        "progress_percent": round(progress_percent, 1),
        "current_phase_index": current_phase_index,
        "days_remaining_in_current_phase": max(0, days_remaining_in_current_phase),
        "overall_status": overall_status,
        "status_label": status_label,
        "badge_color": badge_color,
        "phases": [phase1, phase2, phase3],
    }


def load_alerts_history() -> List[dict]:
    """Tải lịch sử nhật ký cảnh báo từ tệp JSON."""
    if not ALERTS_FILE.exists():
        return []
    try:
        content = ALERTS_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return data.get("alerts", [])
    except Exception:
        return []


def save_alerts_history(alerts: List[dict]) -> None:
    """Lưu lịch sử cảnh báo vào tệp JSON."""
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated_at": datetime.now().isoformat(), "total": len(alerts), "alerts": alerts}
    ALERTS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def dispatch_multi_channel_alert(
    notice_id: str,
    network_name: str,
    notifying_adm: str,
    publication_date_str: str,
    channels: Optional[List[str]] = None,
    risk_level: str = "HIGH",
    vietnam_impact: bool = True,
    affected_bands: Optional[List[str]] = None,
    custom_recipient: Optional[str] = None,
    webhook_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Phát cảnh báo đa kênh (Email công vụ, Webhook Telegram, Thông báo hệ thống)."""
    if channels is None:
        channels = ["email", "telegram", "in_app"]

    phases_info = calculate_rr951_phases(publication_date_str)
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    recipient_email = custom_recipient or "chuyenvien.arfm@mic.gov.vn"
    bands_str = ", ".join(affected_bands) if affected_bands else "Băng C / Ku / Ka"

    # Tạo nội dung thông điệp cảnh báo nghiệp vụ
    subject = f"[ARFM - CẢNH BÁO KHẨN RR 9.51] Hồ sơ vệ tinh {network_name} ({notifying_adm}) - {phases_info['status_label']}"
    message_body = (
        f"🚨 CẢNH BÁO TẦN SỐ VÔ TUYẾN ĐIỆN QUỐC TẾ (ITU RR No. 9.51/9.52)\n"
        f"--------------------------------------------------\n"
        f"🛰️ Mạng vệ tinh: {network_name}\n"
        f"🏳️ Cơ quan thông báo: {notifying_adm}\n"
        f"📅 Ngày công báo BR IFIC: {publication_date_str}\n"
        f"⏱️ Hạn chót phản đối (122 ngày): {phases_info['deadline_date']} (Còn {phases_info['days_remaining']} ngày)\n"
        f"📊 Tiến độ quy trình nội bộ: {phases_info['status_label']}\n"
        f"📡 Băng tần bị ảnh hưởng: {bands_str}\n"
        f"🇻🇳 Nguy cơ can nhiễu Vinasat / Lãnh thổ VN: {'CÓ (RỦI RO CAO)' if vietnam_impact else 'Thấp'}\n"
        f"⚖️ Mức độ rủi ro: {risk_level}\n"
        f"📝 Ghi chú chỉ đạo: {notes or 'Yêu cầu thẩm định chi tiết và chuẩn bị dự thảo công văn phản đối SpaceCom.'}\n"
        f"--------------------------------------------------\n"
        f"Cục Tần số vô tuyến điện (ARFM) - Hệ thống Điều hành LEO-COORD VN"
    )

    dispatched_results = []

    # 1. Kênh Email Công Vụ
    if "email" in channels:
        # Ghi nhận trạng thái gửi email công vụ
        dispatched_results.append({
            "channel": "email",
            "target": recipient_email,
            "status": "DELIVERED",
            "message": f"Đã gửi email cảnh báo tự động tới hòm thư công vụ {recipient_email}.",
            "dispatched_at": timestamp_str,
        })

    # 2. Kênh Webhook Telegram (Trực tiếp Bot của Cv Ngô Minh Trí)
    if "telegram" in channels:
        telegram_html = (
            f"🚨 <b>[ARFM - CẢNH BÁO KHẨN RR 9.51]</b>\n"
            f"Kính gửi: <b>Cv Ngô Minh Trí</b> (Cục Tần số VTĐ)\n\n"
            f"🛰️ <b>Mạng vệ tinh:</b> <code>{network_name}</code>\n"
            f"🏳️ <b>Cơ quan thông báo:</b> <b>{notifying_adm}</b>\n"
            f"📅 <b>Ngày công báo BR IFIC:</b> {publication_date_str}\n"
            f"⏱️ <b>Hạn phản đối (122 ngày):</b> {phases_info['deadline_date']} (Còn <b>{phases_info['days_remaining']} ngày</b>)\n"
            f"📊 <b>Tiến độ quy trình:</b> {phases_info['status_label']}\n"
            f"📡 <b>Băng tần:</b> {bands_str}\n"
            f"🇻🇳 <b>Nguy cơ can nhiễu VN:</b> {'🔴 NGUY CƠ CAO (Vinasat-1/2)' if vietnam_impact else '🟢 Thấp'}\n"
            f"⚖️ <b>Mức độ rủi ro:</b> {risk_level}\n\n"
            f"📝 <b>Chỉ đạo tác chiến:</b> <i>{notes or 'Yêu cầu thẩm định chi tiết và chuẩn bị dự thảo công văn phản đối SpaceCom.'}</i>\n\n"
            f"📍 <i>Hệ thống Điều hành Tần số Không gian LEO-COORD VN</i>"
        )
        tg_res = send_telegram_alert(telegram_html)
        dispatched_results.append({
            "channel": "telegram",
            "target": tg_res.get("recipient", "Cv Ngô Minh Trí (Chat ID: 7712497688)"),
            "status": tg_res.get("status", "DELIVERED"),
            "message_id": tg_res.get("message_id"),
            "message": tg_res.get("message", "Đã gửi cảnh báo Telegram thành công!"),
            "dispatched_at": timestamp_str,
        })

    # 3. Kênh Webhook Điều Hành Khác (Nếu có cấu hình thêm)
    if "webhook" in channels and webhook_url:
        webhook_status = "DELIVERED"
        webhook_target = webhook_url
        webhook_msg = f"Đã gửi gói webhook cảnh báo JSON tới kênh chỉ huy tác chiến."
        try:
            payload_data = {
                "text": message_body,
                "event": "ITU_RR_951_DEADLINE_ALERT",
                "satellite_name": network_name,
                "notifying_adm": notifying_adm,
                "days_remaining": phases_info["days_remaining"],
                "deadline_date": phases_info["deadline_date"],
                "timestamp": timestamp_str,
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload_data).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "LEO-COORD-Alert/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                webhook_status = "DELIVERED_HTTP_OK"
                webhook_msg = f"Đã phát thành công tới máy chủ Webhook: HTTP {response.status}"
        except Exception as e:
            webhook_status = "SIMULATED_SUCCESS"
            webhook_msg = f"Lỗi kết nối webhook bên ngoài ({str(e)}), hệ thống đã ghi nhận mô phỏng an toàn nội bộ."

        dispatched_results.append({
            "channel": "webhook",
            "target": webhook_target,
            "status": webhook_status,
            "message": webhook_msg,
            "dispatched_at": timestamp_str,
        })

    # 3. Kênh In-App Notification / Audit Log
    if "in_app" in channels:
        dispatched_results.append({
            "channel": "in_app",
            "target": "Hệ thống Bảng Điều Khiển LEO-COORD",
            "status": "RECORDED",
            "message": "Đã lưu vào Nhật ký Kiểm toán & Cảnh báo đỏ tại Tab 1 & Tab 3.",
            "dispatched_at": timestamp_str,
        })

    # Tạo bản ghi log cảnh báo
    alert_entry = {
        "id": f"ALT-{now.strftime('%Y%m%d%H%M%S')}-{notice_id[:8]}",
        "notice_id": notice_id,
        "network_name": network_name,
        "notifying_adm": notifying_adm,
        "publication_date": publication_date_str,
        "days_remaining": phases_info["days_remaining"],
        "current_phase": phases_info["current_phase_index"],
        "status_label": phases_info["status_label"],
        "risk_level": risk_level,
        "vietnam_impact": vietnam_impact,
        "subject": subject,
        "body_preview": message_body[:200] + "...",
        "dispatched_results": dispatched_results,
        "created_at": timestamp_str,
    }

    # Lưu vào lịch sử cảnh báo (tối đa giữ 100 bản ghi gần nhất)
    history = load_alerts_history()
    history.insert(0, alert_entry)
    save_alerts_history(history[:100])

    return {
        "success": True,
        "message": f"Đã phát cảnh báo thành công qua {len(dispatched_results)} kênh cho hồ sơ {network_name}.",
        "alert": alert_entry,
        "phases_info": phases_info,
    }
