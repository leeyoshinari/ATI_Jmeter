#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import queue
from concurrent.futures import ThreadPoolExecutor
from testing import Testing
from logger import logger, cfg


class Scheduler(object):
    def __init__(self):
        self.testing = Testing()
        self.thread_pool_size = int(cfg.getConfig('thread_pool'))
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
