from django.urls import path
from . import views

urlpatterns = [
    path('available-jobs/', views.available_jobs, name='available_jobs'),
    path('post/', views.post_job, name='post_job'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    # client-specific dashboard URLs
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('my-jobs/<int:job_id>/', views.job_applications, name='job_applications'),
    # freelancer-specific page
    path('my-applications/', views.my_applications, name='my_applications'),
    # application status actions for clients
    path('application/<int:app_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:app_id>/reject/', views.reject_application, name='reject_application'),
    # private messaging
    path('messages/<int:job_id>/<int:user_id>/', views.conversation, name='conversation'),
    path('messages/<int:job_id>/<int:user_id>/clear/', views.clear_chat, name='clear_chat'),
    path('my-conversations/', views.my_conversations, name='my_conversations'),
    # job completion for clients
    path('job/<int:job_id>/complete/', views.complete_job, name='complete_job'),
    # alias path from my-jobs listing
    path('my-jobs/<int:job_id>/complete/', views.complete_job, name='complete_job'),
    # allow freelancers to delete their own rejected applications
    path('application/<int:app_id>/delete/', views.delete_application, name='delete_application'),
]
