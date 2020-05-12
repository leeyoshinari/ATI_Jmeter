#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import os
import time
import logging.handlers
from config import Config


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

# file_handler = logging.handlers.RotatingFileHandler(filename=log_name, maxBytes=10*1024*1024, backupCount=7)
file_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
