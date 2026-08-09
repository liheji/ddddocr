"""
配置文件
"""
import importlib.metadata
import os
import tomllib
from pathlib import Path

from const.mode import Mode

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _default_version() -> str:
    """服务版本号以 pyproject.toml 为唯一来源（优先读取已安装包元数据）"""
    try:
        return importlib.metadata.version('ddddocr-api')
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        with open(_PROJECT_ROOT / 'pyproject.toml', 'rb') as f:
            return tomllib.load(f)['project']['version']
    except (OSError, KeyError, TypeError):
        return 'unknown'


# 服务版本号：环境变量可覆盖，默认取自 pyproject.toml
APP_VERSION = os.getenv('APP_VERSION') or _default_version()

# 服务器配置
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 7777))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
# 请求体与单张图片的统一大小上限（字节），默认 16MB
# 同时用于 Flask 请求体限制和 base64 解码/URL 下载/bytes 的图片大小校验
MAX_IMAGE_BYTES = int(os.getenv('MAX_IMAGE_BYTES', 16 * 1024 * 1024))

# ddddocr配置
# 启动模式：ocr=仅加载OCR模型，det=仅加载目标检测模型，both=两者都加载（默认）
_raw_mode = os.getenv('MODE', 'both').strip().lower()
try:
    MODE = Mode(_raw_mode)
except ValueError:
    raise ValueError(f"MODE 配置无效: {_raw_mode}（可选值: ocr / det / both）") from None
SHOW_AD = os.getenv('SHOW_AD', 'false').lower() == 'true'
USE_GPU = os.getenv('USE_GPU', 'false').lower() == 'true'
DEVICE_ID = int(os.getenv('DEVICE_ID', 0))

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
