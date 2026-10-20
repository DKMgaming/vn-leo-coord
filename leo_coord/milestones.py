"""Theo dõi mốc triển khai chòm sao — chống "xí phần" tài nguyên quỹ đạo.

- ITU Resolution 35 (WRC-19, sửa đổi WRC-23): 10%/50%/100% sau +2/+5/+7 năm
  kể từ khi hết thời hạn 7 năm đưa vào sử dụng (BIU). Trượt mốc -> MIFR bị
  cắt giảm theo số vệ tinh đã triển khai thực tế.
- FCC (2017): 50% trong 6 năm, 100% trong 9 năm kể từ ngày cấp phép.
"""
from __future__ import annotations

import math
from datetime import date


def add_years(d: date, years: int) -> date:
    """Cộng năm, xử lý 29/2 -> 28/2."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def res35_schedule(biu_deadline: date, n_sats: int) -> list:
    """Lịch mốc ITU Res 35. Trả về list dict {due, percent, required_n}."""
    out = []
    for pct, yrs in ((10, 2), (50, 5), (100, 7)):
        out.append({
            "due": add_years(biu_deadline, yrs),
            "percent": pct,
            "required_n": math.ceil(n_sats * pct / 100.0),
            "regime": "ITU Res 35 (WRC-19)",
        })
    return out


def fcc_schedule(grant_date: date, n_sats: int) -> list:
    """Lịch mốc FCC 2017: 50%/6 năm, 100%/9 năm kể từ ngày cấp phép."""
    out = []
    for pct, yrs in ((50, 6), (100, 9)):
        out.append({
            "due": add_years(grant_date, yrs),
            "percent": pct,
            "required_n": math.ceil(n_sats * pct / 100.0),
            "regime": "FCC 17-122 (2017)",
        })
    return out


def evaluate(schedule: list, deployments: list, today: date = None) -> list:
    """Đánh giá từng mốc so với số liệu triển khai thực tế.

    deployments: list (report_date, n_deployed), đã sắp xếp không bắt buộc.
    Trả về list dict {due, percent, required_n, deployed_n, status, note}.
    status: DAT | CHUA_DEN_HAN | TRE_HAN.
    """
    today = today or date.today()
    deps = sorted(deployments, key=lambda x: x[0])
    out = []
    for m in schedule:
        due = m["due"]
        # số đã triển khai tính đến thời hạn mốc (báo cáo muộn hơn hạn không tính)
        n = 0
        for rdate, rn in deps:
            if rdate <= due:
                n = max(n, rn)
        if today < due:
            # chưa đến hạn: lấy số mới nhất để cảnh báo sớm
            n_now = max([rn for _, rn in deps], default=0)
            status = "CHUA_DEN_HAN"
            note = f"da trien khai {n_now}/{m['required_n']} truoc han {due.isoformat()}"
        elif n >= m["required_n"]:
            status = "DAT"
            note = f"dat moc {m['percent']}% ({n}/{m['required_n']}) truoc {due.isoformat()}"
        else:
            status = "TRE_HAN"
            note = (f"TRUOT moc {m['percent']}%: moi {n}/{m['required_n']} den {due.isoformat()} "
                    f"— MIFR co the bi cat giam")
        out.append({**m, "deployed_n": n, "status": status, "note": note})
    return out


def warehousing_flag(n_filed: int, n_deployed: int) -> dict:
    """Cờ cảnh báo 'xí phần' dựa trên tỷ lệ triển khai/thông báo."""
    ratio = (n_deployed / n_filed) if n_filed else 0.0
    if ratio >= 0.5:
        level, msg = "THAP", "trien khai dang tien trien tot"
    elif ratio >= 0.1:
        level, msg = "TRUNG_BINH", "can theo doi tien do phong"
    else:
        level, msg = "CAO", "nguy co xi phan tai nguyen tan so/quy dao — can ra soat"
    return {"filed": n_filed, "deployed": n_deployed, "ratio": ratio,
            "risk": level, "message": msg}
