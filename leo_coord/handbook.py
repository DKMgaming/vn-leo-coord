"""Module tra cứu và đối chiếu Sổ tay Vệ tinh Nhỏ ITU-R (ITU-R Handbook on Small Satellites - Edition 2023).

Tài liệu tham chiếu chuẩn hóa: Handbook-R-HDB-65-2023 (Geneva, 2023)
Ban hành theo Nghị quyết Resolution ITU-R 68 của Đại hội Vô tuyến Điện Thế giới.
Bao gồm toàn bộ 9 Chương, bảng phân loại vệ tinh, quy trình đăng ký tần số, hệ sinh thái phần mềm ITU BR,
tiêu chuẩn giảm thiểu rác vũ trụ (Space Debris) và các nghiên cứu điển hình chòm vệ tinh (Starlink, Jilin-1, Astranis).
"""
from typing import Dict, List, Any, Optional
import re
from pathlib import Path

HANDBOOK_METADATA = {
    "doc_id": "ITU-R HDB-65-2023",
    "title": "ITU-R Handbook on Small Satellites (Edition 2023)",
    "vietnamese_title": "Sổ tay Quy chuẩn Vệ tinh Nhỏ ITU-R (Ấn bản 2023)",
    "publisher": "International Telecommunication Union (ITU-R), Geneva, Switzerland",
    "study_group": "ITU-R Study Group 4 (Satellite Services) & Radiocommunication Bureau (BR)",
    "mandate": "Resolution ITU-R 68 (Improving dissemination of knowledge concerning applicable regulatory procedures for small satellites)",
    "edition": "2023",
    "total_pages": 212,
    "file_path": r"E:\leo-coord-main\Handbook-R-HDB-65-2023-PDF-E.pdf",
    "pdf_filename": "Handbook-R-HDB-65-2023-PDF-E.pdf",
    "status": "OFFICIAL_ITU_PUBLICATION"
}

# Bảng phân loại khối lượng vệ tinh nhỏ (Chapter 1, Section 1.4)
SATELLITE_MASS_CLASSIFICATION = [
    {
        "category": "Femtosatellite (Vệ tinh Femto)",
        "mass_range": "< 100 g (< 0.1 kg)",
        "typical_dimensions": "ChipSat, bảng mạch mỏng",
        "typical_lifetime": "Vài ngày đến vài tuần",
        "typical_applications": "Cảm biến vi mô rải rác, thử nghiệm công nghệ bán dẫn"
    },
    {
        "category": "Picosatellite (Vệ tinh Pico)",
        "mass_range": "100 g - 1 kg (0.1 - 1 kg)",
        "typical_dimensions": "PocketQube (5x5x5 cm), 1/4U - 1/2U CubeSat",
        "typical_lifetime": "Vài tuần đến vài tháng",
        "typical_applications": "Giáo dục đại học, thu thập dữ liệu IoT/M2M dải hẹp, beacon vô tuyến nghiệp dư"
    },
    {
        "category": "Nanosatellite (Vệ tinh Nano)",
        "mass_range": "1 kg - 10 kg",
        "typical_dimensions": "1U, 2U, 3U, 6U CubeSat (10x10x10 cm đơn vị)",
        "typical_lifetime": "1 - 3 năm",
        "typical_applications": "Giáo dục, nghiên cứu khoa học, IoT vệ tinh, viễn thám độ phân giải trung bình, ADS-B/AIS"
    },
    {
        "category": "Microsatellite (Vệ tinh Vi mô)",
        "mass_range": "10 kg - 100 kg",
        "typical_dimensions": "12U, 16U, 27U CubeSat hoặc thân chuyên dụng",
        "typical_lifetime": "3 - 5 năm",
        "typical_applications": "Ảnh quang học độ phân giải cao, radar SAR nhỏ, viễn thông thương mại băng hẹp, chòm sao khoa học"
    },
    {
        "category": "Minisatellite (Vệ tinh Mini / SmallSat)",
        "mass_range": "100 kg - 500 kg",
        "typical_dimensions": "Cấu trúc module công nghiệp (ESPA Ring compatible)",
        "typical_lifetime": "5 - 7 năm",
        "typical_applications": "Chòm sao băng rộng Megaconstellation (Starlink ~260-300kg, OneWeb ~150kg), vệ tinh GSO cỡ nhỏ (Astranis ~400kg)"
    },
    {
        "category": "Small Satellite landscape",
        "mass_range": "500 kg - 1000 kg",
        "typical_dimensions": "Thân vệ tinh tầm trung",
        "typical_lifetime": "7 - 10 năm",
        "typical_applications": "Viễn thám chuyên dụng cấp quốc gia (VNREDSat-1 ~115kg), vệ tinh viễn thông chuyên dụng"
    }
]

