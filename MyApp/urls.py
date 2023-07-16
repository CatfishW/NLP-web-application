from django.urls import path
from . import views
urlpatterns = [
    path('',views.index,name = 'index'),
    path('check/',views.check_username,name = 'check_username'),
    path('login/',views.user_login,name = 'login'),
    path('register/',views.register,name='register'),
    path('logout/',views.logout,name='logout'),
    path('speech_to_text/',views.speech_to_text,name='speech_to_text'),
    path('voice_generation/',views.voice_generation,name='voice_generation'),
    path('song_recognition/',views.song_recognition,name='song_recognition'),
    path('age_gender_recognition/',views.age_gender_recognition,name='age_gender_recognition')
]