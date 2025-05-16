import json
import os
import logging
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_DIR = os.path.join('data', 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

def get_cookie_filename(url):
    domain = url.split('//')[-1].split('/')[0]
    return os.path.join(COOKIES_DIR, f'{domain}_cookies.json')

def load_cookies(url):
    try:
        cookie_file = get_cookie_filename(url)
        if not os.path.exists(cookie_file):
            return []
            
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
            
        # 检查cookie有效期（示例逻辑）
        expire_timestamp = cookies[0].get('expiry', 0)
        if expire_timestamp and datetime.now().timestamp() > expire_timestamp:
            logging.warning('Cookie已过期')
            return []
            
        return cookies
    except Exception as e:
        logging.error(f'加载Cookie失败: {str(e)}')
        return []

def save_cookies(driver, url):
    try:
        cookies = driver.get_cookies()
        cookie_file = get_cookie_filename(url)
        
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
            
        logging.info(f'成功保存{len(cookies)}个Cookie')
    except Exception as e:
        logging.error(f'保存Cookie失败: {str(e)}')

def handle_login(driver, url):
    try:
        # 检查是否已登录
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-e2e="user-info"]'))
        )
        return True
    except:
        # 触发扫码登录流程
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.login-btn'))
        )
        login_btn.click()
        
        # 等待二维码加载
        qr_code = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.qrcode-container img'))
        )
        logging.info('请使用抖音APP扫码登录（15秒超时）')
        
        # 检测登录成功
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-e2e="user-info"]'))
            )
            save_cookies(driver, url)
            return True
        except:
            logging.error('扫码登录超时')
            return False