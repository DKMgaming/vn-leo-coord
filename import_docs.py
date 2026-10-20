"""Script nạp toàn bộ tài liệu nghiên cứu quốc tế từ docs/nghien-cuu-quoc-te vào kho tham luận."""
import json
from pathlib import Path
import docx

upload_dir = Path("web/uploads")
docs_src = Path("docs/nghien-cuu-quoc-te")
meta_file = upload_dir / "documents.json"

docs = []
if meta_file.exists():
    try:
        docs = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:
        docs = []

files_to_import = [
    {
        "id": "doc-intl-01",
        "src": docs_src / "report.md",
        "title": "Báo cáo Toàn diện: Kinh nghiệm Quốc tế về Quản lý Tần số & Quỹ đạo Chòm sao LEO/NGSO",
        "author": "Cục Tần số Vô tuyến điện — Nhóm Nghiên cứu Chiến lược Quốc tế",
        "category": "Chiến lược & Chính sách",
        "orig_name": "Bao_cao_Nghien_cuu_Quoc_te_LEO_NGSO.docx",
        "target": "bao_cao_nghien_cuu_quoc_te_leo.docx",
        "summary": "Tổng kết toàn diện kinh nghiệm của FCC (Hoa Kỳ), ITU, Ofcom (Anh) và các nước về quy chế cấp phép chòm sao tầm thấp, cơ chế suy giảm băng thông thay thế EPFD cứng nhắc, và các khuyến nghị cốt lõi cho Việt Nam."
    },
    {
        "id": "doc-intl-02",
        "src": docs_src / "itu.md",
        "title": "Tài liệu Kỹ thuật ITU: Nghị quyết Res 35, Giới hạn PFD/EPFD và Thủ tục Phối hợp Tần số Vũ trụ",
        "author": "Ban Điều phối Tần số Quốc tế (ITU/WRC)",
        "category": "Quy định Quốc tế (ITU)",
        "orig_name": "Tai_lieu_Ky_thuat_ITU_Res35_PFD_EPFD.docx",
        "target": "tai_lieu_ky_thuat_itu_res35.docx",
        "summary": "Quy định chi tiết của ITU tại WRC-19 và WRC-23: các mốc Res 35 (10% sau 2 năm, 50% sau 5 năm, 100% sau 7 năm), ngưỡng PFD Điều 21 Bảng 21-4, EPFD Điều 22 và phương pháp tính toán S.1503."
    },
    {
        "id": "doc-intl-03",
        "src": docs_src / "fcc.md",
        "title": "Chuyên đề FCC: Cải cách Cấp phép Chòm sao NGSO và Cơ chế Xử lý Can nhiễu Suy giảm Băng thông",
        "author": "Phòng Nghiên cứu Chính sách Phổ tần Quốc tế",
        "category": "Chiến lược & Chính sách",
        "orig_name": "Chuyen_de_FCC_Cai_cach_Cap_phep_NGSO.docx",
        "target": "chuyen_de_fcc_cap_phep_ngso.docx",
        "summary": "Phân tích các lệnh cải cách của FCC (FCC 17-122, FCC 24-117) chuyển từ giới hạn EPFD sang cơ chế bảo vệ suy giảm thông lượng 3% (throughput degradation) và quy định ký quỹ chống xí phần 5 triệu USD."
    },
    {
        "id": "doc-intl-04",
        "src": docs_src / "admins-sustainability-vietnam.md",
        "title": "Tham luận: Khung Quản lý và Tính Bền vững Không gian Vũ trụ đối với Chòm sao LEO tại Việt Nam",
        "author": "Hội đồng Khoa học & Công nghệ Vũ trụ Việt Nam",
        "category": "Kỹ thuật & Tính toán",
        "orig_name": "Tham_luan_Quan_ly_Ben_vung_Chom_sao_LEO_VietNam.docx",
        "target": "tham_luan_ben_vung_leo_vietnam.docx",
        "summary": "Đánh giá các quy định quốc tế về thu hồi vệ tinh sau nhiệm vụ (quy tắc 5 năm của FCC, tiêu chuẩn IADC), kiểm soát rác thải không gian và kiến nghị chính sách thử nghiệm cấp phép tại Việt Nam."
    }
]

for item in files_to_import:
    if not item["src"].exists():
        continue
    md_content = item["src"].read_text(encoding="utf-8")
    doc = docx.Document()
    doc.add_heading(item["title"], level=0)
    p_meta = doc.add_paragraph()
    p_meta.add_run("Tác giả / Cơ quan: ").bold = True
    p_meta.add_run(item["author"] + "\n")
    p_meta.add_run("Phân loại: ").bold = True
    p_meta.add_run(item["category"] + "\n")
    p_meta.add_run("Tóm tắt: ").bold = True
    p_meta.add_run(item["summary"] + "\n")
    doc.add_paragraph("=" * 60)
    
    for line in md_content.split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("# "):
            doc.add_heading(line_s[2:], level=1)
        elif line_s.startswith("## "):
            doc.add_heading(line_s[3:], level=2)
        elif line_s.startswith("### "):
            doc.add_heading(line_s[4:], level=3)
        elif line_s.startswith("- "):
            doc.add_paragraph(line_s[2:], style="List Bullet")
        else:
            doc.add_paragraph(line_s)
            
    out_docx = upload_dir / item["target"]
    doc.save(str(out_docx))
    file_size = len(out_docx.read_bytes())
    
    existing_idx = next((i for i, d in enumerate(docs) if d["id"] == item["id"]), None)
    entry = {
        "id": item["id"],
        "title": item["title"],
        "author": item["author"],
        "category": item["category"],
        "file_type": "docx",
        "filename": item["target"],
        "original_filename": item["orig_name"],
        "file_size": file_size,
        "upload_date": "2026-10-19 15:46",
        "summary": item["summary"],
        "content_full": md_content
    }
    if existing_idx is not None:
        docs[existing_idx] = entry
    else:
        docs.insert(0, entry)

meta_file.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Hoàn thành nạp {len(files_to_import)} tài liệu. Tổng số tài liệu: {len(docs)}")