# Danh mục 9 Chương chi tiết trong Sổ tay ITU
HANDBOOK_CHAPTERS = [
    {
        "chapter_num": 1,
        "title": "Introduction & Systems Engineering",
        "vietnamese_title": "Chương 1: Giới thiệu, Thuật ngữ & Kỹ thuật Hệ thống Vệ tinh nhỏ",
        "page_range": "11 - 15",
        "key_topics": [
            "Mục đích và bối cảnh ban hành Sổ tay theo Resolution ITU-R 68",
            "Thuật ngữ chuẩn hóa quốc tế về Femto, Pico, Nano, Micro và Mini satellites",
            "Lịch sử phát triển từ vệ tinh Sputnik-1, OSCAR đến kỷ nguyên bùng nổ CubeSat",
            "Quy trình kỹ thuật hệ thống (Systems Engineering) thiết kế và chế tạo vệ tinh nhỏ",
            "Tiêu chuẩn giao diện phóng CubeSat (P-POD, deployer canister)"
        ],
        "relevance_to_vietnam": "Định hình khung quy chuẩn chế tạo và phóng vệ tinh nghiên cứu, giáo dục và viễn thám của Việt Nam (kế thừa từ F-1, PicoDragon, NanoDragon và MicroDragon)."
    },
    {
        "chapter_num": 2,
        "title": "Characteristics of Small Satellite Systems",
        "vietnamese_title": "Chương 2: Đặc tính Kỹ thuật Phân đoạn Không gian, Mặt đất & Quỹ đạo",
        "page_range": "16 - 23",
        "key_topics": [
            "Cấu trúc phân đoạn không gian (Space segment): Bus, nguồn điện mặt trời, pin Li-ion, OBC, AOCS/ADCS, payload vô tuyến",
            "Phân đoạn mặt đất (Ground segment): Trạm thu phát điều khiển TT&C, trạm Gateway thương mại, mạng lưới trạm phân tán",
            "Các dạng quỹ đạo đặc thù: Quỹ đạo thấp (LEO 160-2000 km), Quỹ đạo trung (MEO 2000-35786 km), Quỹ đạo địa tĩnh (GSO 35786 km), Quỹ đạo đồng bộ mặt trời (SSO) và Quỹ đạo elip cao (HEO)",
            "Mối liên hệ giữa chu kỳ quay (Orbital period), bán trục lớn, cận điểm (Perigee) và viễn điểm (Apogee)"
        ],
        "relevance_to_vietnam": "Cung cấp công thức cơ học quỹ đạo chuẩn hóa cho module mô phỏng quỹ đạo 3D (SGP4 và Keplerian) và tính toán góc búp sóng phủ sóng các trạm mặt đất Đà Nẵng, Hà Nội, TP.HCM."
    },
    {
        "chapter_num": 3,
        "title": "Radio Regulatory Procedures for Small Satellites",
        "vietnamese_title": "Chương 3: Thủ tục Pháp lý Vô tuyến Quốc tế cho Vệ tinh nhỏ (Trọng tâm)",
        "page_range": "24 - 98",
        "key_topics": [
            "Tổng quan cơ chế pháp lý của ITU: Hiến chương (Constitution), Công ước (Convention) và Thể lệ Vô tuyến điện (Radio Regulations - RR)",
            "Phân định mạng vệ tinh: Không thuộc diện phối hợp (RR Article 9 Section I - API) vs Bắt buộc phối hợp (RR Article 9 Section II - CR/C)",
            "Quy trình đăng ký Thông tin Xuất bản Trước (API/A, API/B) theo Điều 9 Thể lệ Vô tuyến",
            "Quy trình Yêu cầu Phối hợp (CR/C Special Section) cho mạng Non-GSO FSS/MSS",
            "Đăng ký vào Sổ Đăng bạ Quốc tế MIFR (Notification under RR Article 11): Part I-S (Tiếp nhận), Part II-S (Ghi nhận chính thức có kết luận thuận lợi), Part III-S (Hồ sơ bị trả lại do không tuân thủ)",
            "Thẩm định kỹ thuật RR No. 11.31: Giới hạn cứng PFD Article 21 (Bảng 21-4) và EPFD Article 22 (Khuyến nghị ITU-R S.1503)",
            "Hệ sinh thái phần mềm ITU BR: SpaceCap (Bóc tách dữ liệu AP4), SpaceVal/BRSIS (Kiểm tra cú pháp), SpacePub (Đọc công báo BR IFIC), GIBC (Kiểm tra PFD & Phụ lục 7), TFA (Bảng phân bổ tần số)",
            "Nguyên tắc Thu hồi Chi phí (Cost recovery principles and fees)",
            "Quy định Đưa vào Sử dụng (BIU - RR No. 11.44C) và Nghị quyết Resolution 35 (WRC-19) về các mốc triển khai chòm sao (10% sau 2 năm, 50% sau 5 năm, 100% sau 7 năm)",
            "Sứ mệnh phi địa tĩnh thời gian ngắn (Short-Duration Missions - SDM) theo Resolution 32 (WRC-19)",
            "Vận hành theo RR No. 4.4 (Không gây nhiễu có hại, không đòi hỏi bảo vệ) và Tạm ngừng theo RR No. 11.49 (Tối đa 3 năm)"
        ],
        "relevance_to_vietnam": "TRỌNG TÂM CỦA HỆ THỐNG: Cung cấp đầy đủ căn cứ pháp lý để Hội đồng AI thẩm định tính đầy đủ theo Phụ lục 4, kiểm tra giới hạn cứng PFD/EPFD bảo vệ Vinasat-1/2 và theo dõi tiến độ chòm sao theo Resolution 35."
    },
    {
        "chapter_num": 4,
        "title": "Type of Services and Spectrum",
        "vietnamese_title": "Chương 4: Các Loại hình Dịch vụ & Băng tần Vô tuyến Vũ trụ",
        "page_range": "99 - 105",
        "key_topics": [
            "Nghiệp vụ Vận hành Vũ trụ (Space Operation Service - SOS): Đo xa, điều khiển và bám (TT&C), các dải tần 2 025 - 2 110 MHz (trái đất lên) và 2 200 - 2 290 MHz (vũ trụ xuống) kèm quy tắc bảo vệ RR No. 22.1",
            "Nghiệp vụ Vô tuyến Nghiệp dư qua Vệ tinh (Amateur-satellite service): Băng tần 144-146 MHz, 435-438 MHz, cơ chế phối hợp trước với IARU",
            "Nghiệp vụ Thăm dò Trái đất qua Vệ tinh (EESS) và Nghiệp vụ Khí tượng Vệ tinh (MetSat)",
            "Nghiệp vụ Nghiên cứu Vũ trụ (Space research service - SRS)",
            "Nghiệp vụ Cố định qua Vệ tinh (FSS) & Nghiệp vụ Di động qua Vệ tinh (MSS): Phân định dải Ku (10.7-12.75 GHz, 14-14.5 GHz), dải Ka (17.7-20.2 GHz, 27.5-30 GHz) và dải Q/V (37.5-42.5 GHz, 47.2-51.4 GHz)"
        ],
        "relevance_to_vietnam": "Hỗ trợ tra cứu nhanh điều kiện cấp phép và dải tần hoạt động cho các mạng vệ tinh LEO/GSO tại Việt Nam (thuộc Vùng 3 ITU - Region 3)."
    },
    {
        "chapter_num": 5,
        "title": "Types of Missions",
        "vietnamese_title": "Chương 5: Phân loại Nhiệm vụ Vũ trụ của Vệ tinh nhỏ",
        "page_range": "106 - 111",
        "key_topics": [
            "Nhiệm vụ Nghiên cứu Khoa học (Scientific missions): Khảo sát tầng điện ly, nhật quyển, tia gamma vũ trụ",
            "Nhiệm vụ Giáo dục & Đào tạo (Educational missions): Đào tạo kỹ sư không gian thông qua dự án vệ tinh sinh viên",
            "Nhiệm vụ Trình diễn Công nghệ (Experimental missions): Thử nghiệm động cơ đẩy vi mô, vật liệu mới, ăng-ten xòe",
            "Nhiệm vụ Thương mại (Commercial missions): Cung cấp băng rộng Internet, viễn thám thương mại, dịch vụ IoT toàn cầu",
            "Nhiệm vụ Không gian Sâu & Thám hiểm Mặt trăng (Deep space & Lunar missions): CubeSat viễn chinh liên hành tinh",
            "Nhiệm vụ Thời gian ngắn (Short-duration missions - SDM): Sứ mệnh dưới 3 năm"
        ],
        "relevance_to_vietnam": "Phân loại hồ sơ thẩm định mạng vệ tinh nộp cho Hội đồng AI để áp dụng quy trình rút gọn (SDM / Giáo dục) hoặc quy trình thẩm định phối hợp chặt chẽ (Thương mại FSS/MSS)."
    },
    {
        "chapter_num": 6,
        "title": "Space Object Registration",
        "vietnamese_title": "Chương 6: Đăng ký Vật thể Không gian theo Công ước Liên Hợp Quốc",
        "page_range": "112 - 113",
        "key_topics": [
            "Công ước Đăng ký Vật thể phóng vào Không gian vũ trụ năm 1974 (UN Registration Convention - UNOOSA)",
            "Nghĩa vụ của Quốc gia phóng (Launching State) trong việc lập sổ đăng bạ quốc gia và gửi thông báo tới Tổng Thư ký LHQ",
            "Thông tin bắt buộc: Tên quốc gia phóng, ký hiệu vật thể, ngày phóng, vị trí phóng, tham số quỹ đạo cơ bản (chu kỳ, độ nghiêng, viễn điểm, cận điểm), chức năng chung của vật thể"
        ],
        "relevance_to_vietnam": "Đảm bảo tính tuân thủ pháp lý kép: Đăng ký phổ tần với ITU (BR) và Đăng ký quyền tài phán vật thể bay với Liên Hợp Quốc (UNOOSA) khi Việt Nam phóng vệ tinh."
    },
    {
        "chapter_num": 7,
        "title": "Launch Considerations",
        "vietnamese_title": "Chương 7: Dịch vụ Phóng & Cơ hội Bay ghép (Rideshare)",
        "page_range": "114 - 131",
        "key_topics": [
            "Các nhà cung cấp dịch vụ phóng chính: Arianespace (Tên lửa Vega-C với cơ cấu SSMS, Ariane 6 với MLS), China Great Wall Industry Corp (CGWIC tên lửa Long March), SpaceX (Chương trình Transporter Rideshare Falcon 9)",
            "Cơ cấu chứa và tách vệ tinh tiêu chuẩn (Dispenser & Canister systems): Hạn chế rung lắc, chống sốc nhiệt và an toàn tách",
            "Yêu cầu cấp phép vô tuyến trước khi ký hợp đồng phóng (Launch authorization vs Spectrum license)"
        ],
        "relevance_to_vietnam": "Tham khảo lộ trình đàm phán hợp đồng phóng vệ tinh và bảo đảm tần số điều khiển TT&C đã có thông báo xuất bản trước (API) trước khi đưa vệ tinh vào bệ phóng."
    },
    {
        "chapter_num": 8,
        "title": "Space Debris Mitigation",
        "vietnamese_title": "Chương 8: Giảm thiểu Rác vũ trụ & Tiêu chuẩn Hủy Quỹ đạo",
        "page_range": "132 - 134",
        "key_topics": [
            "Hướng dẫn của Ủy ban Điều phối Rác vũ trụ Liên cơ quan (IADC) và Ủy ban LHQ về Sử dụng Hòa bình Không gian (UN COPUOS)",
            "Quy tắc 25 năm (25-year de-orbit rule): Vệ tinh kết thúc sứ mệnh trong vùng LEO (< 2000 km) phải tự hủy hoặc hạ quỹ đạo để rơi vào bầu khí quyển trong vòng không quá 25 năm",
            "Ngưỡng rủi ro thương vong khi tái nhập khí quyển (Re-entry casualty risk threshold): Phải thấp hơn 10^-4 (1/10.000)",
            "Quy trình thụ động hóa năng lượng (Passivation): Xả hết năng lượng pin hóa học và xả cạn áp suất bình nhiên liệu để ngăn chặn nguy cơ nổ vỡ thứ cấp trên quỹ đạo"
        ],
        "relevance_to_vietnam": "Đưa tiêu chí giảm thiểu rác vũ trụ và thời hạn tồn tại sau sứ mệnh vào danh mục kiểm tra an toàn khi thẩm định các mạng vệ tinh LEO bay qua không phận Việt Nam."
    },
    {
        "chapter_num": 9,
        "title": "Case Studies & Constellation Architectures",
        "vietnamese_title": "Chương 9: Nghiên cứu Điển hình Chòm sao Vệ tinh Thực tế",
        "page_range": "135 - 200",
        "key_topics": [
            "Vệ tinh Khoa học & Viễn thám: DIWATA-1 (Philippines), HORYU-4, RISESAT, QUESS (Vệ tinh lượng tử)",
            "Vệ tinh Giáo dục CubeSat: XI-IV, XI-V, QB50 (Mạng 50 CubeSat nghiên cứu tầng nhiệt quyển)",
            "Vệ tinh Địa tĩnh cỡ nhỏ thương mại (Small GEO): Astranis (Vệ tinh 400kg, xử lý tín hiệu số SDR, giải pháp sốc nhiệt và bức xạ trong dải GEO)",
            "Chòm sao Viễn thám thương mại Jilin-1 (CGSTL): Chòm viễn thám quang học lớn, trạm mặt đất di động khẩn cấp",
            "Chòm sao Băng rộng Non-GSO Starlink (SpaceX): 4.408 vệ tinh ở 5 cấu hình quỹ đạo (độ cao 540-570 km, góc nghiêng 53°, 70°, 97.6°), đường liên kết quang học laser liên vệ tinh (ISL), cơ chế tránh va chạm tự động và kiểm soát giới hạn EPFD bảo vệ GSO"
        ],
        "relevance_to_vietnam": "Cung cấp bộ tham số cấu hình thực tế chuẩn hóa để nạp vào mô hình giả lập và đối chiếu hồ sơ Starlink, OneWeb, Jilin-1 khi xin giấy phép hoạt động tại Việt Nam."
    }
]

