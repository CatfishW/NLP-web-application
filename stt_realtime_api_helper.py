#!/usr/bin/python
# -*- coding: UTF-8 -*-
#  语音听写（即时语音识别）流式接口：
#  用于1分钟内的即时语音转文字技术，支持实时返回识别结果，达到一边上传音频一边获得识别文本的效果。
import datetime
import hashlib
import base64
import hmac
import json
import os
import time
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import websocket
import ssl
import _thread as thread

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识
text_file = './data.txt'  # 用于存储听写的文本


class Ws_Param(object):  # 定义类用于管理 websocket 参数
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)
        self.BusinessArgs = {"domain": "iat",  # 应用领域 iat：日常用语
                             "language": "zh_cn",  # 语种 zh_cn：中文（支持简单的英文识别）
                             "accent": "mandarin",  # mandarin：中文普通话
                             "vinfo": 1,  # 返回子句结果对应的起始和结束的端点帧偏移值。端点帧偏移值表示从音频开头起已过去的帧长度。0：关闭（默认值）1：开启
                             "vad_eos": 10000  # 用于设置端点检测的静默时间，单位是毫秒。若音频静默10s则引擎认为音频结束
                             }

    # 生成url，通过在请求地址后面加上鉴权相关参数
    def create_url(self):
        # 参数1：生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 参数2： 生成鉴权authorization参数（包括下面step1、2、3、4、5)
        # step1 拼接signature原始字段的字符串（signature原始字段包括host、date、authorization）
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
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
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 在请求地址后面加上鉴权相关参数（拼接鉴权参数），生成url
        url = url + '?' + urlencode(v)
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理：把服务端返回的json数据进行解析
def on_message(ws, message):
    try:
        code = json.loads(message)["code"]  # 返回码，0表示成功，其它表示异常
        sid = json.loads(message)["sid"]  # 本次会话的id，只在握手成功后第一帧请求时返回
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            with open(text_file, 'a') as f:  # 将听写文字以追加方式写入文本文件中
                f.write(result)
    except Exception as e:
        print("接收消息，但解析异常", e)


# 收到websocket错误的处理
def on_error(ws, error):  # websocket报错时，就会触发on_error事件
    print("错误信息:", error)


def on_close(ws):  # websocket关闭时，就会触发on_close事件
    print("websocket连接关闭")


# 用于处理音频数据发送
def data_send(ws, file, commonargs, Businessargs):
    frameSize = 8000  # 每一帧的音频大小
    intervel = 0.04  # 发送音频间隔(单位:s)
    status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

    # 业务数据流参数
    data_format = "audio/L16;rate=16000"  # 音频的采样率支持16k和8k, 8k音频：audio/L16;rate=8000
    data_encoding = "lame"  # 音频数据格式, lame：mp3格式  raw：原生音频（支持单声道的pcm）

    with open(file, "rb") as fp:
        while True:
            buf = fp.read(frameSize)
            # 文件结束
            if not buf:
                status = STATUS_LAST_FRAME
            # 第一帧处理
            # 发送第一帧音频，带business 参数，appid必须带上，只需第一帧发送
            if status == STATUS_FIRST_FRAME:
                d = {"common": commonargs,  # 公共参数APPid
                     "business": Businessargs,
                     "data": {"status": 0,  # 音频的状态 0 :第一帧音频
                              "format": data_format,
                              "audio": str(base64.b64encode(buf), 'utf-8'),  # 音频内容，采用base64编码
                              "encoding": data_encoding
                              }
                     }
                d = json.dumps(d)  # 将请求数据转化为字符串
                ws.send(d)  # 发送数据
                if os.path.exists(text_file):  # 将已存在的文本文件删除，只在第一帧处理
                    os.remove(text_file)
                status = STATUS_CONTINUE_FRAME

            # 中间帧处理
            elif status == STATUS_CONTINUE_FRAME:
                d = {"data": {"status": 1,  # 音频的状态 1 :中间的音频
                              "format": data_format,
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": data_encoding
                              }
                     }
                ws.send(json.dumps(d))

            # 最后一帧处理
            elif status == STATUS_LAST_FRAME:
                d = {"data": {"status": 2,  # 音频的状态 2 :最后一帧音频，最后一帧必须要发送
                              "format": data_format,
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": data_encoding
                              }
                     }
                ws.send(json.dumps(d))
                time.sleep(1)
                break
            # 模拟音频采样间隔
            time.sleep(intervel)
    ws.close()


def stt_api_get_result(APPID, APIKey, APISecret, filename):
    # 实例化websocket参数类
    wsParam = Ws_Param(APPID=APPID,
                       APIKey=APIKey,
                       APISecret=APISecret,
                       AudioFile=filename)
    wsUrl = wsParam.create_url()  # 获取鉴权url

    def on_open(ws):  # 连接到服务器之后就会触发on_open事件
        def run(*args):
            data_send(ws, wsParam.AudioFile, wsParam.CommonArgs, wsParam.BusinessArgs)
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
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # CERT_NONE 禁用SSL证书验证，避免出现验证错误的情况
