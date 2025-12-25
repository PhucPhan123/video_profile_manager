"""
Admin configuration for Video Profile Management
"""
from django.contrib import admin
from .models import VideoProfile, PromptTemplate


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    """Admin cho PromptTemplate"""
    
    list_display = ['name', 'category', 'is_active', 'created_at', 'updated_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'template_content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('id', 'name', 'category', 'is_active')
        }),
        ('Nội dung Template', {
            'fields': ('template_content', 'description')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VideoProfile)
class VideoProfileAdmin(admin.ModelAdmin):
    """Admin cho VideoProfile"""
    
    list_display = ['title', 'status', 'assigned_user', 'get_progress', 'created_at', 'updated_at']
    list_filter = ['status', 'assigned_user', 'created_at']
    search_fields = ['title', 'youtube_link', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at', 'get_progress_display']
    autocomplete_fields = ['assigned_user', 'prompt_template']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('id', 'title', 'status', 'assigned_user', 'prompt_template')
        }),
        ('Links', {
            'fields': ('youtube_link', 'minio_input_link')
        }),
        ('Segments', {
            'fields': ('segments', 'get_progress_display'),
            'description': 'Danh sách các segments đã xử lý'
        }),
        ('Ghi chú', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_progress(self, obj):
        """Display progress percentage"""
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = 'Tiến độ'
    
    def get_progress_display(self, obj):
        """Display detailed progress info"""
        total = obj.get_total_segments()
        processed = obj.get_processed_segments()
        percentage = obj.get_progress_percentage()
        return f"{processed}/{total} segments ({percentage}%)"
    get_progress_display.short_description = 'Chi tiết tiến độ'