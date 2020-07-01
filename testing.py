#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari
import os
import re
import time
from threading import Lock
from git import Repo
from sendEmail import sendMsg
from logger import logger, cfg


class Testing(object):
    def __init__(self):
        self.lock = Lock()

    def run(self, case_email_path):
        """
        执行测试任务
        :param case_email_path: 列表，第一个元素是测试用例文件路径，第二个元素是收件人的txt文件路径
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

        file_name = None
        error_msg = None
        case_path = case_email_path[0]
        email_path = case_email_path[1]
        build_path = os.path.join(case_path, 'build.xml')
        logger.info(f'开始执行测试任务{build_path}')

        try:
            start_time = time.strftime('%Y-%m-%d %H:%M:%S')
            res = os.popen('ant -f {}'.format(build_path)).readlines()  # 执行测试，并等待测试完成
            for i in range(len(res)):
                if 'Build failed' in res[i]:    # 如果有失败日志，打印出
                    error_msg = '{}\n{}'.format(res[i-1], res[i])
                    logger.error(error_msg)
                    break
                if 'xslt' in res[i] and 'Processing' in res[i] and 'to' in res[i]:  # 获取测试报告文件名
                    line = res[i].strip()
                    logger.debug(line)
                    if '/' in line:
                        file_name = line.split('/')[-1]
                    else:
                        file_name = line.split('\\')[-1]
                    logger.info(file_name)
                    break
        except Exception as err:
            error_msg = err
            logger.error(err)

        if file_name:
            logger.info('测试任务执行完成')
            time.sleep(2)
            msg = self.parse_html(file_name, case_path)    # 重组html

            sendMsg(msg['fail_case'], email_path)   # 发送邮件

            string = f"{start_time},{build_path},{msg['total_num']},{msg['failure_num']}\n"
            self.lock.acquire()
            logger.info(f'写测试记录到本地, {string}')
            with open(os.path.join(case_path, cfg.getConfig('record_name')), 'a', encoding='utf-8') as f:
                f.write(string)
            self.lock.release()
            logger.info('测试完成')
        else:
            logger.error(f'测试任务执行失败，失败信息：{error_msg}')
            html = f'<html><body>' \
                   f'<h3>异常提醒：{build_path} 测试任务执行失败，失败信息：{error_msg}，请重新执行！</h3>' \
                   f'<p style="color:blue;">此邮件自动发出，请勿回复。</p></body></html>'
            try:
                sendMsg(html, email_path, is_path=False)
            except Exception as err:
                logger.error(err)

    def parse_html(self, file_name, case_path):
        """
        提取自动生成的测试报告中的一些信息，重组测试报告用于邮件发送
        :param case_path: 测试用例路径
        :param file_name: 测试报告名称
        :return:
        """
        try:
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
            self.lock.acquire()
            with open(os.path.join(case_path, cfg.getConfig('record_name')), 'r', encoding='utf-8') as f:
                history = f.readlines()
            self.lock.release()
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
            return {'all_case': all_case, 'fail_case': fail_case, 'total_num': total_num[0], 'failure_num': failure_num[0]}
        except Exception as err:
            logger.error(err)
            raise Exception(err)
