"""
Utility functions for Minio and MoviePy operations
"""
import os
import tempfile
from minio import Minio
from minio.error import S3Error
from django.conf import settings
from moviepy.editor import VideoFileClip
import logging

logger = logging.getLogger(__name__)


class MinioClient:
    """Singleton Minio Client"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinioClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Minio client"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Tạo bucket nếu chưa tồn tại"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
    
    def upload_file(self, file_path, object_name):
        """
        Upload file lên Minio
        
        Args:
            file_path: Đường dẫn file local
            object_name: Tên object trên Minio
        
        Returns:
            str: Object name nếu thành công, None nếu thất bại
        """
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
            )
            logger.info(f"Uploaded {file_path} to {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    def download_file(self, object_name, file_path):
        """
        Download file từ Minio
        
        Args:
            object_name: Tên object trên Minio
            file_path: Đường dẫn lưu file local
        
        Returns:
            str: File path nếu thành công, None nếu thất bại
        """
        try:
            self.client.fget_object(
                self.bucket_name,
                object_name,
                file_path,
            )
            logger.info(f"Downloaded {object_name} to {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    def get_presigned_url(self, object_name, expires=3600):
        """
        Lấy presigned URL cho object
        
        Args:
            object_name: Tên object trên Minio
            expires: Thời gian hết hạn (giây)
        
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def delete_file(self, object_name):
        """
        Xóa file từ Minio
        
        Args:
            object_name: Tên object trên Minio
        
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def list_objects(self, prefix=''):
        """
        Liệt kê objects trong bucket
        
        Args:
            prefix: Prefix để filter objects
        
        Returns:
            list: Danh sách object names
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []


class VideoProcessor:
    """Video processing utilities using MoviePy"""
    
    def __init__(self):
        self.minio_client = MinioClient()
    
    def cut_video(self, input_path, output_path, start_time, end_time):
        """
        Cắt video từ start_time đến end_time
        
        Args:
            input_path: Đường dẫn video đầu vào
            output_path: Đường dẫn video đầu ra
            start_time: Thời gian bắt đầu (giây)
            end_time: Thời gian kết thúc (giây)
        
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            logger.info(f"Cutting video from {start_time}s to {end_time}s")
            
            # Load video
            video = VideoFileClip(input_path)
            
            # Validate time range
            if start_time < 0:
                start_time = 0
            if end_time > video.duration:
                end_time = video.duration
            if start_time >= end_time:
                raise ValueError(f"Invalid time range: {start_time}s to {end_time}s")
            
            # Cut video
            cut_clip = video.subclip(start_time, end_time)
            
            # Write output
            cut_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None
            )
            
            # Clean up
            cut_clip.close()
            video.close()
            
            logger.info(f"Video cut successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cutting video: {e}")
            return False
    
    def process_segment(self, minio_input_path, start_time, end_time, segment_index):
        """
        Xử lý 1 segment: download từ Minio, cắt video, upload lại
        
        Args:
            minio_input_path: Đường dẫn file input trên Minio
            start_time: Thời gian bắt đầu (giây)
            end_time: Thời gian kết thúc (giây)
            segment_index: Index của segment
        
        Returns:
            str: Đường dẫn output trên Minio nếu thành công, None nếu thất bại
        """
        temp_input = None
        temp_output = None
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                temp_input = f.name
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                temp_output = f.name
            
            # Download input video from Minio
            logger.info(f"Downloading input video: {minio_input_path}")
            if not self.minio_client.download_file(minio_input_path, temp_input):
                raise Exception("Failed to download input video")
            
            # Cut video
            if not self.cut_video(temp_input, temp_output, start_time, end_time):
                raise Exception("Failed to cut video")
            
            # Generate output path on Minio
            base_name = os.path.splitext(os.path.basename(minio_input_path))[0]
            output_name = f"outputs/{base_name}_segment_{segment_index}_{start_time}_{end_time}.mp4"
            
            # Upload output video to Minio
            logger.info(f"Uploading output video: {output_name}")
            if not self.minio_client.upload_file(temp_output, output_name):
                raise Exception("Failed to upload output video")
            
            return output_name
            
        except Exception as e:
            logger.error(f"Error processing segment: {e}")
            return None
            
        finally:
            # Clean up temporary files
            if temp_input and os.path.exists(temp_input):
                os.remove(temp_input)
            if temp_output and os.path.exists(temp_output):
                os.remove(temp_output)
    
    def get_video_duration(self, minio_path):
        """
        Lấy độ dài video (giây)
        
        Args:
            minio_path: Đường dẫn file trên Minio
        
        Returns:
            float: Độ dài video (giây), None nếu lỗi
        """
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                temp_file = f.name
            
            if not self.minio_client.download_file(minio_path, temp_file):
                return None
            
            video = VideoFileClip(temp_file)
            duration = video.duration
            video.close()
            
            return duration
            
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return None
            
        finally:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)


def generate_prompt_from_template(template, youtube_link):
    """
    Generate prompt từ template và youtube link
    
    Args:
        template: PromptTemplate instance hoặc template string
        youtube_link: Link YouTube
    
    Returns:
        str: Generated prompt
    """
    from apps.videos.models import PromptTemplate
    
    if isinstance(template, PromptTemplate):
        template_content = template.template_content
    else:
        template_content = str(template)
    
    # Replace placeholder
    prompt = template_content.replace('{youtube_link}', youtube_link or '')
    
    # Có thể thêm logic xử lý khác ở đây (gọi AI, v.v.)
    
    return prompt