"""Xuất báo cáo đánh giá chòm sao LEO/NGSO (HTML tiếng Việt)."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

CSS = """
body{font-family:Arial,Helvetica,sans-serif;max-width:1000px;margin:24px auto;
padding:0 16px;color:#1a1a1a;line-height:1.55}
h1{font-size:22px;border-bottom:3px solid #0b5cad;padding-bottom:8px}
h2{font-size:17px;color:#0b5cad;margin-top:28px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px}
th,td{border:1px solid #ccc;padding:6px 10px;text-align:left}
th{background:#eef4fb}
.banner{background:#fff3cd;border:1px solid #e0a800;padding:10px 14px;
border-radius:6px;margin:12px 0;font-size:14px}
.ok{color:#0a7a2e;font-weight:bold}.bad{color:#c00;font-weight:bold}
.warn{color:#b26a00;font-weight:bold}
.meta{color:#555;font-size:13px}
.footer{margin-top:32px;font-size:12px;color:#666;border-top:1px solid #ddd;
padding-top:10px}
"""

STATUS_CLASS = {"DAT": "ok", "TRE_HAN": "bad", "CHUA_DEN_HAN": "warn"}


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _row(cells):
    return "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in cells) + "</tr>"


def build_html(a: dict) -> str:
    """Dựng báo cáo HTML từ dict kết quả đánh giá (xem cli.build_assessment)."""
    now_vn = (datetime.now(timezone.utc) + timedelta(hours=7)).strftime(
        "%d/%m/%Y %H:%M (giờ VN)")
    parts = [f"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<title>Báo cáo đánh giá {_esc(a['name'])}</title><style>{CSS}</style></head><body>"""]
    parts.append(f"<h1>Đánh giá chòm sao LEO/NGSO: {_esc(a['name'])}</h1>")
    parts.append(f"<p class='meta'>Ngày lập: {now_vn} · Công cụ leo_coord "
                 f"(sàng lọc kỹ thuật)</p>")
    if a.get("fictional"):
        parts.append("<div class='banner'><b>DỮ LIỆU HƯ CẤU</b> — chòm sao và "
                     "thông số vô tuyến trong báo cáo này chỉ phục vụ demo/kiểm "
                     "thử phần mềm, không phải dữ liệu thật của bất kỳ hệ thống nào.</div>")

    c = a["constellation"]
    parts.append("<h2>1. Tổng quan chòm sao</h2>")
    parts.append("<table><tr><th>Tham số</th><th>Giá trị</th></tr>" + "".join([
        _row(["Độ cao quỹ đạo", f"{c['alt_km']:.0f} km"]),
        _row(["Độ nghiêng", f"{c['inc_deg']:.1f}°"]),
        _row(["Số vệ tinh / mặt phẳng", f"{c['n_sats']} / {c['n_planes']}"]),
        _row(["Kiểu Walker", c['kind']]),
        _row(["Chu kỳ quỹ đạo", f"{c['period_min']:.1f} phút"]),
        _row(["Băng tần đường xuống", a["downlink"]["band_ghz"] + " GHz"]),
        _row(["EIRP (giả thiết)", f"{a['downlink']['eirp_dbw_per_mhz']} dBW/MHz"]),
    ]) + "</table>")

    parts.append("<h2>2. Phủ sóng trên lãnh thổ Việt Nam</h2>")
    pts = a["coverage"]["points"]
    parts.append("<table><tr><th>Điểm</th><th>% thời gian phủ</th>"
                 "<th>Số vệ tinh khả kiến TB</th><th>Khoảng trống dài nhất</th></tr>")
    for p in pts:
        parts.append(_row([p["name"], f"{p['fraction_covered']*100:.1f}%",
                           f"{p['mean_sats_visible']:.1f}",
                           f"{p['max_gap_min']:.1f} phút"]))
    parts.append("</table>")
    g = a["coverage"]["grid_summary"]
    parts.append(f"<p class='meta'>Lưới {g['grid']}: % phủ trung bình "
                 f"{g['mean_fraction']*100:.1f}%, thấp nhất "
                 f"{g['min_fraction']*100:.1f}% (góc ngẩng tối thiểu "
                 f"{a['coverage']['min_elev_deg']:.0f}°).</p>")

    p = a["pfd"]
    parts.append("<h2>3. Kiểm tra PFD — RR Article 21</h2>")
    cls = "ok" if p["compliant"] else "bad"
    parts.append("<table><tr><th>Tham số</th><th>Giá trị</th></tr>" + "".join([
        _row(["Băng tần", f"{p['freq_ghz']} GHz ({p['band']} GHz)"]),
        _row(["PFD tại điểm chiếu vệ tinh", f"{p['pfd']:.1f} {p['unit']}"]),
        _row(["Giới hạn Table 21-4", f"{p['limit']:.1f} {p['unit']}"]),
        _row(["Giảm trừ X (NGSO lớn)", f"{p['x_reduction_db']:.2f} dB"]),
        _row(["Biên", f"{p['margin_db']:.1f} dB"]),
    ]) + "</table>")
    parts.append(f"<p class='{cls}'>{'ĐẠT' if p['compliant'] else 'KHÔNG ĐẠT'} "
                 "giới hạn PFD (trường hợp xấu nhất).</p>")

    e = a["epfd"]
    parts.append("<h2>4. Sàng lọc EPFD — RR Article 22</h2>")
    parts.append("<table><tr><th>Phân vị thời gian</th><th>EPFD (dBW/m²/40kHz)</th></tr>")
    for k, v in e["percentiles"].items():
        parts.append(_row([k, f"{v:.1f}"]))
    parts.append("</table>")
    cls = "ok" if e["screening_pass"] else "bad"
    parts.append(f"<p>Điểm không-bao-giờ-vượt-quá (Table 22-1A): "
                 f"{e['anchor_22_1A']:.0f} dBW/m²/40kHz. Biên: "
                 f"{e['margin_vs_anchor_db']:.1f} dB.</p>")
    parts.append(f"<p class='{cls}'>{'ĐẠT' if e['screening_pass'] else 'KHÔNG ĐẠT'} "
                 "sàng lọc EPFD đơn lẻ.</p>")
    parts.append(f"<p class='meta'>Giả thiết: {e['assumptions']}.</p>")

    co = a["coordination"]
    parts.append("<h2>5. Sàng lọc nhu cầu phối hợp quốc tế</h2>")
    parts.append("<table><tr><th>Điểm tham chiếu</th><th>Góc phân tách "
                 "tối thiểu</th><th>PFD cực đại (dBW/m²/40kHz)</th></tr>")
    for pp in co["per_point"]:
        parts.append(_row([pp["point"],
                           f"{pp['min_separation_deg']:.1f}°"
                           if pp["min_separation_deg"] is not None else "—",
                           f"{pp['max_pfd_dbw_m2_40khz']:.1f}"
                           if pp["max_pfd_dbw_m2_40khz"] is not None else "—"]))
    parts.append("</table>")
    cls = "warn" if co["coordination_likely_required"] else "ok"
    parts.append(f"<p class='{cls}'>Kết luận sàng lọc: "
                 f"{'CẦN tiến hành phối hợp quốc tế' if co['coordination_likely_required'] else 'chưa thấy dấu hiệu cần phối hợp'} "
                 f"(cung Appendix 5: ±{co['coordination_arc_deg']:g}°).</p>")
    for r_ in co["reasons"]:
        parts.append(f"<p>• {_esc(r_)}</p>")
    parts.append(f"<p class='meta'>{_esc(co['note'])}</p>")

    if a.get("milestones"):
        parts.append("<h2>6. Mốc triển khai — ITU Res 35</h2>")
        parts.append("<table><tr><th>Chế độ</th><th>Mốc</th><th>Hạn</th>"
                     "<th>Yêu cầu</th><th>Đã triển khai</th><th>Trạng thái</th></tr>")
        for m in a["milestones"]:
            cls = STATUS_CLASS.get(m["status"], "")
            parts.append("<tr>" + "".join([
                f"<td>{_esc(m['regime'])}</td>", f"<td>{m['percent']}%</td>",
                f"<td>{m['due']}</td>", f"<td>{m['required_n']}</td>",
                f"<td>{m['deployed_n']}</td>",
                f"<td class='{cls}'>{m['status']}</td>"]) + "</tr>")
        parts.append("</table>")
    if a.get("warehousing"):
        w = a["warehousing"]
        cls = {"CAO": "bad", "TRUNG_BINH": "warn", "THAP": "ok"}[w["risk"]]
        parts.append(f"<p class='{cls}'>Cảnh báo 'xí phần': {w['message']} "
                     f"(đã triển khai {w['deployed']}/{w['filed']}).</p>")

    parts.append("""<div class="footer"><b>Lưu ý phương pháp:</b> đây là công cụ
sàng lọc kỹ thuật phục vụ phân tích nội bộ. Kết luận cấp phép/phối hợp chính thức
phải dựa trên văn bản ITU/FCC hiện hành và phần mềm của ITU BR (SpaceCap, GIMS,
S.1503). Các bảng giới hạn trong công cụ lấy từ nguồn mở trên mạng, cần đối chiếu
văn bản gốc trước khi dùng chính thức.</div></body></html>""")
    return "\n".join(parts)
