#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import configparser


class Config(object):
    """读取配置文件"""
    def __init__(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read('config.conf', encoding='utf-8')

    def getConfig(self, key):
        return self.cfg.get('default', key, fallback=None)

    def __del__(self):
        pass
