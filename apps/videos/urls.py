# apps/videos/urls.py
from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Video Profile URLs
    path('videos/', views.VideoProfileListView.as_view(), name='video_list'),
    path('videos/create/', views.VideoProfileCreateView.as_view(), name='video_create'),
    path('videos/<uuid:pk>/', views.VideoProfileDetailView.as_view(), name='video_detail'),
    path('videos/<uuid:pk>/update/', views.VideoProfileUpdateView.as_view(), name='video_update'),
    path('videos/<uuid:pk>/delete/', views.VideoProfileDeleteView.as_view(), name='video_delete'),
    
    # Video Processing URLs
    path('videos/<uuid:pk>/process/', views.VideoProcessingView.as_view(), name='video_process'),
    
    # Prompt Template URLs
    path('prompts/', views.PromptTemplateListView.as_view(), name='prompt_list'),
    path('prompts/create/', views.PromptTemplateCreateView.as_view(), name='prompt_create'),
    path('prompts/<uuid:pk>/', views.PromptTemplateDetailView.as_view(), name='prompt_detail'),
    path('prompts/<uuid:pk>/update/', views.PromptTemplateUpdateView.as_view(), name='prompt_update'),
    path('prompts/<uuid:pk>/delete/', views.PromptTemplateDeleteView.as_view(), name='prompt_delete'),
    
    # AJAX/API URLs
    path('api/youtube-preview/', views.YoutubePreviewView.as_view(), name='youtube_preview'),
    path('api/generate-prompt/', views.PromptGenerateView.as_view(), name='generate_prompt'),
]