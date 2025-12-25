"""
Views for Video Profile Management System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
import logging

from .models import VideoProfile, PromptTemplate
from .utils import MinioClient, VideoProcessor, generate_prompt_from_template

logger = logging.getLogger(__name__)


# ============ VIDEO PROFILE VIEWS ============

def video_list(request):
    """Màn hình Quản lý video - Danh sách tất cả video profiles"""
    videos = VideoProfile.objects.all().select_related('assigned_user', 'prompt_template')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        videos = videos.filter(status=status_filter)
    
    # Filter by user if provided
    user_filter = request.GET.get('user')
    if user_filter:
        videos = videos.filter(assigned_user_id=user_filter)
    
    context = {
        'videos': videos,
        'status_choices': VideoProfile.STATUS_CHOICES,
    }
    return render(request, 'videos/video_list.html', context)


def video_detail(request, pk):
    """Xem chi tiết video profile - redirect đến video_edit"""
    return redirect('video_edit', pk=pk)


def video_create(request):
    """Màn hình Khởi tạo video profile"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            title = request.POST.get('title')
            youtube_link = request.POST.get('youtube_link', '').strip()
            minio_input_link = request.POST.get('minio_input_link', '').strip()
            assigned_user_id = request.POST.get('assigned_user')
            prompt_template_id = request.POST.get('prompt_template')
            notes = request.POST.get('notes', '')
            
            # Validate
            if not title:
                messages.error(request, 'Tiêu đề là bắt buộc')
                return redirect('video_create')
            
            # Tạo video profile
            video = VideoProfile.objects.create(
                title=title,
                youtube_link=youtube_link if youtube_link else None,
                minio_input_link=minio_input_link if minio_input_link else None,
                assigned_user_id=assigned_user_id if assigned_user_id else None,
                prompt_template_id=prompt_template_id if prompt_template_id else None,
                notes=notes,
                segments=[],
                status='draft'
            )
            
            messages.success(request, f'Đã tạo video profile: {video.title}')
            return redirect('video_edit', pk=video.id)
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            messages.error(request, f'Lỗi khi tạo video: {str(e)}')
            return redirect('video_create')
    
    # GET request
    from django.contrib.auth.models import User
    context = {
        'users': User.objects.all(),
        'prompt_templates': PromptTemplate.objects.filter(is_active=True),
    }
    return render(request, 'videos/video_form.html', context)


def video_edit(request, pk):
    """Màn hình Sửa video profile với preview"""
    video = get_object_or_404(VideoProfile, pk=pk)
    minio_client = MinioClient()
    
    if request.method == 'POST':
        try:
            # Update basic fields
            video.title = request.POST.get('title', video.title)
            video.youtube_link = request.POST.get('youtube_link', '').strip() or None
            video.minio_input_link = request.POST.get('minio_input_link', '').strip() or None
            video.notes = request.POST.get('notes', '')
            
            assigned_user_id = request.POST.get('assigned_user')
            video.assigned_user_id = assigned_user_id if assigned_user_id else None
            
            prompt_template_id = request.POST.get('prompt_template')
            video.prompt_template_id = prompt_template_id if prompt_template_id else None
            
            # Update segments from JSON
            segments_json = request.POST.get('segments', '[]')
            try:
                video.segments = json.loads(segments_json)
            except json.JSONDecodeError:
                messages.warning(request, 'Không thể parse segments JSON, giữ nguyên dữ liệu cũ')
            
            video.save()
            messages.success(request, 'Đã cập nhật video profile')
            return redirect('video_edit', pk=pk)
            
        except Exception as e:
            logger.error(f"Error updating video: {e}")
            messages.error(request, f'Lỗi khi cập nhật video: {str(e)}')
    
    # Generate presigned URLs for preview
    input_presigned_url = None
    if video.minio_input_link:
        input_presigned_url = minio_client.get_presigned_url(video.minio_input_link)
    
    # Generate presigned URLs for output segments
    for segment in video.segments:
        if segment.get('minio_output_link'):
            segment['presigned_url'] = minio_client.get_presigned_url(segment['minio_output_link'])
    
    from django.contrib.auth.models import User
    context = {
        'video': video,
        'users': User.objects.all(),
        'prompt_templates': PromptTemplate.objects.filter(is_active=True),
        'input_presigned_url': input_presigned_url,
        'segments_json': json.dumps(video.segments),
    }
    return render(request, 'videos/video_form.html', context)


