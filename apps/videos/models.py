from django.db import models
import uuid

class PromptTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    genre = models.CharField(max_length=10000, verbose_name="Thể loại video")
    template_text = models.TextField(verbose_name="Nội dung template")

    def __str__(self):
        return f"{self.genre} - {self.id}"

class VideoProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    youtube_link = models.URLField(max_length=5000)
    minio_input_path = models.CharField(max_length=5000) # Link mp4 đầu vào
    assigned_user = models.CharField(max_length=100)
    
    # Lưu danh sách object: prompt, kết quả, link đầu ra
    # Cấu trúc: [{"prompt": "...", "result": "...", "output_path": "..."}, ...]
    processing_details = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Video {self.id} - {self.assigned_user}"