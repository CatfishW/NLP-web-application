from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib.auth.hashers import make_password,check_password
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from stt_realtime_api_helper import stt_api_get_result
import os
# Create your views here.
# 讯飞开放平台相关信息
APPID = '5f14f0a0'  # 到控制台语音听写页面获取
APIKey = '617fc1020aebdd37d3b48adb8bdaf26a'  # 到控制台语音听写页面获取
APISecret = '1df0512e0ddbffe279927aec1dbdf82d'  # 注意不要与APIkey写反
text_file = './data.txt'  # 用于存储听写后的文本
def index(request):
    return render(request, 'home.html')
@csrf_exempt
def user_login(request):
    if request.session.get('is_login', None):  # 不允许重复登录
        return redirect('/')
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
                request.session['is_login'] = True  # 往session字典内写入用户状态和数据
                request.session['email'] = email
                return redirect("/")

            else:
                # 登录失败后的逻辑，显示错误信息
                print('test')
                return JsonResponse({'error':True})
        except:
            print('error')
            return JsonResponse({'error':True})
    else:
        return render(request,'loginAndregister.html')

def logout(request):
    if not request.session.get('is_login', None):
        # 如果本来就未登录，也就没有登出一说
        return redirect("/")
    request.session.flush()

    return redirect("/")

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
@csrf_exempt
def speech_to_text(request):
    if request.method == 'GET':
        return render(request,'speech_to_text.html')
    uploaded_file = request.FILES['file']
    file_path = os.path.join('recognition_result', uploaded_file.name)  # 替换为目标路径
    with open(file_path, 'wb') as destination_file:
        for chunk in uploaded_file.chunks():
            destination_file.write(chunk)
    stt_api_get_result(APPID, APIKey, APISecret, file_path)  # 调用听写模块并将结果保存到txt文件中
    with open(text_file, 'r') as f:  # 读取txt文件内容获取听写结果
        text = f.readlines()
    result = {'result':''.join(text)}
    return render(request,'speech_to_text.html',result)





   