@require_http_methods(["POST"])
def video_delete(request, pk):
    """Xóa video profile"""
    video = get_object_or_404(VideoProfile, pk=pk)
    title = video.title
    
    try:
        # Optionally delete files from Minio
        # minio_client = MinioClient()
        # if video.minio_input_link:
        #     minio_client.delete_file(video.minio_input_link)
        # for segment in video.segments:
        #     if segment.get('minio_output_link'):
        #         minio_client.delete_file(segment['minio_output_link'])
        
        video.delete()
        messages.success(request, f'Đã xóa video profile: {title}')
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        messages.error(request, f'Lỗi khi xóa video: {str(e)}')
    
    return redirect('video_list')


# ============ PROMPT TEMPLATE VIEWS ============

def prompt_list(request):
    """Màn hình Quản lý prompt - Danh sách tất cả prompts"""
    prompts = PromptTemplate.objects.all()
    
    # Filter by category if provided
    category_filter = request.GET.get('category')
    if category_filter:
        prompts = prompts.filter(category=category_filter)
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active:
        prompts = prompts.filter(is_active=is_active == 'true')
    
    context = {
        'prompts': prompts,
        'category_choices': PromptTemplate.CATEGORY_CHOICES,
    }
    return render(request, 'videos/prompt_list.html', context)


def prompt_detail(request, pk):
    """Xem chi tiết prompt - redirect đến prompt_edit"""
    return redirect('prompt_edit', pk=pk)


