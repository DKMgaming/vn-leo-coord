FROM python:3.11-slim

# Thiết lập biến môi trường tối ưu cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8098

# Thư mục làm việc
WORKDIR /app

# Cài đặt curl (cho HEALTHCHECK) và mdbtools (để đọc file Microsoft Access .mdb trên Linux)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    mdbtools \
    && rm -rf /var/lib/apt/lists/*

# Sao chép các tệp cấu hình và mã nguồn
COPY pyproject.toml README.md ./
COPY configs/ ./configs/
COPY data/ ./data/
COPY docs/ ./docs/
COPY leo_coord/ ./leo_coord/
COPY web/ ./web/
COPY run_web.py .

# Cài đặt dependencies và thư viện phân tích tài liệu
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . python-docx openpyxl pandas

# Mở cổng dịch vụ
EXPOSE 8098

# Kiểm tra trạng thái hoạt động của Web App
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8098/ || exit 1

# Khởi chạy ứng dụng
CMD ["python", "run_web.py"]
