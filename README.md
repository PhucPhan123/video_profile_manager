🎥 Video Profile Management System
Hệ thống quản lý Profile Video tích hợp xử lý cắt video tự động bằng MoviePy, lưu trữ đối tượng Minio (S3) và quản lý dữ liệu PostgreSQL. Dự án được đóng gói hoàn toàn bằng Docker để chạy trên WSL.

🚀 Tính năng chính
1. Quản lý Video Profile
Khởi tạo: Lưu UUID, Youtube link, Minio input link và người phụ trách.

Preview đa kênh: Xem trực tiếp video từ Youtube, Video gốc từ Minio và Video kết quả sau khi cắt.

Xử lý Video: Cắt video theo khoảng thời gian (giây) và lưu thông tin kết quả (prompt, result, link output) vào JSONField.

2. Quản lý Prompt
Template: Tạo các mẫu prompt theo thể loại (Review, Shorts, Education).

Generator: Tự động sinh prompt dựa trên template và link Youtube.

3. Hệ thống bổ trợ
Admin Dashboard: Giao diện quản lý dữ liệu mạnh mẽ của Django.

Storage: Tích hợp Minio để quản lý file media tập trung.

🛠 Công nghệ sử dụng
Backend: Django 4.2 (Python 3.11)

Database: PostgreSQL 15

Storage: Minio (S3 Compatible)

Video Processing: MoviePy (FFmpeg)

Frontend: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript

Deployment: Docker & Docker Compose

📦 Cấu trúc thư mục
video_manager_project/
├── apps/
│   └── videos/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py          # Định nghĩa VideoProfile và PromptTemplate
│       ├── urls.py            # Routing cho app videos
│       ├── utils.py           # Logic MoviePy và Minio SDK
│       └── views.py           # Controller xử lý logic hiển thị và cắt video
├── core/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py        # Cấu hình kết nối Postgres, Minio, Static
│   ├── urls.py            # Root routing của toàn dự án
│   └── wsgi.py
├── static/                # Chứa file CSS, JS dùng chung
│   ├── css/
│   └── js/
├── templates/             # Giao diện HTML (Django Templates)
│   ├── base.html          # Layout khung
│   └── videos/
│       ├── prompt_form.html
│       ├── prompt_list.html
│       ├── video_form.html    # Màn hình Khởi tạo - Sửa & Preview
│       └── video_list.html
├── .env                   # Biến môi trường (DB_PASSWORD, MINIO_KEYS,...)
├── Dockerfile             # Build Python 3.11 image cho Django & MoviePy
├── docker-compose.yml     # Điều phối Django, PostgreSQL, Minio
├── manage.py
└── requirements.txt       # Danh sách thư viện (Django, moviepy, minio, psycopg2)
⚙️ Hướng dẫn cài đặt trên WSL
1. Chuẩn bị
Đảm bảo bạn đã cài đặt Docker Desktop trên Windows và kích hoạt tính năng WSL 2 Integration.

2. Clone và thiết lập biến môi trường
Tạo file .env tại thư mục gốc:

Code snippet

DB_NAME=videoprofile_db
DB_USER=admin
DB_PASSWORD=secretpassword
DB_HOST=db
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
3. Khởi chạy hệ thống
Mở Terminal WSL và chạy:

Bash

# Build và chạy các container ngầm
docker compose up --build -d

# Thực hiện migrate database
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Tạo tài khoản quản trị
docker compose exec web python manage.py createsuperuser
4. Truy cập
Website: http://localhost:8000

Admin Interface: http://localhost:8000/admin

Minio Console: http://localhost:9001 (User/Pass: minioadmin)

📖 Hướng dẫn sử dụng nhanh
Tạo Prompt Template: Truy cập mục "Quản lý Prompt" để tạo các mẫu prompt theo thể loại video.

Khởi tạo Video: * Dán link Youtube để preview.

Nhập link file MP4 từ Minio.

Cắt Video: Nhập giây bắt đầu và kết thúc, bấm Generate. Hệ thống sẽ:

Tải file từ Minio.

Dùng MoviePy cắt video.

Upload kết quả lên Minio và hiển thị link Preview ngay lập tức.

⚠️ Lưu ý kỹ thuật
Bộ nhớ: MoviePy xử lý video trong bộ nhớ tạm /tmp của container. Hãy đảm bảo video đầu vào không quá lớn để tránh tràn bộ nhớ.

WSL Performance: Để đạt tốc độ tốt nhất, hãy đặt thư mục dự án bên trong hệ thống file của Linux (ví dụ: ~/projects/) thay vì truy cập qua /mnt/c/.