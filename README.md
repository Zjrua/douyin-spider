# 抖音账号数据爬虫

## 项目简介
基于Selenium的抖音数据采集工具，支持自动登录验证、动态内容加载监控和数据持久化存储，可采集视频播放量、点赞数等关键指标。

## 功能特性
- 自动化登录验证（支持Cookie复用）
- 智能页面滚动加载监控
- 动态元素定位与数据解析
- CSV格式数据持久化存储
- 自动反爬策略规避（UserAgent轮换、浏览器指纹伪装）

## 环境要求
```bash
Python 3.8+
ChromeDriver 120.0.6099.109
```

## 快速入门
```bash
# 安装依赖
pip install selenium==4.8.0 beautifulsoup4==4.12.2 webdriver-manager==3.8.6

# 运行爬虫
python douyin_spider.py
```

## 注意事项
1. 首次运行需扫码登录（15秒超时机制）
2. 数据存储路径：`./data/douyin_data.csv`
3. ChromeDriver需与本地Chrome浏览器版本匹配
4. 反爬策略：
   - 启用`--disable-blink-features=AutomationControlled`
   - 随机化UserAgent和滚动间隔
   - 使用`webdriver-manager`自动管理驱动版本

## 文件结构
```
├── data/               # 数据存储目录
├── logs/               # 运行日志
├── cookies_manager.py  # 登录验证模块
└── douyin_spider.py    # 主爬虫程序
```