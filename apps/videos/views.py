# apps/videos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
import re
import json

from .models import VideoProfile, PromptTemplate, VideoProcessingLog
from .forms import (
    VideoProfileForm, PromptTemplateForm, 
    VideoProcessingForm, PromptGeneratorForm
)
from .utils import (
    extract_youtube_video_id, get_youtube_metadata,
    cut_video_segment, upload_to_minio, download_from_minio,
    generate_prompt_from_template
)


# ============================================================
# VIDEO PROFILE VIEWS
# ============================================================

class VideoProfileListView(LoginRequiredMixin, ListView):
    """Màn hình quản lý video - View toàn bộ video"""
    model = VideoProfile
    template_name = 'videos/video_list.html'
    context_object_name = 'videos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(youtube_url__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by assigned user
        assigned_user = self.request.GET.get('assigned_user')
        if assigned_user:
            queryset = queryset.filter(assigned_user_id=assigned_user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = VideoProfile.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class VideoProfileDetailView(LoginRequiredMixin, DetailView):
    """View chi tiết video profile"""
    model = VideoProfile
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processing_results'] = self.object.processing_results or []
        context['processing_logs'] = self.object.processing_logs.all()[:50]
        context['completed_segments'] = self.object.get_completed_segments()
        return context


class VideoProfileCreateView(LoginRequiredMixin, CreateView):
    """Màn hình khởi tạo video profile"""
    model = VideoProfile
    form_class = VideoProfileForm
    template_name = 'videos/video_form.html'
    success_url = reverse_lazy('videos:video_list')
    
    def form_valid(self, form):
        # Extract Youtube video ID
        youtube_url = form.cleaned_data.get('youtube_url')
        if youtube_url:
            video_id = extract_youtube_video_id(youtube_url)
            form.instance.youtube_video_id = video_id
            
            # Get metadata from Youtube
            try:
                metadata = get_youtube_metadata(youtube_url)
                if metadata:
                    if not form.instance.title:
                        form.instance.title = metadata.get('title', '')
                    form.instance.duration = metadata.get('duration')
            except Exception as e:
                messages.warning(self.request, f'Không thể lấy metadata từ Youtube: {str(e)}')
        
        messages.success(self.request, 'Video profile đã được tạo thành công!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Khởi tạo Video Profile'
        context['submit_text'] = 'Tạo mới'
        context['templates'] = PromptTemplate.objects.filter(is_active=True)
        return context


class VideoProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Màn hình sửa video profile"""
    model = VideoProfile
    form_class = VideoProfileForm
    template_name = 'videos/video_form.html'
    
    def get_success_url(self):
        return reverse_lazy('videos:video_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Update Youtube video ID if URL changed
        youtube_url = form.cleaned_data.get('youtube_url')
        if youtube_url:
            video_id = extract_youtube_video_id(youtube_url)
            form.instance.youtube_video_id = video_id
        
        messages.success(self.request, 'Video profile đã được cập nhật!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sửa Video Profile'
        context['submit_text'] = 'Cập nhật'
        context['video'] = self.object
        context['processing_results'] = self.object.processing_results or []
        context['templates'] = PromptTemplate.objects.filter(is_active=True)
        return context


class VideoProfileDeleteView(LoginRequiredMixin, DeleteView):
    """Xóa video profile"""
    model = VideoProfile
    template_name = 'videos/video_confirm_delete.html'
    success_url = reverse_lazy('videos:video_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Video profile đã được xóa!')
        return super().delete(request, *args, **kwargs)


# ============================================================
# VIDEO PROCESSING VIEWS
# ============================================================

class VideoProcessingView(LoginRequiredMixin, View):
    """View xử lý cắt video"""
    
    def post(self, request, pk):
        video = get_object_or_404(VideoProfile, pk=pk)
        form = VideoProcessingForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        # Get processing parameters
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']
        custom_prompt = form.cleaned_data.get('custom_prompt')
        prompt_template = form.cleaned_data.get('prompt_template')
        
        # Determine prompt to use
        if custom_prompt:
            prompt = custom_prompt
        elif prompt_template:
            # Generate prompt from template
            prompt = generate_prompt_from_template(
                template=prompt_template,
                youtube_url=video.youtube_url
            )
        else:
            return JsonResponse({
                'success': False,
                'error': 'Vui lòng chọn template hoặc nhập prompt.'
            }, status=400)
        
        try:
            # Update status
            video.status = 'processing'
            video.save()
            
            # Log start
            VideoProcessingLog.objects.create(
                video_profile=video,
                level='info',
                message='Bắt đầu xử lý cắt video',
                details={
                    'start_time': start_time,
                    'end_time': end_time,
                    'prompt': prompt
                }
            )
            
            # Download video from Minio
            input_file = download_from_minio(
                bucket=video.minio_bucket,
                object_name=video.minio_input_object_name
            )
            
            # Cut video segment
            output_file = cut_video_segment(
                input_file=input_file,
                start_time=start_time,
                end_time=end_time
            )
            
            # Upload result to Minio
            segment_number = len(video.processing_results) + 1
            output_object_name = f"outputs/{video.id}_segment_{segment_number}.mp4"
            output_url = upload_to_minio(
                file_path=output_file,
                bucket=video.minio_bucket,
                object_name=output_object_name
            )
            
            # Add processing result
            result = video.add_processing_result(
                prompt=prompt,
                prompt_result='',  # TODO: Integrate with AI for prompt result
                start_time=start_time,
                end_time=end_time,
                output_url=output_url,
                output_object_name=output_object_name,
                status='completed'
            )
            
            # Update status
            video.status = 'completed'
            video.save()
            
            # Log success
            VideoProcessingLog.objects.create(
                video_profile=video,
                level='success',
                message='Cắt video thành công',
                details=result
            )
            
            return JsonResponse({
                'success': True,
                'result': result,
                'message': 'Video đã được cắt thành công!'
            })
            
        except Exception as e:
            # Update status
            video.status = 'failed'
            video.save()
            
            # Log error
            VideoProcessingLog.objects.create(
                video_profile=video,
                level='error',
                message=f'Lỗi khi cắt video: {str(e)}',
                details={'exception': str(e)}
            )
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PromptGenerateView(LoginRequiredMixin, View):
    """Generate prompt từ template và Youtube URL"""
    
    def post(self, request):
        form = PromptGeneratorForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        youtube_url = form.cleaned_data['youtube_url']
        template = form.cleaned_data['template']
        
        try:
            prompt = generate_prompt_from_template(
                template=template,
                youtube_url=youtube_url
            )
            
            return JsonResponse({
                'success': True,
                'prompt': prompt
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# ============================================================
# PROMPT TEMPLATE VIEWS
# ============================================================

class PromptTemplateListView(LoginRequiredMixin, ListView):
    """Màn hình quản lý prompt - View toàn bộ prompt"""
    model = PromptTemplate
    template_name = 'videos/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(template_content__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = PromptTemplate.CATEGORY_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class PromptTemplateDetailView(LoginRequiredMixin, DetailView):
    """View chi tiết prompt template"""
    model = PromptTemplate
    template_name = 'videos/prompt_detail.html'
    context_object_name = 'prompt'


class PromptTemplateCreateView(LoginRequiredMixin, CreateView):
    """Màn hình khởi tạo prompt template"""
    model = PromptTemplate
    form_class = PromptTemplateForm
    template_name = 'videos/prompt_form.html'
    success_url = reverse_lazy('videos:prompt_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Prompt template đã được tạo thành công!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Khởi tạo Prompt Template'
        context['submit_text'] = 'Tạo mới'
        return context


class PromptTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Màn hình sửa prompt template"""
    model = PromptTemplate
    form_class = PromptTemplateForm
    template_name = 'videos/prompt_form.html'
    
    def get_success_url(self):
        return reverse_lazy('videos:prompt_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Prompt template đã được cập nhật!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sửa Prompt Template'
        context['submit_text'] = 'Cập nhật'
        return context


class PromptTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Xóa prompt template"""
    model = PromptTemplate
    template_name = 'videos/prompt_confirm_delete.html'
    success_url = reverse_lazy('videos:prompt_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Prompt template đã được xóa!')
        return super().delete(request, *args, **kwargs)


# ============================================================
# PREVIEW VIEWS
# ============================================================

class YoutubePreviewView(LoginRequiredMixin, View):
    """Preview Youtube video"""
    
    def get(self, request):
        youtube_url = request.GET.get('url')
        if not youtube_url:
            return JsonResponse({
                'success': False,
                'error': 'URL không được cung cấp'
            }, status=400)
        
        try:
            video_id = extract_youtube_video_id(youtube_url)
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            
            # Get metadata
            metadata = get_youtube_metadata(youtube_url)
            
            return JsonResponse({
                'success': True,
                'video_id': video_id,
                'embed_url': embed_url,
                'metadata': metadata
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# ============================================================
# DASHBOARD VIEW
# ============================================================

class DashboardView(LoginRequiredMixin, View):
    """Dashboard tổng quan"""
    
    def get(self, request):
        context = {
            'total_videos': VideoProfile.objects.count(),
            'total_prompts': PromptTemplate.objects.count(),
            'processing_videos': VideoProfile.objects.filter(status='processing').count(),
            'completed_videos': VideoProfile.objects.filter(status='completed').count(),
            'failed_videos': VideoProfile.objects.filter(status='failed').count(),
            'recent_videos': VideoProfile.objects.all()[:10],
            'active_prompts': PromptTemplate.objects.filter(is_active=True).count(),
        }
        return render(request, 'videos/dashboard.html', context)