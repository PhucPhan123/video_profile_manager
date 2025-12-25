# 🎥 Video Profile Management System

Hệ thống quản lý Video Profile tích hợp xử lý cắt video tự động bằng MoviePy, lưu trữ đối tượng Minio (S3) và quản lý dữ liệu PostgreSQL. Dự án được đóng gói hoàn toàn bằng Docker để chạy trên WSL.

## 🚀 Tính năng chính

### 1. Quản lý Video Profile
- **Khởi tạo & Sửa**: Lưu UUID, Youtube link, Minio input link và người phụ trách
- **Preview đa kênh**: 
  - Xem trực tiếp video từ YouTube (embedded player)
  - Preview video gốc từ Minio
  - Preview video kết quả sau khi cắt
- **Xử lý Video**: Cắt video theo khoảng thời gian (giây) và lưu thông tin kết quả vào JSONField
- **Quản lý Segments**: Thêm, sửa, xóa các segments với prompt, result, và video output

### 2. Quản lý Prompt Template
- **Template theo thể loại**: Tạo các mẫu prompt theo thể loại (Review, Shorts, Education, Tutorial, Interview, Vlog, etc.)
- **Auto-generate Prompt**: Tự động sinh prompt dựa trên template và link YouTube
- **Placeholder system**: Sử dụng `{youtube_link}` làm placeholder

### 3. Hệ thống bổ trợ
- **Admin Dashboard**: Giao diện quản lý dữ liệu mạnh mẽ của Django
- **Storage**: Tích hợp Minio để quản lý file media tập trung
- **Video Processing**: MoviePy (FFmpeg) để cắt và xử lý video

## 🛠 Công nghệ sử dụng

- **Backend**: Django 4.2 (Python 3.11)
- **Database**: PostgreSQL 15
- **Storage**: Minio (S3 Compatible)
- **Video Processing**: MoviePy (FFmpeg)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript
- **Deployment**: Docker & Docker Compose

## 📦 Cấu trúc thư mục

```
video_profile_manager/
├── apps/
│   └── videos/
│       ├── migrations/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py          # VideoProfile & PromptTemplate models
│       ├── urls.py            # Routing cho app videos
│       ├── utils.py           # Minio SDK & MoviePy logic
│       └── views.py           # Controllers
├── core/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py            # Cấu hình Django, Postgres, Minio
│   ├── urls.py                # Root routing
│   └── wsgi.py
├── static/                    # CSS, JS files
│   ├── css/
│   └── js/
├── templates/                 # HTML templates
│   ├── base.html              # Layout chính
│   └── videos/
│       ├── prompt_form.html   # Tạo/Sửa Prompt Template
│       ├── prompt_list.html   # Danh sách Prompts
│       ├── video_form.html    # Tạo/Sửa Video với Preview
│       └── video_list.html    # Danh sách Videos
├── .env                       # Environment variables
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── requirements.txt
└── README.md
```

## ⚙️ Cài đặt và Chạy

### 1. Yêu cầu
- Docker Desktop (Windows)
- WSL 2 Integration enabled
- Git

### 2. Clone project
```bash
git clone https://github.com/PhucPhan123/video_profile_manager.git
cd video_profile_manager
```

### 3. Cấu hình môi trường
File `.env` đã được tạo sẵn với cấu hình mặc định:
```env
DB_NAME=videoprofile_db
DB_USER=admin
DB_PASSWORD=secretpassword
DB_HOST=db
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### 4. Khởi chạy hệ thống
```bash
# Build và chạy các container
docker-compose up --build -d

# Chạy migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Tạo superuser
docker-compose exec web python manage.py createsuperuser
```

### 5. Truy cập
- **Website**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin
- **Minio Console**: http://localhost:9001 (User/Pass: minioadmin/minioadmin)

## 📖 Hướng dẫn sử dụng

### Tạo Prompt Template
1. Truy cập **Quản lý Prompt** → **Tạo Prompt**
2. Nhập tên template, chọn thể loại
3. Viết nội dung template, sử dụng `{youtube_link}` làm placeholder
4. Lưu template

### Tạo Video Profile
1. Truy cập **Tạo Video**
2. Nhập tiêu đề, link YouTube
3. Upload video MP4 lên Minio và nhập đường dẫn
4. Chọn Prompt Template và click **Generate** để tạo prompt tự động
5. Lưu video

### Quản lý Segments
1. Mở video profile đã tạo
2. Click **Thêm Segment**
3. Nhập prompt, result, start time, end time
4. Click **Cắt Video** để xử lý
5. Xem preview video output ngay sau khi xử lý xong

### Cắt Video
1. Đảm bảo video đã có Minio input link
2. Trong segment, nhập Start Time và End Time (giây)
3. Click **Cắt Video**
4. Hệ thống sẽ:
   - Download video từ Minio
   - Cắt video bằng MoviePy
   - Upload kết quả lên Minio
   - Hiển thị preview ngay lập tức

## 🔧 Các lệnh hữu ích

```bash
# Xem logs
docker-compose logs -f web

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Remove all volumes (WARNING: Xóa data)
docker-compose down -v

# Access Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## ⚠️ Lưu ý kỹ thuật

### Bộ nhớ
MoviePy xử lý video trong bộ nhớ tạm `/tmp` của container. Đảm bảo video đầu vào không quá lớn (khuyến nghị < 500MB) để tránh tràn bộ nhớ.

### WSL Performance
Để đạt tốc độ tốt nhất, đặt thư mục dự án bên trong hệ thống file của Linux (ví dụ: `~/projects/`) thay vì truy cập qua `/mnt/c/`.

### Minio Access
- Bucket `video-profiles` được tạo tự động khi khởi động
- Upload file vào thư mục `inputs/` cho video đầu vào
- Video đã cắt sẽ được lưu trong `outputs/`

### Video Format
- Chỉ hỗ trợ MP4
- Codec: H.264 video, AAC audio
- Khuyến nghị resolution: 720p hoặc 1080p

## 🐛 Troubleshooting

### Container không start
```bash
# Check logs
docker-compose logs web
docker-compose logs db
docker-compose logs minio

# Rebuild
docker-compose down
docker-compose up --build
```

### Database connection error
```bash
# Wait for db to be ready
docker-compose exec db pg_isready -U admin

# Restart web service
docker-compose restart web
```

### Minio connection error
```bash
# Check Minio health
curl http://localhost:9000/minio/health/live

# Access Minio console
# http://localhost:9001
```

## 📝 API Endpoints

### Video Profiles
- `GET /videos/list/` - Danh sách videos
- `GET /videos/create/` - Form tạo video
- `GET /videos/<uuid>/edit/` - Form sửa video
- `POST /videos/<uuid>/delete/` - Xóa video

### Prompt Templates
- `GET /videos/prompts/` - Danh sách prompts
- `GET /videos/prompts/create/` - Form tạo prompt
- `GET /videos/prompts/<uuid>/edit/` - Form sửa prompt
- `POST /videos/prompts/<uuid>/delete/` - Xóa prompt

### AJAX APIs
- `POST /videos/api/generate-prompt/` - Generate prompt từ template
- `POST /videos/api/process-segment/` - Cắt video segment
- `POST /videos/api/add-segment/` - Thêm segment
- `POST /videos/api/delete-segment/` - Xóa segment

## 📄 License

MIT License

## 👥 Contributors

- Phuc Phan (@PhucPhan123)

## 🔗 Links

- GitHub: https://github.com/PhucPhan123/video_profile_manager
- Issues: https://github.com/PhucPhan123/video_profile_manager/issues