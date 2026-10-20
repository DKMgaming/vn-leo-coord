# leo_coord — Công cụ hỗ trợ quản lý tần số & quỹ đạo chòm sao vệ tinh LEO

Công cụ phân tích kỹ thuật phục vụ nhiệm vụ "Xây dựng Chiến lược quản lý tần số,
quỹ đạo vệ tinh chòm sao tầm thấp (LEO) và phối hợp quốc tế về tần số vũ trụ"
(Cục Tần số vô tuyến điện — cơ quan thường trực Ủy ban Vũ trụ Việt Nam).

## Phạm vi chức năng

- Mô hình chòm sao Walker LEO, lan truyền quỹ đạo, phân tích phủ sóng trên lãnh thổ Việt Nam
- Kiểm tra sàng lọc PFD (RR Article 21) và EPFD (RR Article 22, phương pháp rút gọn theo ITU-R S.1503)
- Xác định nhu cầu phối hợp tần số (RR Article 9, Appendix 5/8)
- Theo dõi mốc triển khai chòm sao (ITU Res 35 WRC-19) — chống "xí phần" tài nguyên quỹ đạo
- Cơ sở dữ liệu phối hợp tần số vệ tinh quốc gia (SQLite)

## Lưu ý quan trọng

Đây là công cụ HỖ TRỢ phân tích, sàng lọc. Mọi kết luận cấp phép hay phối hợp
chính thức phải dựa trên văn bản ITU/FCC hiện hành và phần mềm của ITU BR
(SpaceCap, GIMS, S.1503). Toàn bộ dữ liệu demo trong `data/demo/` đều là HƯ CẤU
và được gắn nhãn rõ ràng.

## Cài đặt

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Chạy nhanh

```bash
.venv/bin/leo-coord assess --constellation data/demo/constellation_demo.yaml --report out/bao_cao.html
.venv/bin/pytest
```

## Cấu trúc

- `leo_coord/` — mã nguồn (orbits, coverage, pfd, epfd, coordination, milestones, database, report, cli)
- `configs/leo_coord.yaml` — mọi ngưỡng kỹ thuật đều versioned tại đây, không hard-code trong source
- `data/reference/` — bảng tham chiếu ITU (PFD, EPFD, cung phối hợp), kèm trạng thái xác minh
- `data/demo/` — chòm sao demo HƯ CẤU
- `docs/` — báo cáo nghiên cứu quốc tế
- `tests/` — kiểm thử pytest
