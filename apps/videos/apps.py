from django.apps import AppConfig

class VideosConfig(AppConfig):
    # Sử dụng kiểu dữ liệu BigAutoField cho các ID tự tăng (nếu có)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Quan trọng: Phải trỏ đúng đường dẫn tương đối từ thư mục gốc của dự án
    name = 'apps.videos'
    
    # Tên hiển thị thân thiện trên giao diện Admin của Django
    verbose_name = 'Quản lý Video Profile'

    def ready(self):
        """
        Hàm này được gọi khi Django khởi chạy xong.
        Bạn có thể đăng ký các 'signals' ở đây nếu cần 
        (ví dụ: tự động tạo thư mục trên Minio khi một VideoProfile được tạo).
        """
        pass