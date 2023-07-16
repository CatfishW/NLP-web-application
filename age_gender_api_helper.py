#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 性别年龄识别WebAPI 接口：即机器对说话者的年龄大小以及性别属性进行分析，可以通过收到的音频数据判定发音人的性别（男，女）及年龄范围（小孩，中年，老人），对语音内容和语种不做限制。
# 该语音能力是通过Websocket API的方式给开发者提供一个通用的接口。Websocket API具备流式传输能力，适用于需要流式数据传输的AI服务场景，比如边说话边识别。
import datetime
import hashlib
import base64
import hmac
import json
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

# 用于存储年龄和性别信息
age_data = []
gender_data = []


class Ws_Param(object):  # 定义类用于管理 websocket 参数
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile  # 说话人的音频文件

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)
        self.BusinessArgs = {"ent": "igr",  # 引擎类型，目前仅支持igr
                             "aue": "raw",  # 音频格式 raw：支持pcm格式和wav格式
                             "rate": 16000  # 音频采样率 16000/8000
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
        signature_origin += "GET " + "/v2/igr " + "HTTP/1.1"
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
        url = 'wss://ws-api.xfyun.cn/v2/igr'
        # 在请求地址后面加上鉴权相关参数（拼接鉴权参数），生成url
        url = url + '?' + urlencode(v)
        return url


# 收到websocket错误的处理
def on_error(ws, error):  # websocket报错时，就会触发on_error事件
    print("错误信息:", error)


# 收到websocket关闭的处理
def on_close(ws):  # websocket关闭时，就会触发on_close事件
    print("websocket连接关闭")


def data_send(ws, file, commonargs, businessargs):
    frameSize = 5000  # 每一帧的音频大小
    intervel = 0.04  # 发送音频间隔(单位:s)
    status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
    # 业务数据流参数
    data_format = "audio/L16;rate=16000"  # 音频的采样率支持16k和8k, 8k音频：audio/L16;rate=8000
    data_encoding = "raw"  # 音频数据格式, lame：mp3格式  raw：原生音频（支持单声道的pcm,wav）

    with open(file, "rb") as fp:
        while True:
            buf = fp.read(frameSize)
            # 文件结束
            if not buf:
                status = STATUS_LAST_FRAME
            # 第一帧处理
            # 发送第一帧音频，带business 参数
            # appid 必须带上，只需第一帧发送
            if status == STATUS_FIRST_FRAME:
                d = {"common": commonargs,  # 公共参数APPid
                     "business": businessargs,
                     "data": {"status": 0,  # 音频的状态 0 :第一帧音频
                              "format": data_format,
                              "audio": str(base64.b64encode(buf), 'utf-8'),  # 音频内容，采用base64编码
                              "encoding": data_encoding
                              }
                     }
                d = json.dumps(d)  # 将请求数据转化为字符串
                ws.send(d)  # 发送数据
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
    ws.close()  # 关闭websocket


def data_write(message, age_data, gender_data):
    try:
        code = json.loads(message)["code"]  # 返回码，0表示成功，其它表示异常
        sid = json.loads(message)["sid"]  # 本次会话的id，只在握手成功后第一帧请求时返回
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            age_data.append(json.loads(message)["data"]["result"]["age"])
            gender_data.append(json.loads(message)["data"]["result"]["gender"])
    except Exception as e:
        print("接收消息，但解析异常:", e)


def age_gender_api_get_result(APPID, APIKey, APISecret, filename):
    # 实例化websocket参数类
    wsParam = Ws_Param(APPID=APPID,
                       APIKey=APIKey,
                       APISecret=APISecret,
                       AudioFile=filename)
    wsUrl = wsParam.create_url()  # 获取鉴权url

    # 收到websocket消息的处理：把服务端返回的json数据进行解析
    def on_message(ws, message):
        data_write(message, age_data, gender_data)

    # 建立websocket连接,客户端的数据发送给服务端
    def on_open(ws):  # 连接到服务器之后就会触发on_open事件
        def run(*args):
            data_send(ws, wsParam.AudioFile, wsParam.CommonArgs, wsParam.BusinessArgs)
        thread.start_new_thread(run, ())  # 产生新线程

    # 向服务器端发送Websocket协议握手请求
    # 握手成功后，客户端通过Websocket连接同时上传和接收数据。
    # 接收到服务器端的结果全部返回标识后断开Websocket连接
    websocket.enableTrace(False)  # 调试关闭
    ws = websocket.WebSocketApp(wsUrl,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # CERT_NONE 禁用SSL证书验证

    return age_data, gender_data
