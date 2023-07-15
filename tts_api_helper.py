#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import hashlib
import base64
import hmac
import json
import os
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import websocket
import ssl
import _thread as thread

# 讯飞开放平台相关信息
APPID = '5f14f0a0'  # 到控制台语音合成页面获取
APIKey = '617fc1020aebdd37d3b48adb8bdaf26a'  # 到控制台语音合成页面获取
APISecret = '1df0512e0ddbffe279927aec1dbdf82d'  # 注意不要与APIkey写反


class Ws_Param(object):  # 定义类用于管理 websocket 参数
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text  # 需语音合成的文本
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)
        self.BusinessArgs = {"aue": "lame",  # 音频编码 lame mps格式
                             "sfl": 1,  # 开启流式返回
                             "auf": "audio/L16;rate=16000",  # 音频采样率
                             "vcn": "aisjinger",  # 发音人   xiaoyan  aisjiuxu aisxping aisjinger aisbabyxu
                             "speed": 50,  # 语速，可选值：[0-100]，默认为50
                             "volume": 50,  # 音量，可选值：[0-100]，默认为50
                             "pitch": 50,  # 音高，可选值：[0-100]，默认为50
                             "bgs": 0,  # 合成音频的背景音 0:无背景音（默认值） 1:有背景音
                             "tte": "utf8"  # 文本编码格式
                             }
        # 对文本数据进行base64编码，数据状态，固定为2
        # 注：由于流式合成的文本只能一次性传输，不支持多次分段传输，此处status必须为2
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}

    # 生成url，通过在请求地址后面加上鉴权相关参数
    def create_url(self):
        # 参数1：生成RFC1123格式的时间戳data
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 参数2： 生成鉴权authorization参数（包括下面step1、2、3、4、5)
        # step1 拼接signature原始字段的字符串（signature原始字段包括host、date、authorization）
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # step2 结合apiSecret对signature_origin，使用hmac-sha256进行加密（签名）
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        # step3 使用base64编码对signature_sha进行编码获得最终的signature_sha
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        # step4 根据以上信息拼接authorization base64编码前（authorization_origin）的字符串
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        # step5 对authorization_origin进行base64编码获得最终的authorization参数
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数1、2及host组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 请求地址
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 在请求地址后面加上鉴权相关参数（拼接鉴权参数），生成url
        url = url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


def on_error(ws, error):  # websocket报错时，就会触发on_error事件
    print("错误信息:", error)


def on_close(ws):  # websocket关闭时，就会触发on_close事件
    print("websocket连接关闭")
    # print('音频文件合成完毕！')


def data_send(ws, file, commonargs, businessargs, data):
    data = {"common": commonargs,
            "business": businessargs,
            "data": data,
            }  # 请求数据
    print("------>开始发送文本数据")
    data = json.dumps(data)  # 将请求数据转化为字符串
    ws.send(data)  # 发送文本数据
    if os.path.exists(file):
        os.remove(file)  # 将已存在的文件删除


def data_write(ws, message, file):
    try:
        message = json.loads(message)
        code = message["code"]  # 返回码，0表示成功，其它表示异常
        sid = message["sid"]
        audio = message["data"]["audio"]  # 合成后的音频片段，采用了base64编码，需要解码
        audio = base64.b64decode(audio)
        status = message["data"]["status"]  # 当前音频流状态，0表示开始合成，1表示合成中，2表示合成结束

        if status == 2:
            print("关闭websocket")
            print('音频文件合成完毕！')
            ws.close()  # 关闭websocket
        if code != 0:
            errMsg = message["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            # 服务端可能会出现一个消息分为多个websocket帧返回给客户端，需要合并这些帧（音频追加使用'ab'）
            with open(file, 'ab') as f:
                f.write(audio)  # 将音频片段写入到音频文件中
    except Exception as e:
        print("接收消息，但解析异常:", e)


def tts_api_get_result(APPID, APIKey, APISecret, TEXT, tts_file):
    # 实例化websocket参数类
    wsParam = Ws_Param(APPID=APPID,
                       APIKey=APIKey,
                       APISecret=APISecret,
                       Text=TEXT)
    wsUrl = wsParam.create_url()  # 获取鉴权url

    #  收到websocket消息的处理：把服务端返回的json数据进行解析，后写到MP3文件
    def on_message(ws, message):  # 服务器有数据更新时，主动推送过来的数据
        data_write(ws, message, tts_file)

    # 建立websocket连接,客户端的数据发送给服务端
    def on_open(ws):  # 连接到服务器之后就会触发on_open事件
        def run(*args):
            data_send(ws, tts_file, wsParam.CommonArgs, wsParam.BusinessArgs, wsParam.Data)
        thread.start_new_thread(run, ())  # 产生新线程

    # 向服务器端发送Websocket协议握手请求
    # 握手成功后，客户端通过Websocket连接同时上传和接收数据
    # 接收到服务器端的结果全部返回标识后断开Websocket连接
    websocket.enableTrace(False)  # 调试关闭
    ws = websocket.WebSocketApp(wsUrl,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    # run_forever是一个无限循环，只要这个websocket连接未断开，这个循环就会一直进行下去
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # CERT_NONE 禁用SSL证书验证
