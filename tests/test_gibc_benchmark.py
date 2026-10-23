"""Kiểm thử đối chuẩn kỹ thuật giữa LEO-COORD và phần mềm ITU GIBC v10.0 (RR Art. 21)."""
import pytest
import yaml
from pathlib import Path

from leo_coord.pfd import (
    check_downlink_pfd,
    pfd_limit,
    evaluate_pfd_curve,
    benchmark_against_gibc,
)
from leo_coord.reference import reference_dir


def load_gibc_benchmark_data() -> dict:
    fpath = reference_dir() / "itu_gibc_benchmarks.yaml"
    assert fpath.exists(), f"Không tìm thấy file: {fpath}"
    return yaml.safe_load(fpath.read_text(encoding="utf-8"))


def test_gibc_benchmark_file_structure():
    data = load_gibc_benchmark_data()
    assert "benchmark_metadata" in data
    assert "test_vectors" in data
    assert len(data["test_vectors"]) == 5
    assert data["benchmark_metadata"]["status"] == "ITU-GIBC-VERIFIED"


def test_all_five_gibc_test_vectors():
    data = load_gibc_benchmark_data()
    tolerance_db = data["benchmark_metadata"].get("tolerance_db", 0.05)

    for tv in data["test_vectors"]:
        res = benchmark_against_gibc(tv, tolerance_db=tolerance_db)
        assert res["passed"] is True, (
            f"Test Vector {tv['id']} ({tv['name']}) thất bại khi đối chuẩn GIBC! "
            f"Sai số lớn nhất: {res['max_diff_db']} dB (ngưỡng cho phép: {tolerance_db} dB). "
            f"Tính toán: {res['calc']}, Kỳ vọng ITU GIBC: {res['expected']}"
        )
        assert res["max_diff_db"] <= tolerance_db


def test_pfd_curve_generation_and_monotonicity():
    # Thử nghiệm tính đường cong PFD Starlink theo các góc ngẩng từ 0 đến 90 độ
    angles = [0.0, 5.0, 15.0, 25.0, 60.0, 90.0]
    curve = evaluate_pfd_curve(eirp_dbw_per_mhz=15.0, freq_ghz=11.2, alt_km=550.0,
                               n_sats=7500, angles_deg=angles)
    assert len(curve) == len(angles)

    # 1. Cự ly xiên Slant Range phải giảm dần khi góc ngẩng tăng (đỉnh đầu gần nhất)
    ranges = [pt["slant_range_km"] for pt in curve]
    for i in range(len(ranges) - 1):
        assert ranges[i] > ranges[i+1]

    # 2. PFD thực tế tại điểm chiếu vệ tinh (90 độ) phải là lớn nhất (âm ít nhất) do cự ly ngắn nhất
    pfds = [pt["pfd"] for pt in curve]
    assert pfds[-1] > pfds[0]

    # 3. Giới hạn Table 21-4 tại delta=0 và delta=5 bằng nhau (-150 - X)
    assert curve[0]["limit"] == pytest.approx(curve[1]["limit"])
    # Giới hạn tại delta=25 và delta=90 bằng nhau (-140 - X)
    assert curve[3]["limit"] == pytest.approx(curve[-1]["limit"])
