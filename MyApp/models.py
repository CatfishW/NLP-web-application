from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(models.Model):
    username_signup = models.CharField(max_length=150, unique=True)  # 用户名字段，设定为唯一的
    email_signup = models.EmailField(unique=True)  # 邮箱字段，设定为唯一的
    password_signup = models.CharField(max_length=128)  # 密码字段