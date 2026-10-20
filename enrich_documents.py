"""Tạo và bổ sung 4 tài liệu chuyên sâu về công nghệ vũ trụ và quản trị chòm sao LEO:
1. doc-intl-05 (Word): Direct-to-Device (D2D/SCS) 3GPP Rel-17/18
2. doc-intl-06 (Excel): Link Budget & Phân bổ tần số Ka-band chùm sóng điểm (Spot-beams)
3. doc-intl-07 (Word): Sổ tay đăng ký tần số và quỹ đạo ITU-BR (API/CR/Notification)
4. doc-intl-08 (PPTX): Slide Chiến lược Trạm Cổng Mặt Đất (Gateways) và NOC tại Việt Nam
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
from pathlib import Path
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.dml.color import RGBColor as PptxRGBColor

UPLOAD_DIR = Path("web/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOCS_META_FILE = UPLOAD_DIR / "documents.json"

# --- 1. Tạo doc-intl-05: Direct-to-Device (Word) ---
def create_doc_d2d():
    filename = "khung_chinh_sach_d2d_scs_3gpp.docx"
    filepath = UPLOAD_DIR / filename
    doc = docx.Document()
    
    title = doc.add_heading("KHUNG CHÍNH SÁCH VÀ TIÊU CHUẨN KỸ THUẬT DỊCH VỤ KẾT NỐI VỆ TINH TRỰC TIẾP THIẾT BỊ DI ĐỘNG (DIRECT-TO-DEVICE / SCS)", level=0)
    p_sub = doc.add_paragraph("Nghiên cứu Tiêu chuẩn 3GPP Rel-17/18 NTN, Cơ chế Phối hợp Tần số MSS/Terrestrial và Khuyến nghị Triển khai tại Việt Nam")
    p_meta = doc.add_paragraph("Cơ quan chủ trì: Cục Tần số Vô tuyến điện — Viện Chiến lược Thông tin & Truyền thông\nNgày ban hành: 2026-10-20 | Phân loại: Chiến lược & Chính sách")
    
    doc.add_heading("1. TỔNG QUAN XU THẾ KẾT NỐI VỆ TINH TRỰC TIẾP SMARTPHONE (D2D/SCS)", level=1)
    doc.add_paragraph(
        "Dịch vụ kết nối vệ tinh trực tiếp tới thiết bị di động tiêu chuẩn (Direct-to-Device - D2D hoặc Supplemental Coverage from Space - SCS) "
        "đang là bước chuyển dịch mang tính cách mạng trong ngành viễn thông toàn cầu. Khác với các hệ thống MSS truyền thống (Iridium, Inmarsat) "
        "đòi hỏi thiết bị đầu cuối cồng kềnh với anten xoắn ốc chuyên dụng, kiến trúc D2D cho phép các smartphone thương mại phổ thông kết nối trực tiếp "
        "với chòm sao vệ tinh quỹ đạo thấp (LEO) mà không cần thay đổi phần cứng."
    )
    
    doc.add_heading("2. TIÊU CHUẨN KỸ THUẬT 3GPP NON-TERRESTRIAL NETWORKS (NTN)", level=1)
    doc.add_paragraph(
        "- 3GPP Release 17 (2022): Lần đầu tiên chuẩn hóa mạng phi mặt đất (NTN) cho cả NB-IoT NTN (nhắn tin khẩn cấp, IoT cảm biến) và 5G NR NTN.\n"
        "- 3GPP Release 18 (2024 - 5G-Advanced): Bổ sung khả năng chuyển vùng (handover) mượt mà giữa các búp sóng LEO di chuyển với vận tốc 7.5 km/s, "
        "bù trừ dịch tần Doppler lên tới ±50 kHz ở băng S (2 GHz) và giảm thiểu độ trễ khứ hồi RTT (Round Trip Time) từ 10-25 ms.\n"
        "- Băng tần tiêu chuẩn: Băng n255 (1626.5-1660.5 MHz / 1525-1559 MHz), Băng n256 (1980-2010 MHz / 2170-2200 MHz), và các băng mặt đất FDD (Băng 700 MHz, 800 MHz, PCS) theo mô hình thuê băng tần mặt đất."
    )
    
    doc.add_heading("3. CƠ CHẾ CẤP PHÉP VÀ QUẢN LÝ TẦN SỐ CỦA HOA KỲ (FCC) VÀ BÀI HỌC", level=1)
    doc.add_paragraph(
        "Ngày 14/03/2024, Ủy ban Truyền thông Liên bang Hoa Kỳ (FCC) đã chính thức ban hành Lệnh FCC 24-28 (Docket 23-65) thiết lập khung cấp phép SCS:\n"
        "1. Phân bổ thứ cấp (Secondary Allocation): Cấp quyền phân bổ dịch vụ di động vệ tinh (MSS) song hướng thứ cấp trên các băng tần di động mặt đất linh hoạt.\n"
        "2. Điều kiện thuê phổ tần độc quyền (Single Leaseholder Requirement): Nhà khai thác vệ tinh LEO chỉ được phép phát sóng trên một khu vực địa lý độc lập (GIA) khi đã có hợp đồng thuê phổ tần từ toàn bộ các nhà mạng mặt đất nắm giữ giấy phép tại khu vực đó, đảm bảo không gây nhiễu cho mạng di động mặt đất.\n"
        "3. Nghĩa vụ định tuyến cuộc gọi khẩn cấp (911 Routing): Bắt buộc định tuyến cuộc gọi và tin nhắn SOS về trung tâm ứng cứu khẩn cấp gần nhất kèm tọa độ GPS định vị chính xác."
    )
    
    doc.add_heading("4. ĐỀ XUẤT LỘ TRÌNH QUẢN LÝ D2D TẠI VIỆT NAM", level=1)
    doc.add_paragraph(
        "1. Giai đoạn 2026-2027 (Thử nghiệm diện hẹp): Cho phép thử nghiệm dịch vụ tin nhắn khẩn cấp SOS và thoại vệ tinh trên băng tần 700MHz/2.1GHz tại các khu vực biển đảo, biên giới, vùng sâu vùng xa (nơi mạng di động mặt đất chưa phủ sóng).\n"
        "2. Yêu cầu thiết lập trạm Gateway và cổng kết nối dữ liệu (Data Intercept Gateway) đặt tại lãnh thổ Việt Nam, tuân thủ Luật An ninh mạng và Luật Viễn thông.\n"
        "3. Bảo đảm ưu tiên các kênh thông tin phòng chống thiên tai, cứu hộ cứu nạn quốc gia và lực lượng quốc phòng, an ninh trên biển."
    )
    doc.save(str(filepath))
    return filename, filepath.stat().st_size

# --- 2. Tạo doc-intl-06: Link Budget Ka-band (Excel) ---
def create_doc_link_budget():
    filename = "bang_tinh_link_budget_ka_band_leo.xlsx"
    filepath = UPLOAD_DIR / filename
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Link Budget Ka-Band"
    
    # Header styling
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    sub_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    font_title = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_cell = Font(name="Segoe UI", size=10)
    border = Border(left=Side(style='thin', color='D1D5DB'),
                    right=Side(style='thin', color='D1D5DB'),
                    top=Side(style='thin', color='D1D5DB'),
                    bottom=Side(style='thin', color='D1D5DB'))
    
    ws.merge_cells("A1:E1")
    ws["A1"] = "BẢNG TÍNH TOÁN NGÂN SÁCH TUYẾN SÓNG (LINK BUDGET) VỆ TINH LEO BĂNG TẦN KA (28 GHz / 19 GHz)"
    ws["A1"].font = font_title
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35
    
    headers = ["Tham số kỹ thuật", "Ký hiệu", "Tuyến lên (Uplink - 29.5 GHz)", "Tuyến xuống (Downlink - 19.7 GHz)", "Đơn vị tính"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.font = font_bold
        cell.fill = sub_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[2].height = 25
    
    rows = [
        ("Tần số sóng mang trung tâm", "f", 29.5, 19.7, "GHz"),
        ("Độ cao quỹ đạo danh định", "h", 550.0, 550.0, "km"),
        ("Góc ngẩng tối thiểu trạm mặt đất", "theta_min", 25.0, 25.0, "độ"),
        ("Cự ly nghiêng cực đại (Slant Range)", "d_max", 1123.5, 1123.5, "km"),
        ("Tổn hao không gian tự do (FSPL)", "FSPL", 182.8, 179.3, "dB"),
        ("Tổn hao khí quyển & hấp thụ mưa (99.9%)", "A_rain", 4.2, 2.8, "dB"),
        ("Công suất phát bão hòa máy phát", "P_tx", 20.0, 15.0, "dBW"),
        ("Độ tăng ích anten phát cực đại", "G_tx", 45.0, 36.5, "dBi"),
        ("Độ giảm công suất ngoài trục chính (Off-axis)", "L_off", 1.5, 1.5, "dB"),
        ("Công suất bức xạ đẳng hướng tương đương", "EIRP", 63.5, 50.0, "dBW"),
        ("Nhiệt độ tạp âm hệ thống thu", "T_sys", 450.0, 290.0, "K"),
        ("Hệ số phẩm chất máy thu (G/T)", "G/T", 18.5, 12.8, "dB/K"),
        ("Tỷ số công suất sóng mang trên mật độ tạp âm", "C/N0", 87.2, 83.4, "dB-Hz"),
        ("Băng thông kênh truyền khả dụng", "BW", 250.0, 250.0, "MHz"),
        ("Tỷ số sóng mang trên tạp âm (C/N)", "C/N", 13.2, 11.4, "dB"),
        ("Ngưỡng điều chế & mã hóa yêu cầu (16-APSK 3/4)", "C/N_req", 10.2, 10.2, "dB"),
        ("Biên dự phòng liên lạc (Fade Margin)", "Margin", 3.0, 1.2, "dB (ĐẠT)")
    ]
    
    for row_idx, r in enumerate(rows, 3):
        for col_idx, val in enumerate(r, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_cell
            cell.border = border
            if col_idx in [3, 4]:
                cell.alignment = Alignment(horizontal="right")
            elif col_idx in [2, 5]:
                cell.alignment = Alignment(horizontal="center")
        ws.row_dimensions[row_idx].height = 20
        
    ws.column_dimensions["A"].width = 45
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 25
    ws.column_dimensions["D"].width = 25
    ws.column_dimensions["E"].width = 18
    
    wb.save(str(filepath))
    return filename, filepath.stat().st_size

# --- 3. Tạo doc-intl-07: Sổ tay đăng ký ITU-BR (Word) ---
def create_doc_itu_handbook():
    filename = "so_tay_quy_trinh_dang_ky_tan_so_itu_br.docx"
    filepath = UPLOAD_DIR / filename
    doc = docx.Document()
    
    doc.add_heading("SỔ TAY KỸ THUẬT: QUY TRÌNH ĐĂNG KÝ VỊ TRÍ QUỸ ĐẠO VÀ TẦN SỐ CHÒM SAO LEO TẠI CỤC VÔ TUYẾN ĐIỆN QUỐC TẾ (ITU-BR)", level=0)
    doc.add_paragraph("Hướng dẫn Chi tiết Trình tự Lập Hồ sơ API, Yêu cầu Phối hợp (CR) và Đăng ký MIFR theo Thể lệ Vô tuyến điện ITU")
    doc.add_paragraph("Cơ quan biên soạn: Ban Điều phối Tần số Quốc tế (ITU/WRC) — Cục Tần số Vô tuyến điện\nNgày ban hành: 2026-10-20 | Phân loại: Quy định Quốc tế (ITU)")
    
    doc.add_heading("1. CÁC GIAI ĐOẠN ĐĂNG KÝ MẠNG VỆ TINH THEO THỂ LỆ VÔ TUYẾN ĐIỆN ITU", level=1)
    doc.add_paragraph(
        "Quy trình đăng ký mạng vệ tinh phi địa tĩnh (NGSO/LEO) quốc tế tuân theo 4 bước cơ bản quy định tại Điều 9 và Điều 11 của Thể lệ Vô tuyến điện (ITU Radio Regulations - RR):\n"
        "1. Thông tin xuất bản sớm (Advance Publication Information - API): Công bố thông tin chung về mạng vệ tinh để các nước thành viên ITU nắm bắt sơ bộ.\n"
        "2. Yêu cầu Phối hợp (Coordination Request - CR/C): Xác định danh sách các mạng vệ tinh GSO và chòm sao NGSO bị ảnh hưởng theo các tiêu chí kích hoạt (trigger arcs, EPFD, delta-T/T).\n"
        "3. Thông báo chính thức (Notification under Article 11): Gửi hồ sơ chi tiết sau khi đã đạt được thỏa thuận phối hợp kỹ thuật với các quốc gia liên quan.\n"
        "4. Ghi nhận vào Bảng Đăng bạ Tần số Quốc tế (Master International Frequency Register - MIFR): Khẳng định quyền bảo vệ quốc tế đối với việc sử dụng tần số và quỹ đạo của mạng vệ tinh."
    )
    
    doc.add_heading("2. THỦ TỤC PHỐI HỢP KỸ THUẬT (COORDINATION MECHANISM)", level=1)
    doc.add_paragraph(
        "- Theo Khoản số 9.12: Phối hợp song phương giữa hệ thống NGSO với hệ thống NGSO khác sử dụng chung băng tần.\n"
        "- Theo Khoản số 9.12A: Phối hợp giữa hệ thống NGSO với mạng vệ tinh địa tĩnh GSO (bảo vệ quyền ưu tiên của mạng GSO theo Điều 22).\n"
        "- Tiêu chí can nhiễu delta-T/T > 6% theo Phụ lục 8 (Appendix 8) và ngưỡng suy giảm thông lượng (Throughput Degradation) theo Khuyến nghị ITU-R S.2131.\n"
        "- Ứng dụng phần mềm mô phỏng kiểm tra EPFD của ITU (GIBC / ITU Validation Tool) tuân thủ Khuyến nghị ITU-R S.1503-2."
    )
    
    doc.add_heading("3. KIỂM SOÁT THỜI HẠN VÀ CƠ CHẾ RES 35 CHỐNG XÍ PHẦN TẦN SỐ", level=1)
    doc.add_paragraph(
        "- Thời hạn đưa vào sử dụng (Bringing Into Use - BIU): Tối đa 7 năm kể từ ngày ITU tiếp nhận hồ sơ API đầy đủ.\n"
        "- Bắt buộc triển khai tối thiểu 1 vệ tinh trên 1 mặt phẳng quỹ đạo và duy trì hoạt động liên tục trong 90 ngày.\n"
        "- Lộ trình Nghị quyết 35 (WRC-19): Triển khai đủ 10% chòm sao trong 2 năm, 50% trong 5 năm, và 100% trong 7 năm kể từ khi kết thúc thời hạn 7 năm BIU.\n"
        "- Chế tài xử lý: Nếu không đạt mốc, dung lượng vệ tinh được bảo vệ trong MIFR sẽ bị cắt giảm tương ứng với số lượng vệ tinh thực tế đã phóng lên quỹ đạo."
    )
    doc.save(str(filepath))
    return filename, filepath.stat().st_size

# --- 4. Tạo doc-intl-08: Slide Chiến lược Trạm Cổng Mặt Đất (PPTX) ---
def create_doc_gateways_pptx():
    filename = "slide_chien_luoc_tram_cong_mat_dat_leo_vietnam.pptx"
    filepath = UPLOAD_DIR / filename
    prs = Presentation()
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Slide 1: Tiêu đề
    s1 = prs.slides.add_slide(blank_layout)
    txBox = s1.shapes.add_textbox(PptxInches(1.0), PptxInches(2.0), PptxInches(11.33), PptxInches(3.5))
    tf = txBox.text_frame
    p1 = tf.paragraphs[0]
    p1.text = "CHIẾN LƯỢC QUY HOẠCH & TRIỂN KHAI TRẠM CỔNG VỆ TINH LEO (GATEWAY EARTH STATIONS) TẠI VIỆT NAM"
    p1.font.size = PptxPt(28)
    p1.font.bold = True
    p1.font.color.rgb = PptxRGBColor(2, 132, 199)
    
    p2 = tf.add_paragraph()
    p2.text = "Định vị vị trí địa lý, Tích hợp Trung tâm Điều hành Mạng (NOC) và Bảo đảm An ninh Phổ tần Quốc gia"
    p2.font.size = PptxPt(16)
    p2.font.color.rgb = PptxRGBColor(100, 116, 139)
    
    p3 = tf.add_paragraph()
    p3.text = "Cục Tần số Vô tuyến điện — Viện Công nghệ Vũ trụ | Hội thảo Chuyên đề 2026"
    p3.font.size = PptxPt(13)
    p3.font.color.rgb = PptxRGBColor(71, 85, 105)
    
    # Slide 2: Vị trí 3 Trạm Cổng
    s2 = prs.slides.add_slide(blank_layout)
    txBox2 = s2.shapes.add_textbox(PptxInches(1.0), PptxInches(1.0), PptxInches(11.33), PptxInches(5.5))
    tf2 = txBox2.text_frame
    p_title2 = tf2.paragraphs[0]
    p_title2.text = "1. MẠNG LƯỚI TRẠM CỔNG MẶT ĐẤT CHIẾN LƯỢC TẠI 3 MIỀN"
    p_title2.font.size = PptxPt(24)
    p_title2.font.bold = True
    p_title2.font.color.rgb = PptxRGBColor(15, 23, 42)
    
    points = [
        "Trạm Cổng Miền Bắc (Hòa Lạc - Hà Nội): Đặt tại Khu Công nghệ cao Hòa Lạc, kết nối cáp quang trực tiếp trục Bắc - Nam, quản lý vùng phủ miền Bắc và biên giới phía Bắc.",
        "Trạm Cổng Miền Trung (Đà Nẵng): Tận dụng vị trí trung gian ven biển, đóng vai trò trạm kết nối trọng yếu phục vụ vùng phủ Quần đảo Hoàng Sa, Trường Sa và vùng biển đặc quyền kinh tế (EEZ).",
        "Trạm Cổng Miền Nam (Tân Tạo / Cần Thơ): Quản trị lưu lượng mạng vệ tinh LEO khu vực Đồng bằng Sông Cửu Long, vùng biển phía Nam và kết nối quốc tế qua tuyến cáp quang biển cập bờ.",
        "Kiến trúc Anten: Mỗi trạm cổng trang bị từ 6 - 8 anten bám tự động búp sóng chuyển động nhanh (Ka-band Tracking Dishes đường kính 1.5m - 2.4m) bảo đảm chuyển vùng không gián đoạn."
    ]
    for pt in points:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.size = PptxPt(14)
        p.space_before = PptxPt(14)
        p.font.color.rgb = PptxRGBColor(51, 65, 85)
        
    prs.save(str(filepath))
    return filename, filepath.stat().st_size

print("Đang tạo 4 tài liệu chuyên sâu mới...")
f1, s1 = create_doc_d2d()
f2, s2 = create_doc_link_budget()
f3, s3 = create_doc_itu_handbook()
f4, s4 = create_doc_gateways_pptx()
print(f"Đã tạo: {f1} ({s1} bytes), {f2} ({s2} bytes), {f3} ({s3} bytes), {f4} ({s4} bytes)")

# Cập nhật documents.json
with open(DOCS_META_FILE, "r", encoding="utf-8") as f:
    docs = json.load(f)

# Tạo các object metadata đầy đủ
new_docs = [
    {
        "id": "doc-intl-05",
        "title": "Khung Chính Sách & Tiêu Chuẩn Kỹ Thuật Dịch Vụ Kết Nối Vệ Tinh Trực Tiếp Di Động (Direct-to-Device / SCS) theo 3GPP Rel-17/18",
        "author": "Cục Tần số Vô tuyến điện — Viện Chiến lược Thông tin & Truyền thông",
        "category": "Chiến lược & Chính sách",
        "file_type": "docx",
        "filename": f1,
        "original_filename": "Chinh_sach_D2D_SCS_3GPP_Rel18_Vietnam.docx",
        "file_size": s1,
        "upload_date": "2026-10-20 09:30",
        "summary": "Phân tích kiến trúc kết nối vệ tinh trực tiếp smartphone tiêu chuẩn (Direct-to-Device), cơ chế thuê phổ tần thứ cấp FCC SCS Lệnh 24-28, định tuyến cứu nạn khẩn cấp 911 và đề xuất lộ trình thí điểm tại Việt Nam.",
        "content_full": (UPLOAD_DIR / f1).read_bytes().decode("latin1", errors="ignore")  # hoặc text
    },
    {
        "id": "doc-intl-06",
        "title": "Bảng Tính Toán Ngân Sách Tuyến Sóng (Link Budget) & Tái Sử Dụng Tần Số Ka-band (28/19 GHz) Chùm Sóng Điểm LEO",
        "author": "Phòng Kỹ thuật & Tối ưu hóa Mạng Vệ tinh Không gian",
        "category": "Kỹ thuật & Tính toán",
        "file_type": "xlsx",
        "filename": f2,
        "original_filename": "Link_Budget_Ka_Band_LEO_MultiBeam.xlsx",
        "file_size": s2,
        "upload_date": "2026-10-20 09:30",
        "summary": "Bảng tính chi tiết thông số đường truyền tuyến lên (29.5 GHz) và tuyến xuống (19.7 GHz), tổn hao hấp thụ mưa, hệ số G/T, tỷ số C/N0 và biên dự phòng điều chế thích ứng ACM 16-APSK."
    },
    {
        "id": "doc-intl-07",
        "title": "Sổ Tay Kỹ Thuật: Quy Trình Đăng Ký Vị Trí Quỹ Đạo và Tần Số Chòm Sao LEO tại Cục Vô Tuyến Điện Quốc Tế (ITU-BR)",
        "author": "Ban Điều phối Tần số Quốc tế (ITU/WRC)",
        "category": "Quy định Quốc tế (ITU)",
        "file_type": "docx",
        "filename": f3,
        "original_filename": "So_tay_Dang_ky_Quy_dao_Tan_so_ITU_BR.docx",
        "file_size": s3,
        "upload_date": "2026-10-20 09:30",
        "summary": "Cẩm nang hướng dẫn tuần tự các bước lập hồ sơ API, Yêu cầu Phối hợp (CR Khoản 9.12/9.12A), thông báo Điều 11 MIFR và xử lý tranh chấp theo Thể lệ Vô tuyến điện ITU."
    },
    {
        "id": "doc-intl-08",
        "title": "Slide Báo Cáo Hội Nghị: Chiến Lược Triển Khai Trạm Cổng Vệ Tinh (LEO Gateways) & Trung Tâm Điều Hành Mặt Đất tại Việt Nam",
        "author": "Viện Công nghệ Vũ trụ — Ban Dự án Trạm Mặt Đất",
        "category": "Thuyết trình & Hội thảo",
        "file_type": "pptx",
        "filename": f4,
        "original_filename": "Presentation_LEO_Gateways_Strategy_Vietnam_2026.pptx",
        "file_size": s4,
        "upload_date": "2026-10-20 09:30",
        "summary": "Bản trình bày quy hoạch 3 cụm trạm cổng mặt đất tại Hòa Lạc (miền Bắc), Đà Nẵng (miền Trung - bảo đảm vùng phủ Hoàng Sa/Trường Sa) và Tân Tạo (miền Nam) kèm cấu hình bám búp sóng tự động."
    }
]

# Chèn các tài liệu mới vào
existing_ids = {d["id"] for d in docs}
for nd in new_docs:
    if nd["id"] not in existing_ids:
        docs.append(nd)

# Ghi lại file JSON
with open(DOCS_META_FILE, "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)

print(f"Tổng số tài liệu hiện có trong kho: {len(docs)}")
