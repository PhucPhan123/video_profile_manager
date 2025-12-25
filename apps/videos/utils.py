import os
from moviepy.editor import VideoFileClip
from django.conf import settings
from minio import Minio

# Khởi tạo Minio Client (Lấy cấu hình từ settings.py)
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def cut_video_moviepy(input_local_path, output_local_path, start_sec, end_sec):
    """Sử dụng MoviePy để cắt video"""
    try:
        with VideoFileClip(input_local_path) as video:
            new_video = video.subclip(start_sec, end_sec)
            new_video.write_videofile(output_local_path, codec="libx264")
        return True
    except Exception as e:
        print(f"Error cutting video: {e}")
        return False

def upload_to_minio(file_path, object_name):
    """Upload file đã cắt lên Minio"""
    minio_client.fput_object(
        settings.MINIO_BUCKET_NAME, object_name, file_path
    )
    return f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{object_name}"