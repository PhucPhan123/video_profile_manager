# Sử dụng Python 3.11 như yêu cầu
FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết cho MoviePy và PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở port 8000 cho Django
EXPOSE 8000

# Lệnh chạy mặc định
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]