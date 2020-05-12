#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari
import os
import glob
import json
import asyncio
from aiohttp import web
from schedule import Scheduler
from sendEmail import sendMsg
from logger import logger, cfg


schedule = Scheduler()
report_path = cfg.getConfig('report_path')
IP = cfg.getConfig('host')
PORT = cfg.getConfig('port')


async def run(request):
    """
    run接口，get请求，把测试任务放入队列中
    :param request:
    :return:
    """
    system_name = request.match_info['name']
    case_path = os.path.join(cfg.getConfig('case_path'), system_name)
    record_path = os.path.join(case_path, cfg.getConfig('record_name'))
    build_file = os.path.join(cfg.getConfig('case_path'), system_name, 'build.xml')
    email_file = glob.glob(os.path.join(case_path, 'email_*.txt'))
    if os.path.exists(case_path):
        if len(email_file) == 0:
            return web.Response(body=json.dumps({'code': 0, 'message': '没有设置收件人邮箱地址的txt文件，测试任务执行失败', 'data': None}, ensure_ascii=False))
        elif len(email_file) > 1:
            return web.Response(body=json.dumps({'code': 0, 'message': '应该只有一个收件人邮箱地址的txt文件，但是找到了多个，测试任务执行失败', 'data': None}, ensure_ascii=False))

        if not os.path.exists(record_path):
            f = open(record_path, 'a')
            f.close()

        if os.path.exists(build_file):
            schedule.task = [case_path, email_file[0]]
            return web.Response(body=json.dumps({'code': 1, 'message': '操作成功，测试任务正在准备执行', 'data': None}, ensure_ascii=False))
        else:
            return web.Response(body=json.dumps({'code': 0, 'message': 'build.xml文件不存在，测试任务执行失败', 'data': None}, ensure_ascii=False))
    else:
        return web.Response(body=json.dumps({
            'code': 0, 'message': '未找到与系统名称对应的脚本，请确认系统名称是否正确，脚本是否存在！', 'data': None}, ensure_ascii=False))


async def sendEmail(request):
    """
    get请求，用于发送邮件，用于客户端异常时发送邮件提醒
    :param request:
    :return:
    """
    name = request.match_info['name']
    port = request.match_info['port']
    email_file = glob.glob(os.path.join(cfg.getConfig('case_path'), name, 'email_*.txt'))
    if len(email_file) == 0:
        return web.Response(body=json.dumps({'code': 0, 'message': '没有设置收件人邮箱地址的txt文件，测试任务执行失败', 'data': None}, ensure_ascii=False))
    elif len(email_file) > 1:
        return web.Response(body=json.dumps({'code': 0, 'message': '应该只有一个收件人邮箱地址的txt文件，但是找到了多个，测试任务执行失败', 'data': None}, ensure_ascii=False))

    html = f'<html><body>' \
           f'<h3>异常提醒：{name}的接口自动化测试环境对应的{port}端口已经停了，请及时重启或更换端口！</h3>' \
           f'<p style="color:blue;">此邮件自动发出，请勿回复。</p></body></html>'
    try:
        sendMsg(html, email_file[0], is_path=False)
        return web.Response(body=json.dumps({'code': 1, 'message': '邮件提醒发送成功', 'data': None}, ensure_ascii=False))
    except Exception as err:
        return web.Response(body=json.dumps({'code': 0, 'message': err, 'data': None}, ensure_ascii=False))


async def main():
    app = web.Application()
    app.router.add_static('/testReport/', path=report_path)

    app.router.add_route('GET', '/run/{name}', run)
    app.router.add_route('GET', '/sendEmail/{name}/{port}', sendEmail)

    app_runner = web.AppRunner(app)
    await app_runner.setup()
    site = web.TCPSite(app_runner, IP, int(PORT))
    await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
