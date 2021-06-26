#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari
import os
import re
import time
import shutil
from threading import Thread
from git import Repo
from sendEmail import sendMsg
from logger import logger, cfg, handle_exception


class Testing(object):
    def __init__(self):
        self.interval = int(cfg.getConfig('interval'))
        self.tasking = []

        t = Thread(target=self.lookup)
        t.start()

    def run(self, paths):
        """
        执行测试任务
        :param paths: 字典
        :return:
        """
        try:
            if int(cfg.getConfig('is_git')):
                logger.info('准备从git上拉取最新版本')
                repo = Repo(cfg.getConfig('git_path'))
                remote = repo.remote()
                remote.pull()
                logger.info('从git上拉取版本成功')
        except Exception as err:
            logger.error(err)

        build_path = paths["build_file"]
        logger.info(f'开始执行测试任务{build_path}')

        try:
            if paths["method"] == "GET":
                shutil.copy(paths["config_file"], paths["new_config_file"])  # 复制，用于jmx执行
            else:
                if paths["post_data"].get('params'):
                    replace_config(paths["config_file"], paths["post_data"]['params'], paths["new_config_file"])

            report_name = f'{paths["system_name"]}-{int(time.time() * 1000)}'
            _ = os.popen('nohup ant -f {} -DReportName={} &'.format(build_path, report_name))  # 执行测试
            paths.update({"file_name": report_name})
            paths.update({"start_time": time.time()})
            self.tasking.append(paths)
            time.sleep(3)
        except Exception as err:
            logger.error(err)

    @handle_exception(is_return=True, default_value=False)
    def post_deal(self, paths):
        msg = self.parse_html(paths["file_name"] + '.html', paths["case_path"])  # 重组html

        sendMsg(msg['fail_case'], paths, failure_num=msg['failure_num'])  # 发送邮件

        string = f"{paths['start_time']},{paths['build_file']},{msg['total_num']},{msg['failure_num']}\n"
        logger.info(f'写测试记录到本地, {string}')
        with open(paths["record_path"], 'a', encoding='utf-8') as f:
            f.write(string)

        logger.info('测试完成')
        return True

    @handle_exception()
    def parse_html(self, file_name, case_path):
        """
        提取自动生成的测试报告中的一些信息，重组测试报告用于邮件发送
        :param case_path: 测试用例路径
        :param file_name: 测试报告名称
        :return:
        """
        all_case = os.path.join(cfg.getConfig('report_path'), file_name)    # 完整的测试报告路径
        fail_case = os.path.join(cfg.getConfig('report_path'), 'send_' + file_name)      # 处理好用于邮件发送的测试报告路径
        logger.info('开始处理html测试报告{}'.format(all_case))
        with open(all_case, 'r', encoding='utf-8') as f:
            htmls = f.readlines()

        html = ''
        for line in htmls:
            html += line.strip()

        # 提取用例总数，成功率数据
        case_num = re.findall('响应时间最大值</th>.*<td align="center">(\d+)</td><td align="center">(\d+)</td>'
                              '<td align="center">\d{1,3}.\d+%', html)[0]
        total_num = [int(case_num[0])]
        failure_num = [int(case_num[1])]

        # 提取出概览和失败用例，用于邮件发送
        # res = re.findall('(.*?)<h2>所有用例', html)[0]
        res = html.split('<h2>所有用例')[0]
        url = 'http://{}:{}/testReport/{}'.format(cfg.getConfig('host'), cfg.getConfig('port'), file_name)
        logger.info(f'详细测试报告跳转链接为 {url}')
        # 添加完整测试报告路径跳转链接
        jump_url = f'<span style="font-size: 125%; margin-left: 2.5%;">如需查看详细测试结果，<a href="{url}">请点我</a></span>'

        # 添加历史数据
        with open(os.path.join(case_path, cfg.getConfig('record_name')), 'r', encoding='utf-8') as f:
            history = f.readlines()
        for line in history:
            datas = line.split(',')
            total_num.append(int(datas[-2]))
            failure_num.append(int(datas[-1]))
        ratio = 100 - round(100 * sum(failure_num) / sum(total_num), 2)
        history = f'<hr align="center" width="95%" size="1"><h2>历史数据概览</h2><table width="95%" cellspacing="2" ' \
                  f'cellpadding="5" border="0" class="details" align="center"><tbody><tr valign="top"><th>累计执行次数' \
                  f'</th><th>累计执行用例数</th><th>累计执行失败用例数</th><th>执行成功率</th></tr><tr valign="top" ' \
                  f'style="font-weight: bold;"><td align="center">{len(total_num)}</td><td align="center">{sum(total_num)}</td>' \
                  f'<td align="center">{sum(failure_num)}</td><td align="center">{ratio}%</td></tr></tbody></table>'

        res1 = re.sub('<span>(.*?)</span>', jump_url+history, res)
        # 添加尾巴
        res = res1 + '<p style="color:blue;font-size: 125%;">此邮件自动发出，请勿回复。</p></body></html>'
        # 写到本地
        with open(fail_case, 'w', encoding='utf-8') as f:
            f.writelines(res)

        logger.info('html测试报告处理完成')
        del htmls, html, res, res1, history
        return {'all_case': all_case, 'fail_case': fail_case, 'total_num': total_num[0], 'failure_num': failure_num[0]}

    def lookup(self):
        while True:
            time.sleep(2)
            n = len(self.tasking)
            logger.info(f'当前正在执行的任务数为{n}')
            inds = []
            for i in range(n):
                html_path = os.path.join(cfg.getConfig('report_path'), self.tasking[i]["file_name"]) + '.html'
                logger.info(html_path)
                if not os.path.exists(html_path):
                    if time.time() - self.tasking[i]["start_time"] < self.interval:
                        continue
                    else:
                        logger.error(f'测试任务执行超时')
                        inds.append(i)
                        html = f'<html><body>' \
                               f'<h3>异常提醒：{self.tasking[i]["build_file"]} 测试任务执行超时，请检查！</h3>' \
                               f'<p style="color:blue;">此邮件自动发出，请勿回复。</p></body></html>'
                        try:
                            sendMsg(html, self.tasking[i], is_path=False)
                        except Exception as err:
                            logger.error(err)
                else:
                    time.sleep(1)
                    logger.info('测试任务执行完成')
                    flag = self.post_deal(self.tasking[i])
                    if flag:
                        inds.append(i)

            for j in range(len(inds) - 1, -1, -1):
                self.tasking.pop(inds[j])


def replace_config(src, new_dict, dst):
    old_dict = {}
    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        k_v = line.split('//')[0].split('=')
        old_dict.update({k_v[0].strip(): k_v[1].strip()})

    for k, v in new_dict.items():
        old_dict.update({k: v})

    lines = [f'{k}={v}\n' for k, v in old_dict.items()]
    with open(dst, 'w', encoding='utf-8') as f:
        f.writelines(lines)
