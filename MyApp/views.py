from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib.auth.hashers import make_password,check_password
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.
@login_required
def index(request):
    return HttpResponse('home page')
@csrf_exempt
def user_login(request):
    # 1.获取用户提交的数据
    if request.method == 'POST':
        email = request.POST.get('login_email')
        password = request.POST.get('login_password')
        print(request.POST)
        print("login")
        try:
            auth_login = CustomUser.objects.get(email_signup=email)
            checkpassword = check_password(password,auth_login.password_signup)
            print(auth_login.email_signup,auth_login.password_signup,end='\n')
            if auth_login.email_signup == email and checkpassword:
                # 登录成功后重定向到首页
                return HttpResponse('success')
            else:
                # 登录失败后的逻辑，显示错误信息
                print('test')
                return JsonResponse({'error':True})
        except:
            print('error')
            return JsonResponse({'error':True})
    else:
        return render(request,'index.html')
@csrf_exempt
def check_username(request):
    if request.method == 'POST':
        username = request.POST.get('register_username')
        email = request.POST.get('register_email')
        print(request.POST)
        print('checking_username')
        # 检查用户名是否已存在
        if CustomUser.objects.filter(username_signup = username).exists():
            print('用户名已存在')
            return JsonResponse({'duplicate_username': True})
        if CustomUser.objects.filter(email_signup = email).exists():
            print('邮箱已存在')
            return JsonResponse({'duplicate_email': True})
        else:
            print('用户名可用')
            return JsonResponse({'duplicate_username': False,'duplicate_email':False})        
@csrf_exempt
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        # 创建新用户
        User = CustomUser()
        print(CustomUser.objects.filter(username_signup=username))
        try:
            User.username_signup = username
            User.email_signup = email
            User.password_signup = make_password(password)
            User.save()
            return HttpResponse('home page')
        except:
            return HttpResponse('fail')





   