# Bộ công cụ phần mềm ITU BR (Section 3.5.5)
BR_SOFTWARE_TOOLKIT = [
    {
        "name": "SpaceCap",
        "full_name": "Space Capture Software",
        "version": "v9.1 / v9.2",
        "role": "Bắt giữ & Nhập liệu Hồ sơ Điện tử",
        "description": "Phần mềm chính thức của Cục Thông tin Vô tuyến (BR) để thu thập dữ liệu hồ sơ mạng vệ tinh theo định dạng Phụ lục 4 (RR Appendix 4). Xuất tệp cơ sở dữ liệu SNS (.mdb / .xml).",
        "supported_filings": "API/A, CR/C, Notification Part I-S, Earth Station (trạm mặt đất)"
    },
    {
        "name": "SpaceVal / BRSIS Validation",
        "full_name": "Space Validation Software",
        "version": "v9.x",
        "role": "Thẩm định Cú pháp & Toàn vẹn Dữ liệu",
        "description": "Kiểm tra toàn bộ các trường bắt buộc, quy tắc toàn vẹn tham chiếu, giới hạn góc nghiêng, băng tần hợp lệ trước khi gửi hồ sơ chính thức qua hệ thống e-Submission của ITU.",
        "supported_filings": "Kiểm tra lỗi Fatal Error, Warning và Reference checks cho mọi loại hồ sơ"
    },
    {
        "name": "SpacePub",
        "full_name": "Space Publication Browser",
        "version": "v9.x",
        "role": "Đọc & Khai thác Ấn phẩm Công báo BR IFIC",
        "description": "Công cụ tra cứu và in ấn các mục công báo đặc biệt (Special Sections) phát hành 2 tuần/lần trên đĩa DVD/tải về từ mạng BR IFIC (Space Services).",
        "supported_filings": "Xem chi tiết đồ họa chùm sóng GIMS, bảng phân kênh tần số và danh sách quốc gia bị ảnh hưởng"
    },
    {
        "name": "GIBC",
        "full_name": "Graphical Interference Bureau Check",
        "version": "v9.x",
        "role": "Tính toán Can nhiễu Kỹ thuật Độc lập",
        "description": "Phần mềm tính toán độc lập của ITU dùng để kiểm tra giới hạn cứng PFD theo Điều 21, xác định đường biên phối hợp theo Phụ lục 7 (Appendix 7) và độ tăng nhiệt độ nhiễu Delta T/T theo Phụ lục 8.",
        "supported_filings": "PFD Art 21, Appendix 7 Contours, Appendix 8 Delta T/T, Rec. ITU-R S.1428"
    },
    {
        "name": "TFA Software",
        "full_name": "Table of Frequency Allocations Software",
        "version": "Edition 2024",
        "role": "Tra cứu Bảng Phân bổ Tần số Quốc tế",
        "description": "Phần mềm tra cứu Điều 5 Thể lệ Vô tuyến (RR Article 5), phân định các nghiệp vụ ưu tiên (Primary) và thứ cấp (Secondary) theo 3 Khu vực (Region 1, Region 2, Region 3).",
        "supported_filings": "Tra cứu cước chú chân trang (Footnotes), điều kiện áp dụng RR No. 9.11A / 9.21"
    },
    {
        "name": "SAM",
        "full_name": "Space Advance Publication & Examination Tool",
        "version": "Web-based / Desktop",
        "role": "Hỗ trợ Phân tích và Xử lý Bất đồng",
        "description": "Hệ thống hỗ trợ cơ quan quản lý (Administrations) gửi phản đối kỹ thuật (Comments) khi phát hiện mạng vệ tinh của nước khác có nguy cơ gây nhiễu trong thời hạn 4 tháng.",
        "supported_filings": "Bình luận API/B, phản đối phối hợp CR/D"
    }
]

