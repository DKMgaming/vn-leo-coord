"""
Unit tests cho Giai đoạn 7: Bộ Giải mã CSDL Công báo Quốc tế ITU BR IFIC (SRS.mdb / SQLite Diff Engine).
Kiểm tra:
- Khởi tạo và đọc CSDL SQLite
- Kết nối và đọc CSDL Microsoft Access (.mdb) qua pyodbc
- Động cơ Diff Engine so sánh 2 kỳ công báo BR IFIC (3014 vs 3015)
- Trình quản lý kết nối trực tiếp (Live Connection)
- API endpoint upload file .mdb / .sqlite
"""

import asyncio
import io
from pathlib import Path
import pytest
from starlette.datastructures import UploadFile

from leo_coord.srs_reader import (
    BRConnectionManager,
    BRDatabaseConnector,
    BRDiffEngine,
    ensure_sample_reference_databases,
    parse_mdb_or_sqlite_file,
)
from web.app import (
    connect_srs_database_endpoint,
    diff_srs_editions_endpoint,
    get_sample_databases_endpoint,
    get_srs_status_endpoint,
    upload_spacecap_filing,
)


@pytest.fixture(scope="module")
def srs_sample_dbs():
    db14, db15 = ensure_sample_reference_databases()
    return db14, db15


def test_ensure_sample_reference_databases(srs_sample_dbs):
    db14, db15 = srs_sample_dbs
    assert db14.exists()
    assert db15.exists()
    assert db14.suffix == ".sqlite"
    assert db15.suffix == ".sqlite"


def test_sqlite_connector_fetch_notices(srs_sample_dbs):
    db14, db15 = srs_sample_dbs
    conn14 = BRDatabaseConnector(db14)
    status14 = conn14.test_connection()
    assert status14["connected"] is True
    assert status14["db_type"] == "SQLite"

    notices14 = conn14.fetch_notices()
    assert len(notices14) == 4
    sat_names14 = [n.sat_name for n in notices14]
    assert "USASAT-NGSO-3" in sat_names14
    assert "CHNSAT-NGSO-1" in sat_names14

    conn15 = BRDatabaseConnector(db15)
    notices15 = conn15.fetch_notices()
    assert len(notices15) == 5
    sat_names15 = [n.sat_name for n in notices15]
    assert "KUIPER-NGSO-V" in sat_names15  # Hồ sơ mới
    assert "JILIN-1-OPT" in sat_names15    # Hồ sơ mới


def test_diff_engine_compare_editions(srs_sample_dbs):
    db14, db15 = srs_sample_dbs
    conn14 = BRDatabaseConnector(db14)
    conn15 = BRDatabaseConnector(db15)

    notices14 = conn14.fetch_notices()
    notices15 = conn15.fetch_notices()

    diff = BRDiffEngine.compare_notices(
        base_notices=notices14,
        target_notices=notices15,
        base_label="BR IFIC No. 3014",
        target_label="BR IFIC No. 3015",
    )

    assert diff["status"] == "success"
    summary = diff["summary"]
    assert summary["new_count"] >= 2
    assert summary["modified_count"] >= 1
    assert summary["vietnam_risk_count"] >= 3

    new_names = [f["sat_name"] for f in diff["new_filings"]]
    assert "KUIPER-NGSO-V" in new_names

    mod_names = [f["sat_name"] for f in diff["modified_filings"]]
    assert "USASAT-NGSO-3" in mod_names

    for f in diff["vietnam_risk_filings"]:
        assert f["is_vietnam_risk"] is True
        assert f["spacecom_days_left"] > 0


def test_connection_manager_live_status(srs_sample_dbs):
    _, db15 = srs_sample_dbs
    mgr = BRConnectionManager.get_instance()
    res = mgr.connect(db15)
    assert res["status"] == "success"
    assert res["connected"] is True

    status = mgr.get_status()
    assert status["status"] == "CONNECTED"
    assert "SẴN SÀNG" in status["ready_state"]
    assert status["total_notices"] == 5

    filings = mgr.get_filings()
    assert len(filings) == 5
    assert any(f.name == "KUIPER-NGSO-V" for f in filings)


def test_access_mdb_reading_if_available():
    mdb_sample = Path("data/reference/sample_srs_ific3015.mdb")
    if not mdb_sample.exists():
        pytest.skip("Tệp MDB mẫu chưa được tạo trên môi trường này.")

    conn = BRDatabaseConnector(mdb_sample)
    test_res = conn.test_connection()
    if not test_res.get("connected"):
        pytest.skip(f"Môi trường chưa có Access ODBC Driver: {test_res.get('message')}")

    notices = conn.fetch_notices()
    assert len(notices) >= 3
    assert any(n.sat_name == "STARLINK-GEN2-MDB" for n in notices)

    filings = parse_mdb_or_sqlite_file(mdb_sample)
    assert len(filings) >= 3
    assert any(f.name == "STARLINK-GEN2-MDB" for f in filings)


def test_api_srs_endpoints():
    # 1. GET /api/srs/status
    data = get_srs_status_endpoint()
    assert data["status"] == "success"
    assert "connection_info" in data

    # 2. POST /api/srs/diff
    diff_data = diff_srs_editions_endpoint({})
    assert diff_data["status"] == "success"
    assert diff_data["summary"]["new_count"] >= 2

    # 3. GET /api/srs/sample-databases
    db_res = get_sample_databases_endpoint()
    db_list = db_res["databases"]
    assert len(db_list) >= 2


def test_api_upload_mdb_or_sqlite(srs_sample_dbs):
    _, db15 = srs_sample_dbs

    with open(db15, "rb") as f:
        file_bytes = f.read()

    upload_file = UploadFile(filename="test_upload_srs.sqlite", file=io.BytesIO(file_bytes))
    res = asyncio.run(upload_spacecap_filing(upload_file))

    assert res["status"] == "success"
    assert res["is_database"] is True
    assert res["total_filings_imported"] == 5
    assert res["filing"]["total_satellites"] > 0

