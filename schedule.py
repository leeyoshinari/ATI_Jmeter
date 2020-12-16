#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import json
import queue
from concurrent.futures import ThreadPoolExecutor
from testing import Testing
from logger import logger, cfg


class Scheduler(object):
    def __init__(self):
        self.testing = Testing()
        self.thread_pool_size = max(1, int(cfg.getConfig('thread_pool')))
        self.test_task = queue.Queue()  # 创建队列
        self.executor = ThreadPoolExecutor(self.thread_pool_size)    # 创建线程池

        self.run()

    @property
    def task(self):
        return None

    @task.setter
    def task(self, value):
        self.test_task.put((self.testing.run, value))

    def worker(self):
        """
        从队列中获取测试任务，并开始执行
        :return: 
        """
        while True:
            func, param = self.test_task.get()
            func(param)
            self.test_task.task_done()

    def run(self):
        """
        启动线程池执行测试任务
        :return:
        """
        for i in range(self.thread_pool_size):
            self.executor.submit(self.worker)


def replace_email(src, new_dict, dst):
    old_dict = json.load(open(src, 'r', encoding='utf-8'))
    for k, v in new_dict.items():
        old_dict.update({k: v})

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(json.dumps(old_dict))


def replace_config(src, new_dict, dst):
    old_dict = {}
    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        k_v = line.split('//')[0].split('=')
        old_dict.update({k_v[0].strip(): k_v[1].strip()})

    for k, v in new_dict.items():
        old_dict.update({k: v})

    lines = [f'{k}={v}\n' for k, v in old_dict.items()]
    with open(dst, 'w', encoding='utf-8') as f:
            f.writelines(lines)