def prompt_create(request):
    """Màn hình Khởi tạo prompt template"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category = request.POST.get('category')
            template_content = request.POST.get('template_content')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate
            if not name or not category or not template_content:
                messages.error(request, 'Tên, thể loại và nội dung template là bắt buộc')
                return redirect('prompt_create')
            
            # Create prompt
            prompt = PromptTemplate.objects.create(
                name=name,
                category=category,
                template_content=template_content,
                description=description,
                is_active=is_active
            )
            
            messages.success(request, f'Đã tạo prompt template: {prompt.name}')
            return redirect('prompt_edit', pk=prompt.id)
            
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            messages.error(request, f'Lỗi khi tạo prompt: {str(e)}')
            return redirect('prompt_create')
    
    # GET request
    context = {
        'category_choices': PromptTemplate.CATEGORY_CHOICES,
    }
    return render(request, 'videos/prompt_form.html', context)


def prompt_edit(request, pk):
    """Màn hình Sửa prompt template"""
    prompt = get_object_or_404(PromptTemplate, pk=pk)
    
    if request.method == 'POST':
        try:
            prompt.name = request.POST.get('name', prompt.name)
            prompt.category = request.POST.get('category', prompt.category)
            prompt.template_content = request.POST.get('template_content', prompt.template_content)
            prompt.description = request.POST.get('description', '')
            prompt.is_active = request.POST.get('is_active') == 'on'
            
            prompt.save()
            messages.success(request, 'Đã cập nhật prompt template')
            return redirect('prompt_edit', pk=pk)
            
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            messages.error(request, f'Lỗi khi cập nhật prompt: {str(e)}')
    
    context = {
        'prompt': prompt,
        'category_choices': PromptTemplate.CATEGORY_CHOICES,
    }
    return render(request, 'videos/prompt_form.html', context)


@require_http_methods(["POST"])
def prompt_delete(request, pk):
    """Xóa prompt template"""
    prompt = get_object_or_404(PromptTemplate, pk=pk)
    name = prompt.name
    
    try:
        prompt.delete()
        messages.success(request, f'Đã xóa prompt template: {name}')
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        messages.error(request, f'Lỗi khi xóa prompt: {str(e)}')
    
    return redirect('prompt_list')


# ============ AJAX/API VIEWS ============

@require_http_methods(["POST"])
def generate_prompt(request):
    """Generate prompt từ template và youtube link (AJAX)"""
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        youtube_link = data.get('youtube_link', '')
        
        if not template_id:
            return JsonResponse({'error': 'Template ID is required'}, status=400)
        
        template = get_object_or_404(PromptTemplate, pk=template_id)
        generated_prompt = generate_prompt_from_template(template, youtube_link)
        
        return JsonResponse({
            'success': True,
            'prompt': generated_prompt
        })
        
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def process_video_segment(request):
    """Xử lý cắt video segment (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        segment_index = data.get('segment_index')
        start_time = float(data.get('start_time', 0))
        end_time = float(data.get('end_time', 0))
        
        # Validate
        if not video_id or segment_index is None:
            return JsonResponse({'error': 'Video ID and segment index are required'}, status=400)
        
        if start_time >= end_time:
            return JsonResponse({'error': 'Start time must be less than end time'}, status=400)
        
        video = get_object_or_404(VideoProfile, pk=video_id)
        
        if not video.minio_input_link:
            return JsonResponse({'error': 'No input video link'}, status=400)
        
        # Process segment
        video.status = 'processing'
        video.save()
        
        processor = VideoProcessor()
        output_link = processor.process_segment(
            video.minio_input_link,
            start_time,
            end_time,
            segment_index
        )
        
        if not output_link:
            video.status = 'failed'
            video.save()
            return JsonResponse({'error': 'Failed to process video segment'}, status=500)
        
        # Update segment
        if segment_index < len(video.segments):
            video.segments[segment_index]['minio_output_link'] = output_link
            video.segments[segment_index]['start_time'] = start_time
            video.segments[segment_index]['end_time'] = end_time
        
        # Update status
        if video.get_processed_segments() == video.get_total_segments():
            video.status = 'completed'
        
        video.save()
        
        # Generate presigned URL for preview
        minio_client = MinioClient()
        presigned_url = minio_client.get_presigned_url(output_link)
        
        return JsonResponse({
            'success': True,
            'output_link': output_link,
            'presigned_url': presigned_url,
            'progress': video.get_progress_percentage()
        })
        
    except Exception as e:
        logger.error(f"Error processing video segment: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def add_segment(request):
    """Thêm segment mới vào video (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        prompt = data.get('prompt', '')
        result = data.get('result', '')
        
        video = get_object_or_404(VideoProfile, pk=video_id)
        
        new_segment = {
            'prompt': prompt,
            'result': result,
            'minio_output_link': None,
            'start_time': None,
            'end_time': None
        }
        
        video.segments.append(new_segment)
        video.save()
        
        return JsonResponse({
            'success': True,
            'segment_index': len(video.segments) - 1,
            'segment': new_segment
        })
        
    except Exception as e:
        logger.error(f"Error adding segment: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def delete_segment(request):
    """Xóa segment khỏi video (AJAX)"""
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        segment_index = data.get('segment_index')
        
        video = get_object_or_404(VideoProfile, pk=video_id)
        
        if 0 <= segment_index < len(video.segments):
            deleted_segment = video.segments.pop(segment_index)
            video.save()
            
            return JsonResponse({
                'success': True,
                'deleted_segment': deleted_segment
            })
        else:
            return JsonResponse({'error': 'Invalid segment index'}, status=400)
        
    except Exception as e:
        logger.error(f"Error deleting segment: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def home(request):
    """Home page - redirect to video list"""
    return redirect('video_list')