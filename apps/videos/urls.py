from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    # Video Profile URLs
    path('', views.video_list, name='video_list'),
    path('create/', views.video_create, name='video_create'),
    path('<uuid:pk>/', views.video_detail, name='video_detail'),
    path('<uuid:pk>/edit/', views.video_edit, name='video_edit'),
    path('<uuid:pk>/delete/', views.video_delete, name='video_delete'),
    # path('<uuid:pk>/process/', views.video_process, name='video_process'),
    path('<uuid:pk>/preview/', views.video_preview, name='video_preview'),
    
    # Prompt Template URLs
    path('prompts/', views.prompt_list, name='prompt_list'),
    path('prompts/create/', views.prompt_create, name='prompt_create'),
    path('prompts/<int:pk>/', views.prompt_detail, name='prompt_detail'),
    path('prompts/<int:pk>/edit/', views.prompt_edit, name='prompt_edit'),
    path('prompts/<int:pk>/delete/', views.prompt_delete, name='prompt_delete'),
    
    # Prompt Generator URL
    path('prompts/generate/', views.prompt_generate, name='prompt_generate'),
    
    # Video Processing URLs
    path('<uuid:pk>/cut/', views.video_cut, name='video_cut'),
    path('<uuid:pk>/download/', views.video_download, name='video_download'),
]