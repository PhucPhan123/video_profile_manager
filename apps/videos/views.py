from django.shortcuts import render, redirect, get_object_or_404
from .models import VideoProfile, PromptTemplate
from django.http import JsonResponse

# --- QUẢN LÝ PROMPT ---
def prompt_list(request):
    prompts = PromptTemplate.objects.all()
    return render(request, 'videos/prompt_list.html', {'prompts': prompts})

def prompt_create_or_edit(request, pk=None):
    prompt = get_object_or_404(PromptTemplate, pk=pk) if pk else None
    if request.method == "POST":
        genre = request.POST.get('genre')
        template = request.POST.get('template')
        if prompt:
            prompt.genre = genre
            prompt.template_text = template
            prompt.save()
        else:
            PromptTemplate.objects.create(genre=genre, template_text=template)
        return redirect('prompt_list')
    return render(request, 'videos/prompt_form.html', {'prompt': prompt})

# --- QUẢN LÝ VIDEO PROFILE ---
def video_list(request):
    videos = VideoProfile.objects.all()
    return render(request, 'videos/video_list.html', {'videos': videos})

def video_create_or_edit(request, pk=None):
    video = get_object_or_404(VideoProfile, pk=pk) if pk else None
    prompts = PromptTemplate.objects.all()
    
    if request.method == "POST":
        # Logic save thông tin cơ bản
        yt_link = request.POST.get('youtube_link')
        input_path = request.POST.get('minio_input_path')
        user = request.POST.get('assigned_user')
        
        if video:
            video.youtube_link = yt_link
            video.minio_input_path = input_path
            video.assigned_user = user
            video.save()
        else:
            video = VideoProfile.objects.create(
                youtube_link=yt_link, 
                minio_input_path=input_path, 
                assigned_user=user
            )
        return redirect('video_list')
        
    return render(request, 'videos/video_form.html', {'video': video, 'prompts': prompts})

def delete_video(request, pk):
    video = get_object_or_404(VideoProfile, pk=pk)
    video.delete()
    return redirect('video_list')

def generate_video_cut(request, pk):
    if request.method == "POST":
        video_profile = get_object_or_404(VideoProfile, pk=pk)
        
        # 1. Lấy thông tin từ request (ví dụ cắt từ giây thứ 10 đến 20)
        start_t = int(request.POST.get('start_time', 0))
        end_t = int(request.POST.get('end_time', 10))
        prompt_text = request.POST.get('prompt', 'Default Prompt')
        
        # 2. Đường dẫn tạm thời trên server (WSL/Docker container)
        temp_input = f"/tmp/in_{video_profile.id}.mp4"
        temp_output = f"/tmp/out_{uuid.uuid4()}.mp4"
        
        try:
            # 3. Download file gốc từ Minio về server để MoviePy xử lý
            # Giả sử link minio_input_path là tên object trong bucket
            minio_client.fget_object(
                settings.MINIO_BUCKET_NAME, 
                video_profile.minio_input_path, 
                temp_input
            )

            # 4. Thực hiện cắt video bằng MoviePy
            success = cut_video_moviepy(temp_input, temp_output, start_t, end_t)
            
            if success:
                # 5. Upload file đã cắt lên Minio
                object_name = f"outputs/{uuid.uuid4()}.mp4"
                output_url = upload_to_minio(temp_output, object_name)

                # 6. Cập nhật kết quả vào JSONField của Model
                new_object = {
                    "prompt": prompt_text,
                    "result": f"Cắt từ {start_t}s đến {end_t}s",
                    "output_path": output_url # Link truy cập video đầu ra
                }
                video_profile.processing_details.append(new_object)
                video_profile.save()

                return JsonResponse({"status": "success", "data": new_object})
        
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        finally:
            # Xóa file tạm để tránh đầy bộ nhớ container
            if os.path.exists(temp_input): os.remove(temp_input)
            if os.path.exists(temp_output): os.remove(temp_output)