#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import queue
from threading import Thread
from testing import Testing


class Scheduler(object):
    def __init__(self):
        self.testing = Testing()
        self.test_task = queue.Queue()  # 创建队列

        t = Thread(target=self.worker)
        t.start()

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
