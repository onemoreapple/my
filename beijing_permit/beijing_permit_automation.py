#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动办理进京证脚本
每天定时检查并自动办理进京证
"""

import requests
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import schedule
import time
import logging
from typing import Optional, Dict, Any
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('beijing_permit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BeijingPermitAuto:
    def __init__(self):
        """初始化配置"""
        # 从环境变量或配置文件读取敏感信息
        self.username = os.getenv('BEIJING_USERNAME')
        self.password = os.getenv('BEIJING_PASSWORD')
        self.phone = os.getenv('BEIJING_PHONE')
        self.car_plate = os.getenv('BEIJING_CAR_PLATE')

        # API配置（需要通过抓包获取真实API）
        self.base_url = "https://api.beijing.gov.cn"  # 需要替换为真实API地址
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; ...)',  # 需要替换
            'X-App-Version': '3.2.1',
            'Content-Type': 'application/json'
        }

        # 邮件配置
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.recipient = os.getenv('RECIPIENT_EMAIL', self.email_user)

        self.session = requests.session()
        self.token = None
        self.refresh_token = None

    def login(self) -> bool:
        """
        登录获取token
        需要根据实际API实现
        """
        try:
            # 示例：需要替换为真实的登录API
            login_data = {
                'username': self.username,
                'password': self.password,
                'device_id': 'unique_device_id'  # 可能需要设备ID
            }

            response = self.session.post(
                f"{self.base_url}/auth/login",
                headers=self.headers,
                json=login_data
            )

            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.refresh_token = result.get('refresh_token')
                self.headers['Authorization'] = f'Bearer {self.token}'
                logger.info("登录成功")
                return True
            else:
                logger.error(f"登录失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False

    def refresh_access_token(self) -> bool:
        """
        刷新token
        """
        try:
            refresh_data = {
                'refresh_token': self.refresh_token
            }

            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                headers=self.headers,
                json=refresh_data
            )

            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.headers['Authorization'] = f'Bearer {self.token}'
                logger.info("Token刷新成功")
                return True
            else:
                logger.error("Token刷新失败，需要重新登录")
                return self.login()

        except Exception as e:
            logger.error(f"Token刷新异常: {e}")
            return self.login()

    def check_current_permit(self) -> Optional[Dict[str, Any]]:
        """
        查询当前进京证状态
        """
        try:
            # 示例：需要替换为真实的查询API
            response = self.session.get(
                f"{self.base_url}/permit/current",
                headers=self.headers,
                params={'car_plate': self.car_plate}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('data'):
                    permit = result['data']
                    end_date = datetime.strptime(permit['end_date'], '%Y-%m-%d')
                    days_left = (end_date - datetime.now()).days

                    logger.info(f"当前进京证有效期至: {permit['end_date']}, 剩余{days_left}天")
                    return {
                        'valid': True,
                        'end_date': permit['end_date'],
                        'days_left': days_left
                    }
                else:
                    logger.info("当前无有效进京证")
                    return {'valid': False}
            else:
                logger.error(f"查询失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"查询异常: {e}")
            return None

    def apply_permit(self) -> bool:
        """
        申请新的进京证
        """
        try:
            # 示例：需要替换为真实的申请API
            apply_data = {
                'car_plate': self.car_plate,
                'car_type': 'private',  # 私家车
                'entry_date': datetime.now().strftime('%Y-%m-%d'),
                'exit_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'reason': '通勤',  # 进京事由
                'routes': []  # 进京路线
            }

            # 可能需要人机验证（验证码或滑块）
            # captcha_id = self.get_captcha()
            # apply_data['captcha_id'] = captcha_id

            response = self.session.post(
                f"{self.base_url}/permit/apply",
                headers=self.headers,
                json=apply_data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("进京证申请成功")
                    return True
                else:
                    logger.error(f"申请失败: {result.get('message')}")
                    return False
            else:
                logger.error(f"申请失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"申请异常: {e}")
            return False

    def send_email_notification(self, subject: str, content: str):
        """
        发送邮件通知
        """
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.recipient
            msg['Subject'] = subject

            body = MimeText(content, 'plain', 'utf-8')
            msg.attach(body)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info("邮件通知发送成功")

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")

    def daily_check(self):
        """
        每日检查任务
        """
        logger.info("开始每日进京证检查...")

        # 登录
        if not self.login():
            self.send_email_notification(
                "进京证自动检查-登录失败",
                "无法登录北京交警APP，请检查账号密码或App是否有更新"
            )
            return

        # 查询当前进京证状态
        permit_status = self.check_current_permit()

        if permit_status is None:
            self.send_email_notification(
                "进京证自动检查-查询失败",
                f"无法查询当前进京证状态于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return

        if permit_status.get('valid'):
            days_left = permit_status['days_left']
            if days_left <= 2:  # 剩余2天时自动办理
                logger.info("进京证即将到期，开始办理新的...")
                if self.apply_permit():
                    self.send_email_notification(
                        "进京证自动办理成功",
                        f"您的车辆{self.car_plate}的新进京证已成功办理。\n"
                        f"有效期: {datetime.now().strftime('%Y-%m-%d')} - "
                        f"{(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}"
                    )
                else:
                    self.send_email_notification(
                        "进京证自动办理失败",
                        f"自动办理{self.car_plate}的进京证失败，请手动办理。\n"
                        f"当前进京证剩余有效期: {days_left}天"
                    )
            else:
                logger.info(f"进京证仍然有效（剩余{days_left}天），无需办理")
        else:
            # 没有进京证，立即办理
            logger.info("当前无进京证，开始办理...")
            if self.apply_permit():
                self.send_email_notification(
                    "进京证自动办理成功",
                    f"您的车辆{self.car_plate}的进京证已成功办理。\n"
                    f"有效期: {datetime.now().strftime('%Y-%m-%d')} - "
                    f"{(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}"
                )
            else:
                self.send_email_notification(
                    "进京证自动办理失败",
                    f"自动办理{self.car_plate}的进京证失败，请手动办理。"
                )

    def run(self):
        """
        运行自动化脚本
        """
        logger.info("启动进京证自动办理脚本")

        # 每天早上8点检查
        schedule.every().day.at("08:00").do(self.daily_check)

        # 也可以设置其他时间检查
        # schedule.every().day.at("20:00").do(self.daily_check)

        # 启动时先检查一次
        self.daily_check()

        # 保持运行
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 创建.env文件配置敏感信息
    """
    # .env文件内容示例
    BEIJING_USERNAME=your_username
    BEIJING_PASSWORD=your_password
    BEIJING_PHONE=your_phone
    BEIJING_CAR_PLATE=京AXXXXX
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASSWORD=your_email_password
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    RECIPIENT_EMAIL=recipient@email.com
    """

    auto_permit = BeijingPermitAuto()
    auto_permit.run()