"""
配置文件
"""
import os

# 服务器配置
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 7777))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# ddddocr配置
OCR_BETA = os.getenv('OCR_BETA', 'true').lower() == 'true'
DET_BETA = os.getenv('DET_BETA', 'true').lower() == 'true'
SHOW_AD = os.getenv('SHOW_AD', 'false').lower() == 'true'

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
