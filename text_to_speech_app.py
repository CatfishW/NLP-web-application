#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
from tts_api_helper import tts_api_get_result  # 导入 tts_api_helper.py中调用讯飞开放平台接口的语音合成模块
from flask import Flask, render_template, request  # 导入flask web框架依赖的模块

# 讯飞开放平台相关信息
APPID = '5f14f0a0'  # 到控制台语音合成页面获取
APIKey = '617fc1020aebdd37d3b48adb8bdaf26a'  # 到控制台语音合成页面获取
APISecret = '1df0512e0ddbffe279927aec1dbdf82d'  # 注意不要与APIkey写反

app = Flask(__name__)  # 创建程序实例
@app.route('/', methods=['GET', 'POST'])
def text_to_speech():
    if request.method == 'GET':
        return render_template('home.html', result={})

    TEXT = request.form['TEXT']  # 获取页面输入的文本
    if len(TEXT) == 0:
        return render_template('home.html', result={})

    # 此处时间用于音频文件路径的定义，便于页面请求音频文件
    nowtime = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    tts_file = './static/' + nowtime + r'text_to_speech.mp3'  # 存储合成语音文件
    tts_file_post = nowtime + r'text_to_speech.mp3'  # 用于页面请求音频文件地址

    tts_api_get_result(APPID, APIKey, APISecret, TEXT, tts_file)  # 调用合成模块并将结果保存到音频文件中

    return render_template('home.html', result=tts_file_post)  # 页面请求音频文件


if __name__ == '__main__':
    app.run(debug=True)
