"""marketplace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/stable/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from jobs import views as jobs_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page
    path('', jobs_views.home, name='home'),
    
    # Authentication
    path('signup/', jobs_views.choose_role, name='choose_role'),
    path('signup/client/', jobs_views.signup_client, name='signup_client'),
    path('signup/freelancer/', jobs_views.signup_freelancer, name='signup_freelancer'),
    path('join/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', jobs_views.logout_view, name='logout'),
    
    # Jobs app
    path('', include('jobs.urls')),
]

urlpatterns += staticfiles_urlpatterns()
