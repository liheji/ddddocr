# API package

from core import CAPTCHA
from const import DEVICE_ID, MODE, SHOW_AD, USE_GPU
from . import routes
from .routes import api_bp


def init_routes():
    """初始化路由，注入CAPTCHA实例"""
    routes.captcha = CAPTCHA(
        mode=MODE, show_ad=SHOW_AD,
        use_gpu=USE_GPU, device_id=DEVICE_ID,
    )
