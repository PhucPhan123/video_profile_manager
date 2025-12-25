# apps/videos/forms.py
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .models import VideoProfile, PromptTemplate
import re


class PromptTemplateForm(forms.ModelForm):
    """Form cho tạo và sửa Prompt Template"""
    
    class Meta:
        model = PromptTemplate
        fields = ['name', 'category', 'template_content', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên template...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'template_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Nhập nội dung template...\nSử dụng {youtube_title}, {youtube_description}, {youtube_tags}'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả về template này...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Tên Template',
            'category': 'Thể loại Video',
            'template_content': 'Nội dung Template',
            'description': 'Mô tả',
            'is_active': 'Kích hoạt'
        }
    
    def clean_template_content(self):
        content = self.cleaned_data.get('template_content')
        if not content:
            raise ValidationError('Nội dung template không được để trống.')
        
        # Kiểm tra có ít nhất 10 ký tự
        if len(content.strip()) < 10:
            raise ValidationError('Nội dung template phải có ít nhất 10 ký tự.')
        
        return content


class VideoProfileForm(forms.ModelForm):
    """Form cho tạo và sửa Video Profile"""
    
    # Additional fields cho video processing
    start_time = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Giây bắt đầu',
            'step': '0.1',
            'min': '0'
        }),
        label='Thời gian bắt đầu (giây)'
    )
    
    end_time = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Giây kết thúc',
            'step': '0.1',
            'min': '0'
        }),
        label='Thời gian kết thúc (giây)'
    )
    
    processing_prompt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Nhập prompt để xử lý video...'
        }),
        label='Prompt xử lý'
    )
    
    class Meta:
        model = VideoProfile
        fields = [
            'title', 'youtube_url', 'minio_input_url', 
            'assigned_user', 'minio_bucket', 'minio_input_object_name',
            'status', 'notes', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề video...'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'minio_input_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'http://minio:9000/bucket/video.mp4'
            }),
            'assigned_user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'minio_bucket': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'videos'
            }),
            'minio_input_object_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'inputs/video.mp4'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú về video...'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'tag1, tag2, tag3'
            }),
        }
        labels = {
            'title': 'Tiêu đề',
            'youtube_url': 'Link Youtube',
            'minio_input_url': 'Link Minio MP4 Input',
            'assigned_user': 'Người phụ trách',
            'minio_bucket': 'Minio Bucket',
            'minio_input_object_name': 'Tên Object trong Minio',
            'status': 'Trạng thái',
            'notes': 'Ghi chú',
            'tags': 'Tags (phân cách bằng dấu phẩy)'
        }
    
    def clean_youtube_url(self):
        url = self.cleaned_data.get('youtube_url')
        if not url:
            raise ValidationError('Link Youtube không được để trống.')
        
        # Extract Youtube video ID
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        
        match = re.match(youtube_regex, url)
        if not match:
            raise ValidationError('Link Youtube không hợp lệ.')
        
        return url
    
    def clean_minio_input_url(self):
        url = self.cleaned_data.get('minio_input_url')
        if url:
            # Validate URL format
            validator = URLValidator()
            try:
                validator(url)
            except ValidationError:
                raise ValidationError('Link Minio không hợp lệ.')
        return url
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            if isinstance(tags, str):
                # Convert comma-separated string to list
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                return tag_list
            elif isinstance(tags, list):
                return tags
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validate time range if both are provided
        if start_time is not None and end_time is not None:
            if start_time < 0:
                self.add_error('start_time', 'Thời gian bắt đầu phải >= 0.')
            if end_time <= start_time:
                self.add_error('end_time', 'Thời gian kết thúc phải lớn hơn thời gian bắt đầu.')
        
        return cleaned_data


class VideoProcessingForm(forms.Form):
    """Form riêng cho xử lý video (cắt video)"""
    
    prompt_template = forms.ModelChoiceField(
        queryset=PromptTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Chọn Template Prompt',
        empty_label='-- Chọn template hoặc nhập thủ công --'
    )
    
    custom_prompt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Hoặc nhập prompt tùy chỉnh...'
        }),
        label='Prompt tùy chỉnh'
    )
    
    start_time = forms.FloatField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.1',
            'min': '0'
        }),
        label='Thời gian bắt đầu (giây)',
        initial=0
    )
    
    end_time = forms.FloatField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10',
            'step': '0.1',
            'min': '0'
        }),
        label='Thời gian kết thúc (giây)',
        initial=10
    )
    
    def clean(self):
        cleaned_data = super().clean()
        prompt_template = cleaned_data.get('prompt_template')
        custom_prompt = cleaned_data.get('custom_prompt')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Must have either template or custom prompt
        if not prompt_template and not custom_prompt:
            raise ValidationError('Vui lòng chọn template hoặc nhập prompt tùy chỉnh.')
        
        # Validate time range
        if start_time is not None and end_time is not None:
            if start_time < 0:
                self.add_error('start_time', 'Thời gian bắt đầu phải >= 0.')
            if end_time <= start_time:
                self.add_error('end_time', 'Thời gian kết thúc phải lớn hơn thời gian bắt đầu.')
        
        return cleaned_data


class PromptGeneratorForm(forms.Form):
    """Form để generate prompt từ template và Youtube URL"""
    
    youtube_url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=...'
        }),
        label='Link Youtube'
    )
    
    template = forms.ModelChoiceField(
        queryset=PromptTemplate.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Chọn Template'
    )
    
    def clean_youtube_url(self):
        url = self.cleaned_data.get('youtube_url')
        
        # Extract Youtube video ID
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        
        match = re.match(youtube_regex, url)
        if not match:
            raise ValidationError('Link Youtube không hợp lệ.')
        
        return url