# Bảng tiêu chuẩn Resolution 35 (WRC-19) - Milestone deployment
RES_35_MILESTONES_RULES = {
    "resolution": "Resolution 35 (WRC-19)",
    "applicable_services": "Non-GSO satellite systems in FSS (Fixed-satellite service), MSS (Mobile-satellite service), and BSS",
    "frequency_bands": [
        "10.7 - 12.75 GHz (Ku-band downlink)",
        "14.0 - 14.5 GHz (Ku-band uplink)",
        "17.7 - 20.2 GHz (Ka-band downlink)",
        "27.5 - 30.0 GHz (Ka-band uplink)",
        "37.5 - 42.5 GHz (Q/V-band downlink)",
        "47.2 - 51.4 GHz (Q/V-band uplink)"
    ],
    "milestones": [
        {
            "milestone": "Mốc 1 (1st Milestone)",
            "deadline": "2 năm sau khi kết thúc thời hạn đưa vào sử dụng 7 năm (7 + 2 = 9 năm)",
            "minimum_deployment_percentage": "10% tổng số vệ tinh đã thông báo",
            "regulatory_consequence": "Nếu không đạt 10%, số lượng vệ tinh trong hồ sơ thông báo tại Sổ Master Register sẽ bị BR giảm bớt tương ứng."
        },
        {
            "milestone": "Mốc 2 (2nd Milestone)",
            "deadline": "5 năm sau khi kết thúc thời hạn 7 năm (7 + 5 = 12 năm)",
            "minimum_deployment_percentage": "50% tổng số vệ tinh đã thông báo",
            "regulatory_consequence": "Nếu không đạt 50%, số lượng vệ tinh ghi nhận trong MIFR sẽ bị cắt giảm theo tỷ lệ thực tế đã phóng."
        },
        {
            "milestone": "Mốc 3 (3rd Milestone)",
            "deadline": "7 năm sau khi kết thúc thời hạn 7 năm (7 + 7 = 14 năm)",
            "minimum_deployment_percentage": "100% tổng số vệ tinh đã thông báo",
            "regulatory_consequence": "Hồ sơ chính thức bị khóa vĩnh viễn ở số lượng vệ tinh thực tế đang vận hành trên quỹ đạo."
        }
    ]
}

