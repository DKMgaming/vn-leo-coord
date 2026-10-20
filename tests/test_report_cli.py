"""Kiểm thử báo cáo HTML và CLI (tích hợp)."""
import subprocess
import sys
from pathlib import Path

from leo_coord.report import build_html

PROJ = Path(__file__).resolve().parent.parent


def _fake_assessment():
    return {
        "name": "DEMO_LEO_KU", "fictional": True,
        "constellation": {"alt_km": 550.0, "inc_deg": 53.0, "n_sats": 120,
                          "n_planes": 6, "kind": "delta", "period_min": 95.5,
                          "footprint_km": 1657.0},
        "downlink": {"band_ghz": "10.7-12.7", "freq_ghz": 11.7,
                     "eirp_dbw_per_mhz": 10.0},
        "coverage": {
            "points": [{"name": "hanoi", "fraction_covered": 1.0,
                        "mean_sats_visible": 8.5, "max_gap_min": 0.0}],
            "grid_summary": {"grid": "16x9", "mean_fraction": 0.99,
                             "min_fraction": 0.9},
            "min_elev_deg": 10.0},
        "pfd": {"freq_ghz": 11.7, "band": "10.7-11.7", "unit": "dB(W/m2)/4kHz",
                "pfd": -120.0, "limit": -140.0, "x_reduction_db": 2.1,
                "margin_db": -20.0, "compliant": False},
        "epfd": {"percentiles": {"p0": -200.0, "p100": -150.0},
                 "anchor_22_1A": -160.0, "margin_vs_anchor_db": 10.0,
                 "screening_pass": True,
                 "assumptions": "demo"},
        "coordination": {
            "coordination_arc_deg": 6.0,
            "coordination_likely_required": True,
            "reasons": ["goc phan tach toi thieu 2.0° nam trong cung"],
            "note": "sang loc",
            "per_point": [{"point": "hanoi", "min_separation_deg": 2.0,
                           "max_pfd_dbw_m2_40khz": -150.0}]},
        "milestones": [{"regime": "ITU Res 35 (WRC-19)", "percent": 10,
                        "due": "2026-03-01", "required_n": 12,
                        "deployed_n": 15, "status": "DAT"}],
        "warehousing": {"filed": 120, "deployed": 15, "ratio": 0.125,
                        "risk": "TRUNG_BINH", "message": "can theo doi"},
    }


def test_build_html_contains_sections():
    html = build_html(_fake_assessment())
    for needle in ["DEMO_LEO_KU", "DỮ LIỆU HƯ CẤU", "Article 21", "Article 22",
                   "Res 35", "xí phần", "SpaceCap"]:
        assert needle in html
    assert html.strip().startswith("<!DOCTYPE html>")


def test_cli_assess_end_to_end(tmp_path):
    out = tmp_path / "bao_cao.html"
    r = subprocess.run(
        [sys.executable, "-m", "leo_coord.cli", "assess",
         "--constellation", "data/demo/constellation_demo.yaml",
         "--biu-deadline", "2031-03-01",
         "--deployed", "2025-06-01:10",
         "--out", str(out)],
        cwd=PROJ, capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    html = out.read_text(encoding="utf-8")
    assert "DEMO_LEO_KU" in html and "DỮ LIỆU HƯ CẤU" in html


def test_cli_milestones():
    r = subprocess.run(
        [sys.executable, "-m", "leo_coord.cli", "milestones",
         "--biu-deadline", "2024-03-01", "--n-sats", "648",
         "--deployed", "2025-06-01:70,2028-12-01:320",
         "--today", "2030-01-01"],
        cwd=PROJ, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-1000:]
    assert "DAT" in r.stdout and "TRE_HAN" in r.stdout
