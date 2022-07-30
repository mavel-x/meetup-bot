"""meetup_bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from meetup import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('meetup/participant/<int:telegram_id>/', views.get_participant, name='get_participant'),
    path('meetup/participant/register/', views.register_participant, name='register_participant'),
    path('meetup/sections/', views.get_sections_list, name='get_sections_list'),
    path('meetup/section/<int:section_id>/', views.get_section, name='get_section'),
    path('meetup/meeting/<int:meeting_id>/', views.get_meeting, name='get_meeting'),
    path('meetup/question/create/', views.create_question, name='create_question'),
    path(
        'meetup/question/<int:question_message_id>/add_answer/',
        views.add_answer_to_question,
        name='add_answer_to_question'
    ),
]