# Tiêu chuẩn thẩm định kỹ thuật theo RR No. 11.31 (Table 3 trong Handbook)
EXAMINATION_11_31_STANDARDS = [
    {
        "provision": "RR Article 5 (Table of Frequency Allocations)",
        "scope": "Phù hợp nghiệp vụ và dải tần",
        "description": "Tần số xin phân bổ phải thuộc nghiệp vụ được phép tại Region tương ứng (Việt Nam thuộc Region 3), không vi phạm cước chú cấm."
    },
    {
        "provision": "RR Article 21 (Hard PFD Limits - Bảng 21-4)",
        "scope": "Mật độ thông lượng công suất tại mặt đất",
        "description": "Giới hạn công suất tối đa máy phát vệ tinh chiếu xuống mặt đất theo các góc ngẩng (0°-5°, 5°-25°, 25°-90°) nhằm bảo vệ trạm cố định mặt đất (FS) và 5G."
    },
    {
        "provision": "RR Article 22 (Hard EPFD Limits)",
        "scope": "Mật độ thông lượng công suất tương đương bảo vệ GSO",
        "description": "Giới hạn tích lũy EPFD từ chòm Non-GSO chiếu vào ăng-ten trạm mặt đất thu vệ tinh Địa tĩnh GSO (như trạm thu Vinasat) theo Khuyến nghị ITU-R S.1503."
    },
    {
        "provision": "RR No. 22.1 (Space Operation TT&C protection)",
        "scope": "Bảo vệ kênh điều khiển đo xa",
        "description": "Kênh đo xa điều khiển phải hạn chế công suất phát và chỉ phát trong thời gian cần thiết để duy trì an toàn bay."
    },
    {
        "provision": "RR No. 4.4 (Derogation Operation)",
        "scope": "Vận hành ngoại lệ không gây nhiễu",
        "description": "Nếu hồ sơ không đạt kết luận thuận lợi theo 11.31 nhưng nước nộp cam kết hoạt động theo 4.4 (không gây can nhiễu, không đòi hỏi bảo vệ), BR sẽ ghi nhận ở chế độ 'For information only'."
    }
]

