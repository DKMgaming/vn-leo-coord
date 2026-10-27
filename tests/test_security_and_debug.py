"""Kiểm thử bảo mật, biên giới đường dẫn và gỡ lỗi (Test & Debug) cho LEO-COORD.

Bao gồm:
- Kiểm thử phòng vệ Path Traversal trong upload/download/delete tài liệu tham luận.
- Kiểm thử kiểm soát định dạng tệp (chỉ cho phép các phần mở rộng hợp lệ).
- Kiểm thử tính an toàn của API Key không bị rò rỉ qua query URL.
- Kiểm thử luồng xử lý lỗi và tính toàn vẹn của dữ liệu tải lên.
"""
import asyncio
import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from starlette.datastructures import UploadFile
from fastapi import HTTPException

from web.app import (
    app,
    upload_document,
    download_document,
    delete_document,
    get_document_content,
    upload_spacecap_filing,
    UPLOAD_DIR,
    load_documents_meta,
    save_documents_meta,
)
from leo_coord.multi_agent import call_llm_api


def test_upload_document_valid():
    """Kiểm thử tải lên tài liệu hợp lệ (.docx)."""
    content = b"Fake Word Document Content for Testing"
    upload_file = UploadFile(filename="bao_cao_test.docx", file=io.BytesIO(content))
    res = asyncio.run(
        upload_document(
            file=upload_file,
            title="Báo cáo thử nghiệm",
            author="Kỹ sư kiểm thử",
            category="Chiến lược & Chính sách",
            summary="Tóm tắt kiểm thử"
        )
    )
    assert res["status"] == "success"
    doc = res["document"]
    assert doc["title"] == "Báo cáo thử nghiệm"
    assert doc["author"] == "Kỹ sư kiểm thử"
    assert doc["file_type"] == "docx"

    # Kiểm tra file đã được lưu trong UPLOAD_DIR
    saved_file = UPLOAD_DIR / doc["filename"]
    assert saved_file.exists()
    assert saved_file.read_bytes() == content

    # Dọn dẹp
    delete_document(doc["id"])
    assert not saved_file.exists()


def test_upload_document_invalid_extension():
    """Kiểm thử từ chối tệp có phần mở rộng nguy hiểm (.exe, .py, .sh)."""
    upload_file = UploadFile(filename="malicious_script.exe", file=io.BytesIO(b"malicious"))
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_document(
                file=upload_file,
                title="Tệp độc hại",
                author="Hacker",
            )
        )
    assert exc_info.value.status_code == 400
    assert "Định dạng tệp không được hỗ trợ" in exc_info.value.detail


def test_upload_document_path_traversal_sanitized():
    """Kiểm thử phòng vệ tấn công Path Traversal qua filename (ví dụ: ../../evil.pdf)."""
    malicious_filename = "../../../etc/passwd.pdf"
    content = b"PDF content trying to traverse"
    upload_file = UploadFile(filename=malicious_filename, file=io.BytesIO(content))
    doc_id = None
    try:
        res = asyncio.run(
            upload_document(
                file=upload_file,
                title="Thử nghiệm Path Traversal",
                author="Pentester",
            )
        )
        assert res["status"] == "success"
        doc = res["document"]
        doc_id = doc["id"]

        # Đảm bảo filename đã được sanitize bằng Path().name, không còn ../
        assert ".." not in doc["filename"]
        assert doc["filename"].endswith("_passwd.pdf")
        saved_file = (UPLOAD_DIR / doc["filename"]).resolve()

        # File bắt buộc phải nằm bên trong UPLOAD_DIR
        assert str(saved_file).startswith(str(UPLOAD_DIR.resolve()))
        assert saved_file.exists()
    finally:
        if doc_id:
            delete_document(doc_id)


def test_download_document_safe_path():
    """Kiểm thử tải xuống tài liệu an toàn."""
    content = b"Safe download content"
    upload_file = UploadFile(filename="safe_download.pdf", file=io.BytesIO(content))
    doc_id = None
    try:
        res_upload = asyncio.run(
            upload_document(
                file=upload_file,
                title="Tài liệu an toàn",
                author="Tester",
            )
        )
        doc_id = res_upload["document"]["id"]

        # Tải xuống
        resp = download_document(doc_id)
        assert resp.status_code == 200
        assert Path(resp.path).exists()
        assert Path(resp.path).read_bytes() == content
    finally:
        if doc_id:
            delete_document(doc_id)


def test_download_document_not_found():
    """Kiểm thử tải xuống tài liệu không tồn tại trả về 404."""
    with pytest.raises(HTTPException) as exc_info:
        download_document("doc-non-existent-9999")
    assert exc_info.value.status_code == 404


def test_get_document_content_safe():
    """Kiểm thử đọc nội dung tài liệu an toàn."""
    upload_file = UploadFile(filename="content_test.pdf", file=io.BytesIO(b"Hello Content"))
    doc_id = None
    try:
        res_upload = asyncio.run(
            upload_document(
                file=upload_file,
                title="Đọc nội dung",
                author="Tester",
            )
        )
        doc_id = res_upload["document"]["id"]

        res = get_document_content(doc_id)
        assert res["title"] == "Đọc nội dung"
    finally:
        if doc_id:
            delete_document(doc_id)


def test_spacecap_upload_path_traversal_sanitization():
    """Kiểm thử bóc tách SpaceCap an toàn trước tên file độc hại có path traversal."""
    malicious_filename = "../../../uploads/evil_spacecap.xml"
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
    <spacecap_filing xmlns="http://www.itu.int/ITU-R/spacecap" version="2.0">
      <header>
        <satellite_name>SEC-TEST-SAT</satellite_name>
        <notifying_administration>VTN</notifying_administration>
      </header>
    </spacecap_filing>
    """
    upload_file = UploadFile(filename=malicious_filename, file=io.BytesIO(xml_content.encode("utf-8")))
    res = asyncio.run(upload_spacecap_filing(upload_file))
    assert res["status"] == "success"
    assert res["filing"]["name"] == "SEC-TEST-SAT"

    # Dọn dẹp
    from leo_coord.spacecap import UPLOADED_FILINGS_DIR
    test_json = UPLOADED_FILINGS_DIR / f"{res['filing']['id']}.json"
    if test_json.exists():
        test_json.unlink()


@patch("urllib.request.urlopen")
def test_multi_agent_gemini_api_key_not_in_url_query(mock_urlopen):
    """Kiểm thử API Key của Google Gemini được gửi an toàn qua header x-goog-api-key, không lộ trên query URL."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": "Phân tích an toàn bảo mật thành công."}]}
        }]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    test_api_key = "AIzaSyFakeSecretKeyForTesting12345"
    res = call_llm_api(
        prompt="Kiểm tra bảo mật URL",
        provider="gemini",
        model="gemini-3.1-flash-lite",
        api_key=test_api_key,
    )
    assert res["status"] == "success"
    assert "Phân tích an toàn bảo mật" in res["text"]

    # Lấy đối tượng Request đã được gửi
    called_req = mock_urlopen.call_args[0][0]
    called_url = called_req.full_url
    called_headers = called_req.headers

    # Xác minh: API key KHÔNG được nằm trong URL
    assert "key=" not in called_url
    assert test_api_key not in called_url

    # Xác minh: API key ĐƯỢC truyền an toàn trong headers
    assert called_headers.get("X-goog-api-key") == test_api_key
