# -*- coding: utf-8 -*-
"""
@time: 2018-01-04
@author: ssf
"""
from splinter.browser import Browser
from configparser import ConfigParser
from time import sleep
import traceback
import time, sys
import codecs
import argparse

class huoche(object):
    """docstring for huoche"""
    driver_name=''
    executable_path=''
	
    """读取配置文件"""
    def readConfig(self, config_file='config.ini'):
        cp = ConfigParser()
        try:
            # 指定读取config.ini编码格式，防止中文乱码（兼容windows）
            cp.readfp(codecs.open(config_file, "r", "utf-8-sig"))
        except IOError as e:
            print(u'打开配置文件"%s"失败, 请先创建或者拷贝一份配置文件config.ini' % (config_file))
            raw_input('Press any key to continue')
            sys.exit()
        # 登录名
        self.username = cp.get("login", "username")
        # 密码
        self.passwd = cp.get("login", "password")
        # 始发站
        self.starts = cp.get("cookieInfo", "starts")
        # 终点站
        self.ends = cp.get("cookieInfo", "ends")
        # 乘车时间
        self.dtime = cp.get("cookieInfo", "dtime")
        # 车次
        orderStr = cp.get("orderItem", "order")
        # 配置文件中的是字符串，转换为int
        self.order = int(orderStr)
        # 乘客名
        self.users = cp.get("userInfo", "users").split(",")
        # 车次类型
        self.train_types = cp.get("trainInfo", "train_types").split(",")
        # 发车时间
        self.start_time = cp.get("trainInfo", "start_time")
        # 网址
        self.ticket_url = cp.get("urlInfo", "ticket_url")
        self.login_url = cp.get("urlInfo", "login_url")
        self.initmy_url = cp.get("urlInfo", "initmy_url")
        self.buy = cp.get("urlInfo", "buy")

        # 浏览器名称：目前使用的是chrome
        self.driver_name = cp.get("pathInfo", "driver_name")
        # 浏览器驱动（目前使用的是chromedriver）路径
        self.executable_path = cp.get("pathInfo", "executable_path")

    def loadConfig(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config', help='Specify config file, use absolute path')
        args = parser.parse_args()
        if args.config:
            # 使用指定的配置文件
            self.readConfig(args.config)
        else:
            # 使用默认的配置文件config.ini
            self.readConfig()

    def __init__(self):
        # 读取配置文件，获得初始化参数
        self.loadConfig();

    def login(self):
        # 登录
        self.driver.visit(self.login_url)
        # 自动填充用户名
        self.driver.fill("loginUserDTO.user_name", self.username)
        # 自动填充密码
        self.driver.fill("userDTO.password", self.passwd)

        print(u"等待验证码，自行输入...")

        # 验证码需要自行输入，程序自旋等待，直到验证码通过，点击登录
        while True:
            if self.driver.url != self.initmy_url:
                sleep(1)
            else:
                break
    
    """更多查询条件"""            
    def searchMore(self):
        # 选择车次类型
        for type in self.train_types:
            #type = type.replace("\"", "")
            # 车次类型选择
            train_type_dict = {'T': u'T-特快',                # 特快
                                'G': u'GC-高铁/城际',         # 高铁
                                'D': u'D-动车',               # 动车
                                'Z': u'Z-直达',               # 直达
                                'K': u'K-快速'                # 快速
                                }
            if type == 'T' or type == 'G' or type == 'D' or type == 'Z':
                print(u'--------->选择的车次类型', train_type_dict[type])
                self.driver.find_by_text(train_type_dict[type]).click()
            else:
                print(u"车次类型异常或未选择!(train_type=%s)" % type)
		
        # 选择发车时间
        print(u'--------->选择的发车时间', self.start_time)
        self.driver.find_option_by_text(self.start_time).first.click()
	
    """填充查询条件"""
    def preStart(self):
        # 加载查询信息
        # 出发地
        self.driver.cookies.add({"_jc_save_fromStation": self.starts})
        # 目的地
        self.driver.cookies.add({"_jc_save_toStation": self.ends})
        # 出发日
        self.driver.cookies.add({"_jc_save_fromDate": self.dtime})

    def buyTickets(self):
        try:
            print(u"购票页面开始...")
            
            # 填充查询条件
            self.preStart()

            # 带着查询条件，重新加载页面
            self.driver.reload()

            count=0
            # 预定车次算法：根据order的配置确定开始点击预订的车次，0-从上至下点击
            if self.order!=0:
                while self.driver.url==self.ticket_url:
                    # 勾选车次类型，发车时间
                    self.searchMore();
                    sleep(0.05)
                    self.driver.find_by_text(u"查询").click()
                    count += 1
                    print(u"循环点击查询... 第 %s 次" % count)
                    
                    try:
                        self.driver.find_by_text(u"预订")[self.order - 1].click()
                    except Exception as e:
                        print(e)
                        print(u"还没开始预订")
                        continue
            else:
                while self.driver.url == self.ticket_url:
                    # 勾选车次类型，发车时间
                    self.searchMore();
                    
                    self.driver.find_by_text(u"查询").click()
                    count += 1
                    print(u"循环点击查询... 第 %s 次" % count)
                    
                    try:
                        for i in self.driver.find_by_text(u"预订"):
                            i.click()
                            # 等待0.3秒，提交等待的时间
                            sleep(0.3)
                    except Exception as e:
                        print(e)
                        print(u"还没开始预订 %s" %count)
                        continue
            print(u"开始预订...")
            
            sleep(0.8)
            print(u'开始选择用户...')
            for user in self.users:
                self.driver.find_by_text(user).last.click()

            print(u"提交订单...")
            sleep(1)
            # self.driver.find_by_text(self.pz).click()
            # self.driver.find_by_id('').select(self.pz)
            # # sleep(1)
            # self.driver.find_by_text(self.xb).click()
            # sleep(1)
            self.driver.find_by_id('submitOrder_id').click()
            # print u"开始选座..."
            # self.driver.find_by_id('1D').last.click()
            # self.driver.find_by_id('1F').last.click()

            # 若提交订单异常，请适当加大sleep的时间
            sleep(1)
            print(u"确认选座...")
            self.driver.find_by_id('qr_submit_id').click()

        except Exception as e:
            print(e)

    """入口函数"""
    def start(self):
        # 初始化驱动
        self.driver=Browser(driver_name=self.driver_name,executable_path=self.executable_path)
        # 初始化浏览器窗口大小
        self.driver.driver.set_window_size(1400, 1000)

        # 登录，自动填充用户名、密码，自旋等待输入验证码，输入完验证码，点登录后，访问 tick_url（余票查询页面）
        self.login()

        # 登录成功，访问余票查询页面
        self.driver.visit(self.ticket_url)

        # 自动购买车票
        self.buyTickets();

if __name__ == '__main__':
    huoche=huoche()
    huoche.start()
