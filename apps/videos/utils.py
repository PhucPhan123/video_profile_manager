# apps/videos/utils.py
import os
import re
import tempfile
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from moviepy.editor import VideoFileClip
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import yt_dlp

logger = logging.getLogger(__name__)


# ============================================================
# YOUTUBE UTILITIES
# ============================================================

def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract Youtube video ID from URL
    
    Args:
        url: Youtube URL
        
    Returns:
        Video ID or None if not found
    """
    # Pattern for youtube URLs
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_youtube_metadata(url: str) -> Dict[str, Any]:
    """
    Get metadata from Youtube video using yt-dlp
    
    Args:
        url: Youtube URL
        
    Returns:
        Dictionary containing video metadata
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            metadata = {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'tags': info.get('tags', []),
                'thumbnail': info.get('thumbnail', ''),
                'channel': info.get('channel', ''),
                'channel_id': info.get('channel_id', ''),
            }
            
            return metadata
            
    except Exception as e:
        logger.error(f"Error getting Youtube metadata: {str(e)}")
        raise Exception(f"Không thể lấy metadata từ Youtube: {str(e)}")


def download_youtube_video(url: str, output_path: Optional[str] = None) -> str:
    """
    Download Youtube video
    
    Args:
        url: Youtube URL
        output_path: Output file path (optional)
        
    Returns:
        Path to downloaded video file
    """
    if not output_path:
        output_path = tempfile.mktemp(suffix='.mp4')
    
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return output_path
        
    except Exception as e:
        logger.error(f"Error downloading Youtube video: {str(e)}")
        raise Exception(f"Không thể tải video từ Youtube: {str(e)}")


# ============================================================
# MINIO UTILITIES
# ============================================================

def get_minio_client() -> Minio:
    """
    Get Minio client instance
    
    Returns:
        Minio client
    """
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL
    )


def upload_to_minio(file_path: str, bucket: str, object_name: str) -> str:
    """
    Upload file to Minio
    
    Args:
        file_path: Path to file to upload
        bucket: Minio bucket name
        object_name: Object name in bucket
        
    Returns:
        URL to uploaded file
    """
    try:
        client = get_minio_client()
        
        # Create bucket if not exists
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info(f"Created bucket: {bucket}")
        
        # Upload file
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
        )
        
        # Generate URL
        url = f"{settings.MINIO_EXTERNAL_ENDPOINT}/{bucket}/{object_name}"
        
        logger.info(f"Uploaded to Minio: {url}")
        return url
        
    except S3Error as e:
        logger.error(f"Minio S3 Error: {str(e)}")
        raise Exception(f"Lỗi khi upload lên Minio: {str(e)}")
    except Exception as e:
        logger.error(f"Error uploading to Minio: {str(e)}")
        raise Exception(f"Lỗi khi upload: {str(e)}")


def download_from_minio(bucket: str, object_name: str, output_path: Optional[str] = None) -> str:
    """
    Download file from Minio
    
    Args:
        bucket: Minio bucket name
        object_name: Object name in bucket
        output_path: Output file path (optional)
        
    Returns:
        Path to downloaded file
    """
    if not output_path:
        output_path = tempfile.mktemp(suffix=os.path.splitext(object_name)[1])
    
    try:
        client = get_minio_client()
        
        # Download file
        client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=output_path
        )
        
        logger.info(f"Downloaded from Minio: {bucket}/{object_name}")
        return output_path
        
    except S3Error as e:
        logger.error(f"Minio S3 Error: {str(e)}")
        raise Exception(f"Lỗi khi download từ Minio: {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading from Minio: {str(e)}")
        raise Exception(f"Lỗi khi download: {str(e)}")


def delete_from_minio(bucket: str, object_name: str) -> bool:
    """
    Delete file from Minio
    
    Args:
        bucket: Minio bucket name
        object_name: Object name in bucket
        
    Returns:
        True if successful
    """
    try:
        client = get_minio_client()
        
        client.remove_object(
            bucket_name=bucket,
            object_name=object_name
        )
        
        logger.info(f"Deleted from Minio: {bucket}/{object_name}")
        return True
        
    except S3Error as e:
        logger.error(f"Minio S3 Error: {str(e)}")
        raise Exception(f"Lỗi khi xóa file từ Minio: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting from Minio: {str(e)}")
        return False


