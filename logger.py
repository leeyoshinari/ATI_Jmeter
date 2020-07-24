#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari

import os
import time
import traceback
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

file_handler = logging.handlers.RotatingFileHandler(filename=log_name, maxBytes=10 * 1024 * 1024, backupCount=7)
# file_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def handle_exception(errors=(Exception,), is_return=False, default_value=None):
    """
    Handle exception, throw an exception, or return a value.
    :param errors: Exception type
    :param is_return: Whether to return 'default_value'. Default False, if exception, don't throw an exception, but return a value.
    :param default_value: If 'is_return' is True, return 'default_value'.
    :return: 'default_value'
    """

    def decorator(func):
        def decorator1(*args, **kwargs):
            if is_return:
                try:
                    return func(*args, **kwargs)
                except errors:
                    logger.error(traceback.format_exc())
                    return default_value
            else:
                try:
                    return func(*args, **kwargs)
                except errors:
                    raise

        return decorator1
    return decorator