# Starlink Constellation Architecture trích xuất từ Table 27 Sổ tay ITU
STARLINK_ITU_BENCHMARK = {
    "system_name": "Starlink non-GSO Satellite System (SpaceX Filing Benchmark)",
    "total_satellites": 4408,
    "source_in_handbook": "Chapter 9, Section 9.5.3, Table 27, Page 184",
    "configurations": [
        {"planes": 72, "sats_per_plane": 22, "total": 1584, "altitude_km": 550, "inclination_deg": 53.0},
        {"planes": 72, "sats_per_plane": 22, "total": 1584, "altitude_km": 540, "inclination_deg": 53.2},
        {"planes": 36, "sats_per_plane": 20, "total": 720, "altitude_km": 570, "inclination_deg": 70.0},
        {"planes": 6, "sats_per_plane": 58, "total": 348, "altitude_km": 560, "inclination_deg": 97.6},
        {"planes": 4, "sats_per_plane": 43, "total": 172, "altitude_km": 560, "inclination_deg": 97.6}
    ],
    "key_technologies": [
        "Phased array beam-forming steered antenna beams",
        "Optical Inter-Satellite Links (ISL - Laser liên vệ tinh)",
        "Autonomous collision avoidance manoeuvres based on star trackers",
        "Cryptographic spectrum access and dynamic steerable cell footprints"
    ]
}