def get_minio_presigned_url(bucket: str, object_name: str, expires: int = 3600) -> str:
    """
    Get presigned URL for Minio object
    
    Args:
        bucket: Minio bucket name
        object_name: Object name in bucket
        expires: URL expiration time in seconds (default 1 hour)
        
    Returns:
        Presigned URL
    """
    try:
        client = get_minio_client()
        
        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(seconds=expires)
        )
        
        return url
        
    except S3Error as e:
        logger.error(f"Minio S3 Error: {str(e)}")
        raise Exception(f"Lỗi khi tạo presigned URL: {str(e)}")


# ============================================================
# VIDEO PROCESSING UTILITIES
# ============================================================

def cut_video_segment(input_file: str, start_time: float, end_time: float, 
                     output_path: Optional[str] = None) -> str:
    """
    Cut video segment using MoviePy
    
    Args:
        input_file: Path to input video file
        start_time: Start time in seconds
        end_time: End time in seconds
        output_path: Output file path (optional)
        
    Returns:
        Path to output video file
    """
    if not output_path:
        output_path = tempfile.mktemp(suffix='.mp4')
    
    try:
        logger.info(f"Cutting video from {start_time}s to {end_time}s")
        
        # Load video
        video = VideoFileClip(input_file)
        
        # Validate time range
        if start_time < 0:
            start_time = 0
        if end_time > video.duration:
            end_time = video.duration
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        
        # Cut segment
        segment = video.subclip(start_time, end_time)
        
        # Write output
        segment.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=tempfile.mktemp(suffix='.m4a'),
            remove_temp=True,
            logger=None  # Suppress moviepy logs
        )
        
        # Close clips
        segment.close()
        video.close()
        
        logger.info(f"Video segment saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error cutting video: {str(e)}")
        raise Exception(f"Lỗi khi cắt video: {str(e)}")


def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Get video information
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary containing video info
    """
    try:
        video = VideoFileClip(file_path)
        
        info = {
            'duration': video.duration,
            'fps': video.fps,
            'size': video.size,  # (width, height)
            'width': video.w,
            'height': video.h,
            'aspect_ratio': video.aspect_ratio,
        }
        
        video.close()
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise Exception(f"Lỗi khi lấy thông tin video: {str(e)}")


def merge_video_segments(segment_files: list, output_path: Optional[str] = None) -> str:
    """
    Merge multiple video segments
    
    Args:
        segment_files: List of video file paths
        output_path: Output file path (optional)
        
    Returns:
        Path to merged video file
    """
    if not output_path:
        output_path = tempfile.mktemp(suffix='.mp4')
    
    try:
        from moviepy.editor import concatenate_videoclips
        
        logger.info(f"Merging {len(segment_files)} video segments")
        
        # Load all clips
        clips = [VideoFileClip(f) for f in segment_files]
        
        # Concatenate
        final_clip = concatenate_videoclips(clips, method='compose')
        
        # Write output
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        # Close clips
        for clip in clips:
            clip.close()
        final_clip.close()
        
        logger.info(f"Merged video saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error merging videos: {str(e)}")
        raise Exception(f"Lỗi khi merge video: {str(e)}")


# ============================================================
# PROMPT GENERATION UTILITIES
# ============================================================

def generate_prompt_from_template(template, youtube_url: str) -> str:
    """
    Generate prompt from template and Youtube URL
    
    Args:
        template: PromptTemplate instance
        youtube_url: Youtube URL
        
    Returns:
        Generated prompt string
    """
    try:
        # Get Youtube metadata
        metadata = get_youtube_metadata(youtube_url)
        
        # Replace placeholders in template
        prompt = template.template_content
        
        replacements = {
            '{youtube_title}': metadata.get('title', ''),
            '{youtube_description}': metadata.get('description', ''),
            '{youtube_tags}': ', '.join(metadata.get('tags', [])),
            '{youtube_uploader}': metadata.get('uploader', ''),
            '{youtube_channel}': metadata.get('channel', ''),
            '{youtube_duration}': str(metadata.get('duration', 0)),
            '{youtube_views}': str(metadata.get('view_count', 0)),
        }
        
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        raise Exception(f"Lỗi khi generate prompt: {str(e)}")


# ============================================================
# FILE CLEANUP UTILITIES
# ============================================================

def cleanup_temp_files(*file_paths):
    """
    Clean up temporary files
    
    Args:
        *file_paths: Variable number of file paths to delete
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {str(e)}")