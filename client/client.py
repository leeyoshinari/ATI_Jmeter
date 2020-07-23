#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari
import os
import time
import json
import configparser
import logging.handlers
import requests


class Config(object):
    def __init__(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read('config.conf', encoding='utf-8')

    def getConfig(self, key):
        return self.cfg.get('default', key, fallback=None)


cfg = Config()
LEVEL = cfg.getConfig('log_level')
log_path = cfg.getConfig('log_path')

if not os.path.exists(log_path):
    os.mkdir(log_path)

log_level = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d] - %(message)s')
logger.setLevel(level=log_level.get(LEVEL))
current_day = time.strftime('%Y-%m-%d')
log_name = os.path.join(log_path, current_day + '.log')

# 日志输出到文件中
file_handler = logging.handlers.RotatingFileHandler(filename=log_name, maxBytes=10*1024*1024, backupCount=7)
# 日志输出到控制台
# file_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def get_ip():
    """
    获取当前服务器IP地址
    :return: IP
    """
    IP = '127.0.0.1'
    try:
        result = os.popen("hostname -I |awk '{print $1}'").readlines()
        logger.debug(result)
        if result:
            IP = result[0].strip()
        else:
            logger.warning('未获取到服务器IP地址')
    except Exception as err:
        logger.error(err)

    return IP


def port_to_pid(port):
    """
    根据端口号查询进程号
    :param port: 端口号
    :return: 进程号
    """
    pid = '0'
    try:
        result = os.popen(f'netstat -nlp|grep {port} |tr -s " "').readlines()
        flag = f':{port}'
        res = [line.strip() for line in result if flag in line]
        logger.debug(res[0])
        p = res[0].split(' ')
        pp = p[3].split(':')[-1]
        if str(port) == pp:
            pid = p[p.index('LISTEN') + 1].split('/')[0]
    except Exception as err:
        logger.error(err)

    return pid


def put_queue(system_name):
    """
    get请求，触发任务执行，将测试任务放入队列中，如果无测试任务执行，则会立即执行，否则会排队
    :param system_name: 系统名
    :return: 
    """
    try:
        url = f"http://{cfg.getConfig('IP')}:{cfg.getConfig('PORT')}/run/{system_name}"
        res = requests.get(url=url)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['code'] == 1:
                logger.info(data['message'])
            else:
                logger.error(data['message'])
                send_email(system_name, '12020', ind=2)
        else:
            logger.error(f'请求异常-{system_name}，状态码为：{res.status_code}')
            send_email(system_name, '12020', ind=2)
    except Exception as err:
        logger.error(err)


def send_email(name, port, ind=1):
    """
    端口停止，发送邮件提醒
    :param name: 系统名
    :param port: 系统端口
    :param ind: 标志，错误类型
    :return:
    """
    IP = get_ip()
    try:
        url = f"http://{cfg.getConfig('IP')}:{cfg.getConfig('PORT')}/sendEmail/{name}/{port}/{ind}/{IP}"
        res = requests.get(url=url)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['code'] == 1:
                logger.info(data['message'])
            else:
                logger.error(data['message'])
        else:
            logger.error(f'请求异常-{name}，状态码为：{res.status_code}')
    except Exception as err:
        logger.error(err)


def main():
    names = cfg.getConfig('server_name')
    ports = cfg.getConfig('server_port')
    interval = cfg.getConfig('interval')
    timing = cfg.getConfig('timing')
    is_start = cfg.getConfig('is_start')

    port = ports.split(',')
    name = names.split(',')

    if len(port) == len(name):
        error_times = [0] * len(port)
        PID = [0] * len(port)
        if interval:  # 如果周期性执行
            interval = int(interval)
            start_time = [time.time()] * len(port)      # 初始化开始时间
            while True:
                for i in range(len(port)):
                    pid = port_to_pid(port[i])
                    if time.time() - start_time[i] > interval:  # 如果满足时间间隔
                        if pid:
                            logger.info(f'{name[i]}环境已开始执行')
                            put_queue(name[i])
                        else:
                            logger.error(f'{name[i]}环境对应的端口{port[i]}已经停止')
                            send_email(name[i], port[i])
                            continue
                        start_time[i] = time.time()

                    if is_start:
                        if pid:
                            if pid != PID[i]:  # 如果服务重启，则立即执行
                                time.sleep(10)
                                PID[i] = pid
                                logger.info(f'{name[i]}环境已开始执行')
                                put_queue(name[i])
                                start_time[i] = time.time()  # 重置周期性执行开始时间
                                error_times[i] = 0
                        else:
                            error_times[i] = error_times[i] + 1
                            logger.error(f'{name[i]}环境对应的端口{port[i]}已经停止')
                            if error_times[i] == 2:
                                send_email(name[i], port[i])

                time.sleep(29)
        elif timing:  # 如果定时执行
            set_hour = int(timing.split(':')[0])
            set_minute = int(timing.split(':')[1])
            while True:
                current_hour = int(time.strftime('%H'))
                if current_hour - set_hour == 0:
                    current_minute = int(time.strftime('%M'))
                    if current_minute - set_minute == 0:  # 如果满足时、分
                        week = int(time.strftime('%w'))
                        if week < 6:    # 工作日运行，非工作日不运行
                            for i in range(len(port)):
                                pid = port_to_pid(port[i])
                                if pid:
                                    logger.info(f'{name[i]}环境已开始执行')
                                    put_queue(name[i])
                                else:
                                    logger.error(f'{name[i]}环境对应的端口{port[i]}已经停止')
                                    send_email(name[i], port[i])

                if is_start:
                    for i in range(len(port)):
                        pid = port_to_pid(port[i])
                        if pid:
                            if pid != PID[i]:  # 如果服务重启，则立即执行
                                time.sleep(10)
                                PID[i] = pid
                                logger.info(f'{name[i]}环境已开始执行')
                                put_queue(name[i])
                                error_times[i] = 0
                        else:
                            error_times[i] = error_times[i] + 1
                            logger.error(f'{name[i]}环境对应的端口{port[i]}已经停止')
                            if error_times[i] == 2:
                                send_email(name[i], port[i])

                time.sleep(29)

        else:
            for i in range(len(port)):
                pid = port_to_pid(port[i])
                if pid:
                    logger.info(f'{name[i]}环境已开始执行')
                    put_queue(name[i])
                else:
                    logger.error(f'{name[i]}环境对应的端口{port[i]}已经停止')
                    send_email(name[i], port[i])
    else:
        raise Exception('系统名称和系统对应的端口配置异常')


if __name__ == '__main__':
    main()
