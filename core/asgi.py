import os
from django.core.asgi import get_asgi_application

# Thiết lập biến môi trường chỉ đến file cấu hình settings của dự án
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Khởi tạo ứng dụng ASGI của Django
# Đây là entry point cho các server ASGI như Daphne hoặc Uvicorn
django_asgi_app = get_asgi_application()

# Nếu sau này bạn dùng WebSockets (Channels), bạn sẽ cấu hình thêm ở đây:
# from channels.routing import ProtocolTypeRouter, URLRouter
# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": URLRouter([...])
# })

application = django_asgi_app