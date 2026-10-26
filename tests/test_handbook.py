"""Unit tests cho module leo_coord.handbook và các API endpoint tra cứu Sổ tay ITU Handbook."""
import pytest
from leo_coord.handbook import (
    get_handbook_summary,
    get_handbook_chapters,
    get_handbook_chapter_detail,
    search_handbook,
    HANDBOOK_METADATA,
    SATELLITE_MASS_CLASSIFICATION,
    BR_SOFTWARE_TOOLKIT,
)
from web.app import (
    get_handbook_summary_endpoint,
    get_handbook_chapters_endpoint,
    get_handbook_chapter_detail_endpoint,
    search_handbook_endpoint,
    get_handbook_pdf_status,
)


def test_handbook_metadata_and_summary():
    summary = get_handbook_summary()
    assert summary["status"] == "success"
    assert summary["metadata"]["doc_id"] == "ITU-R HDB-65-2023"
    assert summary["metadata"]["total_pages"] == 212
    assert summary["total_chapters"] == 9
    assert len(summary["chapters"]) == 9
    assert len(summary["satellite_classification"]) >= 5
    assert len(summary["software_toolkit"]) == 6
    assert "resolution_35" in summary
    assert "examination_11_31" in summary
    assert summary["starlink_benchmark"]["total_satellites"] == 4408


def test_handbook_chapters():
    chapters = get_handbook_chapters()
    assert len(chapters) == 9
    nums = [c["chapter_num"] for c in chapters]
    assert nums == list(range(1, 10))

    ch3 = get_handbook_chapter_detail(3)
    assert ch3 is not None
    assert "Regulatory Procedures" in ch3["title"]
    assert len(ch3["key_topics"]) >= 5

    ch_none = get_handbook_chapter_detail(99)
    assert ch_none is None


def test_search_handbook():
    res_res35 = search_handbook("Resolution 35")
    assert len(res_res35) >= 1
    assert any("Resolution 35" in r["title"] for r in res_res35)

    res_spacecap = search_handbook("SpaceCap")
    assert len(res_spacecap) >= 1
    assert any("SpaceCap" in r["title"] for r in res_spacecap)

    res_starlink = search_handbook("Starlink")
    assert len(res_starlink) >= 1
    assert any("Starlink" in r["title"] for r in res_starlink)

    res_empty = search_handbook("")
    assert res_empty == []


def test_web_routes_handbook():
    summary = get_handbook_summary_endpoint()
    assert summary["status"] == "success"
    assert summary["total_chapters"] == 9

    chapters = get_handbook_chapters_endpoint()
    assert len(chapters) == 9

    detail3 = get_handbook_chapter_detail_endpoint(3)
    assert detail3["chapter_num"] == 3

    search_res = search_handbook_endpoint("GIBC")
    assert search_res["query"] == "GIBC"
    assert len(search_res["results"]) >= 1

    pdf_stat = get_handbook_pdf_status()
    assert pdf_stat["filename"] == "Handbook-R-HDB-65-2023-PDF-E.pdf"
    assert pdf_stat["exists"] is True
    assert pdf_stat["total_pages"] == 212
    assert pdf_stat["size_mb"] > 0
