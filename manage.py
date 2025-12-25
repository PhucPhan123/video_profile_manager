#!/usr/bin/env python
"""Tiện ích dòng lệnh của Django cho các tác vụ quản trị."""
import os
import sys


def main():
    """Chạy các tác vụ quản trị."""
    # Thiết lập biến môi trường trỏ đến file settings của folder core
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không thể import Django. Bạn có chắc chắn nó đã được cài đặt và "
            "khả dụng trên biến môi trường PYTHONPATH của bạn không? Bạn đã "
            "quên kích hoạt môi trường ảo (virtual environment) chưa?"
        ) from exc
    
    # Thực thi các tham số truyền vào từ dòng lệnh (như runserver, migrate,...)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()