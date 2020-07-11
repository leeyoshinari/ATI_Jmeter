#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from logger import logger, cfg


def sendMsg(html, receiver_email, is_path=True, is_send=True):
    """
    发送邮件
    :param html: 邮件正文用到的html文件路径，或者html
    :param receiver_email: 收件人邮箱地址的txt文件路径
    :param is_path: bool，True表示html是一个路径，False表示html是html
    :param is_send: bool，是否发邮件，仅用于第一次发送失败后，再次发送
    :return: 
    """
    if int(cfg.getConfig('is_email')):
        try:
            receive_name = re.findall('email_(.*?).txt', receiver_email)[0]     # 提取收件人姓名
            with open(receiver_email, 'r', encoding='utf-8') as f:
                sends = f.readlines()
            subject = sends[0]
            send_to = sends[1]
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
                # server.connect(cfg.getConfig('smtp'))
            except Exception as err:
                logger.error(err)
                server = smtplib.SMTP(cfg.getConfig('smtp'), 25)
                # server.connect(cfg.getConfig('smtp'))

            server.login(cfg.getConfig('sender_email'), '123456')  # 登陆邮箱
            server.sendmail(cfg.getConfig('sender_email'), send_to.split(','), message.as_string())  # 发送邮件
            server.quit()
            del email_text
            del message
            logger.info('邮件发送成功')
        except Exception as err:
            logger.error(err)
            if is_send:
                sendMsg(html, receiver_email, is_path=is_path, is_send=False)   # 发送失败后，重发一次

    else:
        logger.info('设置为不自动发送邮件，已跳过。')
