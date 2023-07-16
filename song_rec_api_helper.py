#!/usr/bin/env python
# encoding: utf-8
import requests
import base64
import json
import time
import hashlib


class song_rec_get_result(object):
    #  todo：初使化类的属性
    def __init__(self, url, APPID, APIKey, file):
        # 给出讯飞开放平台相关信息
        self.url = url
        self.APPID = APPID
        self.APIKey = APIKey
        # 设置业务参数
        self.file = file

    def call_url(self):
        # todo：step1 构造请求体 Http Request Body
        # 获取文件名
        # 将哼唱音频文件数据写入到Http Request请求体中
        with open(self.file, 'rb') as f:
            wavfile = f.read()
        body_data = {'audio': str(base64.b64encode(wavfile), 'utf-8')}

        # todo：step2 构造请求头
        # 由于音频数据写入到请求体中，因此在param参数中不需要设置audio_url参数（为空）
        param = {'engine_type': 'afs',  # 引擎类型，可选值：afs（哼唱)
                 'aue': 'raw',  # 音频编码，可选值：raw（pcm、wav格式）、aac，默认raw
                 'sample_rate': '16000',  # 采样率，可选值：8000、16000，默认16000
                 'audio_url': ""  # 哼唱音频存放地址url
                 }
        base64_param = base64.urlsafe_b64encode(json.dumps(param).encode('utf-8'))
        xx_param = str(base64_param, 'utf-8')  # 利用Base64编码生成字符串
        x_time = str(int(time.time()))  # 当前UTC时间戳从1970年1月1日0点0 分0 秒开始到现在的秒数
        # 令牌，计算方法：MD5(APIKey + X-CurTime + X-Param)，三个值拼接的字符串，进行MD5哈希计算（32位小写）
        m2 = hashlib.md5()
        m2.update((self.APIKey + x_time + xx_param).encode('utf-8'))
        x_checksum = m2.hexdigest()
        # 配置请求头参数
        header = {
            "X-CurTime": x_time,
            "X-Param": base64_param,
            "X-Appid": self.APPID,
            "X-CheckSum": x_checksum,
        }

        # todo：step3 向服务器端发送请求，接收服务器端的返回结果
        res = requests.post(self.url, headers=header, data=body_data)

        # todo：对返回结果进行解析
        result = json.loads(res.content)['data']
        # print('识别到的歌曲（按匹配概率降序）如下：')
        # for i in range(len(result)):
        #     print('第 %d 首歌为：%s，歌手为：%s, 开始时间为：%d，结束时间为： %d'
        #           % (i+1, result[i]['song'], result[i]['singer'], result[i]['start_time'], result[i]['end_time']))
        return result
