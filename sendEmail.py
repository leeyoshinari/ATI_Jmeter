#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import json
import smtplib
import shutil
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from logger import logger, cfg


def sendMsg(html, paths, failure_num=1, is_path=True, is_send=True):
    """
    发送邮件
    :param html: 邮件正文用到的html文件路径，或者html
    :param paths:
    :param failure_num: 失败的用例数
    :param is_path: bool，True表示html是一个路径，False表示html是html
    :param is_send: bool，是否发邮件，仅用于第一次发送失败后，再次发送
    :return: 
    """
    flag = 0
    is_email = int(cfg.getConfig('is_email'))
    if is_email:
        if is_email == 1:
            flag = 1
        if is_email == 2:
            if failure_num > 0:
                flag = 1
            else:
                logger.info('所有用例执行成功，不发送邮件，已跳过。')
        if is_email == 3:
            if failure_num == 0:
                flag = 1
            else:
                logger.info('有执行失败的用例，不发送邮件，已跳过。')
    else:
        logger.info('设置为不自动发送邮件，已跳过。')

    if flag:
        try:
            if paths["method"] == "GET":
                shutil.copy(paths["email_file"], paths["new_email_file"])
            else:
                if paths["post_data"].get('email'):
                    replace_email(paths["email_file"], paths["post_data"]['email'], paths["new_email_file"])

            email_dict = json.load(open(paths["new_email_file"], 'r', encoding='utf-8'))
            subject = email_dict['subject']
            send_to = email_dict['receiveEmail']
            receive_name = email_dict['receiveName']
            logger.info('开始发送邮件，收件人{}'.format(send_to))
            message = MIMEMultipart()
            message['From'] = Header(cfg.getConfig('sender_name'))      # 发件人名字
            message['To'] = Header(receive_name)    # 收件人名字
            message['Subject'] = Header(subject, 'utf-8')   # 邮件主题

            if is_path:
                with open(html, 'r', encoding='utf-8') as f:
                    fail_case = f.read()
            else:
                fail_case = html

            email_text = MIMEText(fail_case, 'html', 'utf-8')
            message.attach(email_text)  # 添加邮件正文

            try:
                server = smtplib.SMTP_SSL(cfg.getConfig('smtp'), 465)
            except Exception as err:
                logger.error(err)
                server = smtplib.SMTP(cfg.getConfig('smtp'), 25)

            server.login(cfg.getConfig('sender_email'), '123456')  # 登陆邮箱
            server.sendmail(cfg.getConfig('sender_email'), send_to.split(','), message.as_string())  # 发送邮件
            server.quit()
            del fail_case, email_text, message, server
            logger.info('邮件发送成功')
        except Exception as err:
            logger.error(err)
            if is_send:
                sendMsg(html, paths, is_path=is_path, is_send=False)   # 发送失败后，重发一次


def replace_email(src, new_dict, dst):
    old_dict = json.load(open(src, 'r', encoding='utf-8'))
    for k, v in new_dict.items():
        old_dict.update({k: v})

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(json.dumps(old_dict))
