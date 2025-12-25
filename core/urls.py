from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Trang quản trị hệ thống (Django Admin)
    path('admin/', admin.site.urls),

    # 2. Điều hướng các URL liên quan đến Video và Prompt vào app 'videos'
    # Tất cả các link bắt đầu bằng tiền tố trống hoặc cụ thể sẽ được app videos xử lý
    path('', include('apps.videos.urls')),

    # 3. Trang chủ (Root URL)
    # Tự động chuyển hướng người dùng vào danh sách video khi truy cập domain gốc
    path('', lambda request: redirect('video_list', permanent=False)),

]

# 4. Cấu hình phục vụ file Static và Media trong môi trường Development
# Điều này cực kỳ quan trọng để hiển thị CSS/JS và Video khi chạy trên WSL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)