"""Kiểm thử module milestone Res 35 / FCC."""
from datetime import date

from leo_coord.milestones import (
    add_years, res35_schedule, fcc_schedule, evaluate, warehousing_flag,
)


def test_add_years_feb29():
    assert add_years(date(2024, 2, 29), 1) == date(2025, 2, 28)
    assert add_years(date(2024, 3, 1), 2) == date(2026, 3, 1)


def test_res35_schedule_values():
    # khớp kiểm tra tay: N=648, BIU 01/03/2024 -> 10%=65 (2026), 50%=324 (2029), 100%=648 (2031)
    s = res35_schedule(date(2024, 3, 1), 648)
    assert [(m["due"], m["percent"], m["required_n"]) for m in s] == [
        (date(2026, 3, 1), 10, 65),
        (date(2029, 3, 1), 50, 324),
        (date(2031, 3, 1), 100, 648),
    ]


def test_fcc_schedule_values():
    s = fcc_schedule(date(2024, 1, 15), 1000)
    assert s[0]["due"] == date(2030, 1, 15) and s[0]["required_n"] == 500
    assert s[1]["due"] == date(2033, 1, 15) and s[1]["required_n"] == 1000


def test_evaluate_mixed():
    s = res35_schedule(date(2024, 3, 1), 648)
    deps = [(date(2025, 6, 1), 70), (date(2028, 12, 1), 320)]
    # mốc 10% (hạn 2026-03-01): 70 >= 65 trước hạn -> ĐẠT
    # mốc 50% (hạn 2029-03-01): 320 < 324 -> TRỄ (thiếu 4)
    out = evaluate(s, deps, today=date(2030, 1, 1))
    assert out[0]["status"] == "DAT" and out[0]["deployed_n"] == 70
    assert out[1]["status"] == "TRE_HAN" and out[1]["deployed_n"] == 320
    assert out[2]["status"] == "CHUA_DEN_HAN"


def test_evaluate_met():
    s = res35_schedule(date(2024, 3, 1), 100)
    out = evaluate(s, [(date(2025, 1, 1), 15)], today=date(2027, 1, 1))
    assert out[0]["status"] == "DAT"


def test_warehousing_flag():
    assert warehousing_flag(1000, 600)["risk"] == "THAP"
    assert warehousing_flag(1000, 200)["risk"] == "TRUNG_BINH"
    assert warehousing_flag(1000, 5)["risk"] == "CAO"
