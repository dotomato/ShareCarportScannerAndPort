# !/usr/bin/env python
# coding=utf-8

import RPi.GPIO as GPIO
import time
import os
from flask import Flask, make_response
import requests
import json
import threading

app = Flask(__name__)

SELF_ID = '111'  # 要对应二维码的id
GPIO_IN_List = [23]  # 红外端口列表,有6个，就填6个
SERVER_IP = 'xxx.xxx.xxx.xxx:5001'

GPIO.setmode(GPIO.BCM)
led = 21
sg90 = 20
GPIO.setwarnings(False)
for gpio in GPIO_IN_List:
    GPIO.setup(gpio, GPIO.IN)
GPIO.setup(led, GPIO.OUT)
GPIO.setup(sg90, GPIO.OUT)
p = GPIO.PWM(sg90, 50)
p.start(0)
p.ChangeDutyCycle(7.5)

PORT_OPEN = 0  # 阻栏杆放下的时候为OPEN（可以让车进去）
PORT_CLOSE = 1  # 阻栏杆放下的时候为CLOSE（不可以让车进去）
status = PORT_OPEN  # 初始的状态为OPEN


@app.route('/open', methods=['GET'])
def open():
    GPIO.output(led, GPIO.LOW)
    p.ChangeDutyCycle(7.5)
    time.sleep(5)   # 暂停5秒，防止阻栏杆放下后由于车还在上面又立刻升起
    global status
    status = PORT_OPEN
    return make_response('open', 200)


@app.route('/close', methods=['GET'])
def close():
    GPIO.output(led, GPIO.HIGH)
    p.ChangeDutyCycle(2.5)
    global status
    status = PORT_CLOSE
    return make_response('close', 200)


def send_enter_car_signal():
    payload = json.dumps({'type': 'port', 'id': SELF_ID})
    url = 'http://%s/api/v0.01/enter_car' % SERVER_IP
    requests.post(url, payload)


def send_comfir_car_signal():
    payload = json.dumps({'type': 'port', 'id': SELF_ID})
    url = 'http://%s/api/v0.01/comfir_car' % SERVER_IP
    requests.post(url, payload)


def check_ir():
    while True:
        k = 0
        for gpio in GPIO_IN_List:  # 计算有多个少红外检测到距离为0
            if GPIO.input(gpio) == 0:
                k += 1
        if k >= 5 and status == PORT_OPEN:  # 如果有大于等于5个红外检测到距离为0（也就是5个或者6个都符合），并且当前状态为OPEN
            send_enter_car_signal()
            time.sleep(15)
            k2 = 0
            for gpio in GPIO_IN_List:  # 计算有多个少红外检测到距离为0
                if GPIO.input(gpio) == 0:
                    k2 += 1
            if k>= 5:
                send_comfir_car_signal()
        time.sleep(1)  # 每秒检测一次


if __name__ == '__main__':
    threading.Thread(target=check_ir).start()
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)

