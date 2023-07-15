from django.urls import path
from . import views
urlpatterns = [
    path('',views.index,name = 'index'),
    path('check/',views.check_username,name = 'check_username'),
    path('login/',views.user_login,name = 'login'),
    path('register/',views.register,name='register')
]