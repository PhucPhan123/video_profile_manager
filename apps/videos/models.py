# apps/videos/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.utils import timezone


class PromptTemplate(models.Model):
    """Model cho quản lý Prompt Template"""
    
    CATEGORY_CHOICES = [
        ('review', 'Review'),
        ('shorts', 'Shorts'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('tutorial', 'Tutorial'),
        ('news', 'News'),
        ('vlog', 'Vlog'),
        ('gaming', 'Gaming'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='UUID'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Tên Template'
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='Thể loại Video'
    )
    template_content = models.TextField(
        verbose_name='Nội dung Template',
        help_text='Sử dụng {youtube_title}, {youtube_description}, {youtube_tags} làm placeholders'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mô tả'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Kích hoạt'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'prompt_templates'
        verbose_name = 'Prompt Template'
        verbose_name_plural = 'Prompt Templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class VideoProfile(models.Model):
    """Model cho quản lý Video Profile"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='UUID'
    )
    
    # Basic Information
    title = models.CharField(
        max_length=500,
        verbose_name='Tiêu đề Video',
        blank=True,
        null=True
    )
    youtube_url = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        verbose_name='Link Youtube',
        help_text='URL đầy đủ của video Youtube'
    )
    youtube_video_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Youtube Video ID'
    )
    
    # Minio Storage
    minio_input_url = models.URLField(
        max_length=500,
        verbose_name='Link Minio MP4 Input',
        help_text='URL file MP4 gốc trên Minio',
        blank=True,
        null=True
    )
    minio_bucket = models.CharField(
        max_length=100,
        default='videos',
        verbose_name='Minio Bucket'
    )
    minio_input_object_name = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Tên Object Input trong Minio'
    )
    
    # Assignment
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_videos',
        verbose_name='Người phụ trách'
    )
    
    # Processing Results - JSONField chứa list các object
    # Structure: [
    #   {
    #       "prompt": "Prompt text...",
    #       "prompt_result": "Kết quả AI response...",
    #       "start_time": 10.5,
    #       "end_time": 30.2,
    #       "output_minio_url": "https://minio.../output.mp4",
    #       "output_object_name": "outputs/video_uuid_segment_1.mp4",
    #       "processed_at": "2024-01-01T12:00:00Z",
    #       "status": "completed"
    #   }
    # ]
    processing_results = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Danh sách kết quả xử lý',
        help_text='List các object chứa prompt, kết quả và link output'
    )
    
    # Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Trạng thái'
    )
    duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Thời lượng (giây)'
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Kích thước file (bytes)'
    )
    
    # Additional Info
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ghi chú'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tags'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'video_profiles'
        verbose_name = 'Video Profile'
        verbose_name_plural = 'Video Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_user', '-created_at']),
        ]
    
    def __str__(self):
        return self.title or f"Video {self.id}"
    
    def get_youtube_embed_url(self):
        """Lấy embed URL cho Youtube video"""
        if self.youtube_video_id:
            return f"https://www.youtube.com/embed/{self.youtube_video_id}"
        return None
    
    def get_processing_count(self):
        """Đếm số lượng segment đã xử lý"""
        return len(self.processing_results) if self.processing_results else 0
    
    def add_processing_result(self, prompt, prompt_result, start_time, end_time, 
                            output_url, output_object_name, status='completed'):
        """Thêm một kết quả xử lý mới vào list"""
        if not isinstance(self.processing_results, list):
            self.processing_results = []
        
        result = {
            'prompt': prompt,
            'prompt_result': prompt_result,
            'start_time': start_time,
            'end_time': end_time,
            'output_minio_url': output_url,
            'output_object_name': output_object_name,
            'processed_at': timezone.now().isoformat(),
            'status': status
        }
        
        self.processing_results.append(result)
        self.save()
        
        return result
    
    def get_completed_segments(self):
        """Lấy danh sách các segment đã hoàn thành"""
        if not self.processing_results:
            return []
        return [r for r in self.processing_results if r.get('status') == 'completed']


class VideoProcessingLog(models.Model):
    """Model để log quá trình xử lý video"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    video_profile = models.ForeignKey(
        VideoProfile,
        on_delete=models.CASCADE,
        related_name='processing_logs',
        verbose_name='Video Profile'
    )
    level = models.CharField(
        max_length=20,
        choices=LOG_LEVEL_CHOICES,
        default='info',
        verbose_name='Mức độ'
    )
    message = models.TextField(
        verbose_name='Thông báo'
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Chi tiết'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian'
    )
    
    class Meta:
        db_table = 'video_processing_logs'
        verbose_name = 'Processing Log'
        verbose_name_plural = 'Processing Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.message[:50]}"