def get_handbook_summary() -> Dict[str, Any]:
    """Trả về thông tin tổng quan, danh mục 9 chương và các bộ quy chuẩn cốt lõi."""
    return {
        "status": "success",
        "metadata": HANDBOOK_METADATA,
        "total_chapters": len(HANDBOOK_CHAPTERS),
        "chapters": HANDBOOK_CHAPTERS,
        "satellite_classification": SATELLITE_MASS_CLASSIFICATION,
        "software_toolkit": BR_SOFTWARE_TOOLKIT,
        "resolution_35": RES_35_MILESTONES_RULES,
        "examination_11_31": EXAMINATION_11_31_STANDARDS,
        "starlink_benchmark": STARLINK_ITU_BENCHMARK
    }


def get_handbook_chapters() -> List[Dict[str, Any]]:
    """Trả về danh sách 9 chương kèm mô tả chi tiết."""
    return HANDBOOK_CHAPTERS


def get_handbook_chapter_detail(chapter_num: int) -> Optional[Dict[str, Any]]:
    """Trả về chi tiết 1 chương cụ thể."""
    for ch in HANDBOOK_CHAPTERS:
        if ch["chapter_num"] == chapter_num:
            return ch
    return None


def search_handbook(query: str) -> List[Dict[str, Any]]:
    """Tìm kiếm nội dung trong cơ sở tri thức Sổ tay ITU Handbook."""
    if not query or len(query.strip()) == 0:
        return []
    
    q = query.lower().strip()
    results = []

    # 1. Tìm trong Chapters
    for ch in HANDBOOK_CHAPTERS:
        matched_topics = [t for t in ch["key_topics"] if q in t.lower()]
        if q in ch["title"].lower() or q in ch["vietnamese_title"].lower() or matched_topics:
            results.append({
                "type": "CHAPTER",
                "title": f"Chương {ch['chapter_num']}: {ch['title']}",
                "page_range": ch["page_range"],
                "snippet": ch["vietnamese_title"] + " — " + (matched_topics[0] if matched_topics else ch["key_topics"][0]),
                "relevance": ch["relevance_to_vietnam"]
            })

    # 2. Tìm trong Software Toolkit
    for sw in BR_SOFTWARE_TOOLKIT:
        if q in sw["name"].lower() or q in sw["full_name"].lower() or q in sw["description"].lower():
            results.append({
                "type": "BR_SOFTWARE",
                "title": f"Phần mềm ITU BR: {sw['name']} ({sw['full_name']})",
                "page_range": "Chapter 3, Section 3.5.5, Page 82-84",
                "snippet": sw["description"],
                "relevance": f"Hỗ trợ loại hồ sơ: {sw['supported_filings']}"
            })

    # 3. Tìm trong Resolution 35
    if any(k in q for k in ["res 35", "resolution 35", "milestone", "mốc", "triển khai"]):
        results.append({
            "type": "REGULATION_RES35",
            "title": "Nghị quyết Resolution 35 (WRC-19) - Mốc Triển khai Chòm sao Non-GSO",
            "page_range": "Chapter 3, Section 3.7.3.1, Page 88-90",
            "snippet": "Quy định tiến độ triển khai 10% sau 2 năm, 50% sau 5 năm và 100% sau 7 năm. Không đạt sẽ bị cắt giảm dung lượng trên MIFR.",
            "relevance": "Tiêu chí thẩm định bắt buộc cho Starlink, OneWeb, Amazon Kuiper."
        })

    # 4. Tìm trong Hard limits 11.31
    for st in EXAMINATION_11_31_STANDARDS:
        if q in st["provision"].lower() or q in st["scope"].lower() or q in st["description"].lower():
            results.append({
                "type": "RR_ARTICLE_11_31",
                "title": f"Thẩm định Kỹ thuật: {st['provision']}",
                "page_range": "Chapter 3, Section 3.5.4, Page 70-82",
                "snippet": st["description"],
                "relevance": f"Phạm vi: {st['scope']}"
            })

    # 5. Tìm trong Case study
    if any(k in q for k in ["starlink", "spacex", "4408", "jilin", "astranis", "geo nhỏ"]):
        results.append({
            "type": "CASE_STUDY",
            "title": "Nghiên cứu Điển hình: Starlink, Jilin-1 & Astranis",
            "page_range": "Chapter 9, Section 9.5, Page 183-195",
            "snippet": "Kiến trúc 4.408 vệ tinh Starlink (Table 27), công nghệ laser liên vệ tinh ISL và phân bổ mặt phẳng quỹ đạo.",
            "relevance": "Dữ liệu tham chiếu benchmark cho hệ thống mô phỏng 3D."
        })

    return results
