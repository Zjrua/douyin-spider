import requests
from bs4 import BeautifulSoup
import time
import csv
import os
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from selenium import webdriver

# 新增必要的导入
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cookies_manager import load_cookies, save_cookies

def get_douyin_data(account_url):
    # 初始化浏览器驱动
    # 改进后的浏览器初始化配置
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # 加载已保存的cookies
        try:
            cookies = load_cookies(account_url)
            for cookie in cookies:
                driver.add_cookie(cookie)
        except Exception as e:
            logging.warning(f'Cookie加载失败: {str(e)}')
        
        driver.get(account_url)
        handle_login(driver, account_url)
        # 增强的页面加载检测
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, 'loading-indicator'))
        )
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    except Exception as e:
        logging.error(f'浏览器初始化失败: {str(e)}')
        if 'driver' in locals():
            driver.quit()
        raise SystemExit('浏览器驱动异常，程序终止')
    # 创建存储目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/douyin_crawler.log'),
            logging.StreamHandler()
        ]
    )
    
    # 初始化CSV文件
    csv_file = open('data/douyin_data.csv', 'w', newline='', encoding='utf-8')  # 清空已有内容
    writer = csv.writer(csv_file)
    writer.writerow(['视频标题', '发布时间', '播放量', '点赞数', '收藏数', '评论数'])
    
    # 记录开始爬取
    logging.info(f'Start crawling: {account_url}')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(account_url, headers=headers)
        logging.info(f'Request successful: {response.status_code}')
    except Exception as e:
        logging.error(f'Request failed: {str(e)}')
        return
    
    if response.status_code == 200:
        # 处理动态加载
        last_height = 0
        # 增加滚动次数和等待时间
        scroll_attempts = 0
        while scroll_attempts < 5:  # 最多滚动5次
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 增加等待时间
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # 添加滚动调试日志
            logging.info(f'滚动后页面高度: {new_height} 上次高度: {last_height}')
            
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height
            
            # 实时解析更新内容
            current_soup = BeautifulSoup(driver.page_source, 'html.parser')
            videos = current_soup.find_all('div', {'class': 'ECMy_Zdt'})  # 更新视频容器选择器
            if videos:
                logging.info(f'发现 {len(videos)} 个视频')
                break
            
            time.sleep(1)
        
        # 使用最终页面内容
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 解析网页内容，提取所需数据
        # 更新为最新的视频容器选择器
        # 更新元素选择器并添加异常处理
        try:
            videos = soup.find_all('div', {'class': 'ECMy_Zdt'})  # 最新抖音视频容器class
            logging.info(f'总共找到 {len(videos)} 个视频元素')
        except Exception as e:
            logging.error(f'元素查找失败: {str(e)}')
            videos = []
        for video in videos:
            try:
                title = video.find('a', {'class': 'title'}).text.strip()
                publish_time = video.find('span', {'class': 'publish-time'}).text.strip()
                play_count = video.find('span', {'class': 'play-count'}).text.strip()
                like_count = video.find('span', {'class': 'like-count'}).text.strip()
                collect_count = video.find('span', {'class': 'collect-count'}).text.strip()
                comment_count = video.find('span', {'class': 'comment-count'}).text.strip()
                
                # 时间筛选逻辑，仅处理上个月的内容
                if is_last_month(publish_time):
                    print(f'发布时间: {publish_time}, 播放量: {play_count}, 点赞数: {like_count}, 收藏数: {collect_count}, 评论数: {comment_count}')
                    writer.writerow([title, publish_time, play_count, like_count, collect_count, comment_count])
            except Exception as e:
                logging.error(f'数据解析错误: {str(e)}')
        
        # 关闭CSV文件
        csv_file.close()
    else:
        print('Failed to retrieve data from Douyin')

def is_last_month(time_str):
    try:
        # 处理抖音时间格式（如'3天前'或'2023-08-15'）
        if '前' in time_str:
            days_ago = int(time_str.split('天')[0])
            publish_date = datetime.now() - timedelta(days=days_ago)
        else:
            publish_date = datetime.strptime(time_str, '%Y-%m-%d')
            
        current_date = datetime.now()
        # 计算上个月的第一天
        first_day_of_last_month = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        return first_day_of_last_month <= publish_date < first_day_of_last_month + relativedelta(months=1)
    except Exception as e:
        logging.error(f'时间解析错误: {time_str} - {str(e)}')
        return False

if __name__ == '__main__':
    account_url = 'https://www.douyin.com/user/MS4wLjABAAAAZJdMJWCk20BhmfjdkBtg_3OwU9tHA9aoKriwjS52wFo?from_tab_name=main'  # 哈工大官方账号URL
    get_douyin_data(account_url)