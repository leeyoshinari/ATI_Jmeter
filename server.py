#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari
import os
import glob
import json
import shutil
import asyncio
from aiohttp import web
from schedule import Scheduler, replace_email, replace_config
from sendEmail import sendMsg
from logger import logger, cfg


schedule = Scheduler()
report_path = cfg.getConfig('report_path')
IP = cfg.getConfig('host')
PORT = cfg.getConfig('port')


async def get_list(request):
    """
    获取当前测试用例目录下的系统名，及执行测试任务需要的get请求的url
    """
    case_path = cfg.getConfig('case_path')
    max_num = 0
    for i in os.listdir(case_path):
        if max_num < len(i):
            max_num = len(i)
    dirs = [d+' '*(max_num-len(d))+'\t\t'+'http://'+IP+':'+PORT+'/run?systemName='+d for d in os.listdir(case_path) if os.path.isdir(os.path.join(case_path, d))]
    return web.Response(body='\n'.join(dirs))


async def run(request):
    """
    run接口，把测试任务放入队列中
    :param request:
    :return:
    """
    if request.method == 'GET':
        system_name = request.query.get('systemName')     # 待执行测试的系统根路径
        case_path = os.path.join(cfg.getConfig('case_path'), system_name)   # 测试用例路径
        record_path = os.path.join(case_path, cfg.getConfig('record_name'))     # 测试结果记录路径
        build_file = os.path.join(cfg.getConfig('case_path'), system_name, 'build.xml')     # build.xml路径
        email_file = os.path.join(case_path, 'email_default.txt')   # 邮件默认配置文件
        config_file = os.path.join(case_path, 'config_default.txt')     # jmx执行的配置文件对应的默认配置文件
        new_email_file = os.path.join(case_path, 'email.txt')  # 邮件配置文件
        new_config_file = os.path.join(case_path, 'config.txt')  # jmx执行的配置文件
        if os.path.exists(case_path):
            shutil.copy(email_file, new_email_file)     # 复制，用于发送邮件
            shutil.copy(config_file, new_config_file)   # 复制，用于jmx执行

            if not os.path.exists(record_path):
                f = open(record_path, 'a')
                f.close()

            if os.path.exists(build_file):
                schedule.task = [case_path, new_email_file]
                return web.Response(body=json.dumps({'code': 1, 'message': '操作成功，测试任务正在准备执行', 'data': None}, ensure_ascii=False))
            else:
                return web.Response(body=json.dumps({'code': 0, 'message': 'build.xml文件不存在，测试任务执行失败', 'data': None}, ensure_ascii=False))
        else:
            return web.Response(body=json.dumps({
                'code': 0, 'message': '未找到与系统名称对应的脚本，请确认系统名称是否正确，脚本是否存在！', 'data': None}, ensure_ascii=False))
    else:
        post_data = await request.json()
        system_name = request.query.get('systemName')   # 待执行测试的系统根路径
        case_path = os.path.join(cfg.getConfig('case_path'), system_name)  # 测试用例路径
        record_path = os.path.join(case_path, cfg.getConfig('record_name'))  # 测试结果记录路径
        build_file = os.path.join(cfg.getConfig('case_path'), system_name, 'build.xml')  # build.xml路径
        email_file = os.path.join(case_path, 'email_default.txt')  # 邮件默认配置文件
        config_file = os.path.join(case_path, 'config_default.txt')  # jmx执行的配置文件对应的默认配置文件
        new_email_file = os.path.join(case_path, 'email.txt')  # 邮件配置文件
        new_config_file = os.path.join(case_path, 'config.txt')  # jmx执行的配置文件

        if os.path.exists(case_path):
            if not os.path.exists(record_path):
                f = open(record_path, 'a')
                f.close()

            if post_data.get('email'):
                replace_email(email_file, post_data['email'], new_email_file)

            if post_data.get('params'):
                replace_config(config_file, post_data['params'], new_config_file)

            if os.path.exists(build_file):
                schedule.task = [case_path, new_email_file]
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
    ind = request.match_info['ind']
    IP = request.match_info['IP']
    email_file = glob.glob(os.path.join(cfg.getConfig('case_path'), name, 'email_*.txt'))
    if len(email_file) == 0:
        return web.Response(body=json.dumps({'code': 0, 'message': '没有设置收件人邮箱地址的txt文件，测试任务执行失败', 'data': None}, ensure_ascii=False))
    elif len(email_file) > 1:
        return web.Response(body=json.dumps({'code': 0, 'message': '应该只有一个收件人邮箱地址的txt文件，但是找到了多个，测试任务执行失败', 'data': None}, ensure_ascii=False))

    if int(ind) == 1:
        msg = f'{IP} 服务器上的 {port} 端口已经停了，无法执行 {name} 的接口自动化测试，请及时检查端口状态'
    else:
        msg = f'{IP} 服务器上的 {name} 接口自动化测试执行异常，请检查测试用例，或手动执行get请求 http://{IP}:{PORT}/run?systemName={name} '
    html = f'<html><body>' \
           f'<h3>异常提醒：{msg}！</h3>' \
           f'<p style="color:blue;">此邮件自动发出，请勿回复。</p></body></html>'
    try:
        sendMsg(html, email_file[0], is_path=False)
        return web.Response(body=json.dumps({'code': 1, 'message': '邮件提醒发送成功！', 'data': None}, ensure_ascii=False))
    except Exception as err:
        return web.Response(body=json.dumps({'code': 0, 'message': err, 'data': None}, ensure_ascii=False))


async def main():
    app = web.Application()
    app.router.add_static('/testReport/', path=report_path)

    app.router.add_route('GET', '/', get_list)
    app.router.add_route('*', '/run', run)
    app.router.add_route('GET', '/sendEmail/{name}/{port}/{ind}/{IP}', sendEmail)

    app_runner = web.AppRunner(app)
    await app_runner.setup()
    site = web.TCPSite(app_runner, IP, int(PORT))
    await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
