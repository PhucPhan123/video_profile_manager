"""
Models for Video Profile Management System
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator


class PromptTemplate(models.Model):
    """Model cho Prompt Template"""
    
    CATEGORY_CHOICES = [
        ('review', 'Review'),
        ('shorts', 'Shorts'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('tutorial', 'Tutorial'),
        ('interview', 'Interview'),
        ('vlog', 'Vlog'),
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
        verbose_name='Tên Template',
        help_text='Tên mô tả cho template'
    )
    
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='Thể loại video',
        db_index=True
    )
    
    template_content = models.TextField(
        verbose_name='Nội dung Template',
        help_text='Template sử dụng để generate prompt. Dùng {youtube_link} làm placeholder'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mô tả',
        help_text='Mô tả chi tiết về template này'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động',
        help_text='Template có đang được sử dụng không'
    )
    
    class Meta:
        verbose_name = 'Prompt Template'
        verbose_name_plural = 'Prompt Templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class VideoProfile(models.Model):
    """Model cho Video Profile"""
    
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
    
    title = models.CharField(
        max_length=300,
        verbose_name='Tiêu đề video',
        help_text='Tiêu đề mô tả cho video'
    )
    
    youtube_link = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        verbose_name='Link YouTube',
        help_text='URL của video YouTube gốc',
        blank=True,
        null=True
    )
    
    minio_input_link = models.CharField(
        max_length=500,
        verbose_name='Link Minio Input',
        help_text='Đường dẫn file MP4 đầu vào trên Minio (vd: video-profiles/input/video.mp4)',
        blank=True,
        null=True
    )
    
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_profiles',
        verbose_name='Người phụ trách'
    )
    
    prompt_template = models.ForeignKey(
        PromptTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_profiles',
        verbose_name='Prompt Template'
    )
    
    segments = models.JSONField(
        default=list,
        verbose_name='Danh sách segments',
        help_text='Mảng các object chứa: prompt, result, minio_output_link, start_time, end_time'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Trạng thái',
        db_index=True
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ghi chú',
        help_text='Ghi chú thêm về video'
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
        verbose_name = 'Video Profile'
        verbose_name_plural = 'Video Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def get_total_segments(self):
        """Lấy tổng số segments"""
        return len(self.segments) if self.segments else 0
    
    def get_processed_segments(self):
        """Lấy số segments đã xử lý (có output link)"""
        if not self.segments:
            return 0
        return sum(1 for seg in self.segments if seg.get('minio_output_link'))
    
    def get_progress_percentage(self):
        """Tính phần trăm hoàn thành"""
        total = self.get_total_segments()
        if total == 0:
            return 0
        return int((self.get_processed_segments() / total) * 100)