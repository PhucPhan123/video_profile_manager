from django.contrib import admin
from .models import VideoProfile, PromptTemplate

@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    # Các cột hiển thị trong danh sách
    list_display = ('id', 'genre', 'template_short_text')
    # Cho phép tìm kiếm theo thể loại
    search_fields = ('genre', 'template_text')
    # Bộ lọc ở bên phải
    list_filter = ('genre',)

    def template_short_text(self, obj):
        """Hiển thị bản tóm tắt nội dung template"""
        return obj.template_text[:50] + "..." if len(obj.template_text) > 50 else obj.template_text
    template_short_text.short_description = 'Nội dung Template'


@admin.register(VideoProfile)
class VideoProfileAdmin(admin.ModelAdmin):
    # Các cột hiển thị trong danh sách video
    list_display = ('id', 'assigned_user', 'youtube_link', 'created_at')
    # Cho phép click vào UUID hoặc User để vào trang sửa
    list_display_links = ('id', 'assigned_user')
    # Bộ lọc theo thời gian và người dùng
    list_filter = ('created_at', 'assigned_user')
    # Tìm kiếm theo UUID hoặc Link
    search_fields = ('id', 'youtube_link', 'assigned_user')
    # Sắp xếp theo ngày mới nhất lên đầu
    ordering = ('-created_at',)
    
    # Cấu hình để hiển thị JSONField đẹp hơn (chế độ readonly)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('id', 'assigned_user', 'youtube_link', 'minio_input_path')
        }),
        ('Dữ liệu xử lý (JSON)', {
            'fields': ('processing_details',),
            'description': 'Danh sách các prompt, kết quả và link video đầu ra.'
        }),
        ('Thời gian hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',), # Ẩn đi mặc định
        }),
    )

# Thay đổi tiêu đề trang Admin
admin.site.site_header = "Hệ thống Quản lý Video Profile"
admin.site.site_title = "Video Manager Admin"
admin.site.index_title = "Bảng điều khiển hệ thống"