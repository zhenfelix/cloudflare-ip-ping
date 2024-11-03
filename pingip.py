#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import ctypes
import  subprocess
from multiprocessing.pool import ThreadPool
import logging
import time
import re
from tqdm import tqdm

# 设置日志
def set_logging_format():
    logging.basicConfig(level=logging.INFO,
        format='%(message)s',
        filename="ping_host.log",
        filemode='w'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.FATAL)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

# 获得所有待测试ip
def get_all_ips(hosts_list_path):
    ips = []
    with open(hosts_list_path, "r") as f:
        for host in f.readlines():
            ips.append(host.strip())
    return ips


#多线程调用ping
def ping_host(ip):
    global finish
    popen = subprocess.Popen('ping -c 1 -w 1 %s' %ip, stdout=subprocess.PIPE,shell=True)
    popen.wait()
    res = popen.stdout.read().decode('utf-8').strip('\n')
    if "1 received" in res:
        try:
            latency = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms', res)
            latency = float(latency.group(1)) if latency else None
            loss = re.search(r'(\d+)% packet loss', res)
            loss = int(loss.group(1)) if loss else None
            if int(latency)<THRESHOLD:
                #logging.info("{}, 延迟:{}ms, 丢包:{}%".format(ip, latency, loss))
                outcomes.append((ip, int(latency), int(loss)))
        except Exception as e:
            print(e) 
    finish += 1  




if __name__ == '__main__':
    # 线程数：为200时候，我本地测试179秒。
    # 不同配置和网络的电脑结果有差异。线程不是越大越好，设置成不超过300。
    # 超过300后丢包测试的结果不准。
    # WORD_THREAD_NUM = int(input("线程数(一般设置为200)范围为0-2000："))
    WORD_THREAD_NUM = 200
    assert 0<WORD_THREAD_NUM<2000
    # 移动连接香港，一般设置100ms，电信联通连接美西，一般设置200
    # THRESHOLD = int(input("阈值(移动设置为100，电信联通设置200)范围为0-400:"))
    THRESHOLD = 300
    # assert 0<THRESHOLD<=400
    now = time.time()
    # 初始化参数
    set_logging_format()
    hosts_list_path  = "./input.txt"
    ips = get_all_ips(hosts_list_path)
    total = len(ips)
    finish = 1
    finish_temp = 1
    outcomes = []
    # 设置线程池
    pool = ThreadPool(WORD_THREAD_NUM)
    pool.map_async(ping_host,ips)
    pool.close()
    with tqdm(total=total) as pbar:
        while(True):
            # 更新bar
            time.sleep(1.0)
            pbar.update(finish-finish_temp)  
            finish_temp = finish
            if (total<=finish):
                outcomes.sort(key=lambda outcome_item: (outcome_item[2], outcome_item[1]))
                if len(outcomes)==0:
                    logging.info("没有找到合适的IP，请调整阈值")
                else:
                    for i in outcomes:
                        ip, latency, loss = i[0], i[1], i[2]
                        logging.info("{}, 延迟:{}ms, 丢包:{}%".format(ip, latency, loss))
                pool.terminate()
                print("正在退出")
                break
    print("总共耗时：",time.time()-now, 's')
