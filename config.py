#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import configparser


class Config(object):
    """读取配置文件"""
    def __init__(self):
        self.cfg = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.conf')
        self.cfg.read(config_path, encoding='utf-8')

    def getConfig(self, key):
        return self.cfg.get('default', key)

    def __del__(self):
        pass
