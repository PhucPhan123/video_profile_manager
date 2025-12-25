from django.urls import path
from . import views

urlpatterns = [
    # Prompts
    path('prompts/', views.prompt_list, name='prompt_list'),
    path('prompts/create/', views.prompt_create_or_edit, name='prompt_create'),
    path('prompts/edit/<uuid:pk>/', views.prompt_create_or_edit, name='prompt_edit'),
    
    # Videos
    path('videos/', views.video_list, name='video_list'),
    path('videos/create/', views.video_create_or_edit, name='video_create'),
    path('videos/edit/<uuid:pk>/', views.video_create_or_edit, name='video_edit'),
    path('videos/delete/<uuid:pk>/', views.delete_video, name='video_delete'),
    path('videos/generate-cut/<uuid:pk>/', views.generate_video_cut, name='generate_cut')
]