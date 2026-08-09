"""
启动模式定义

外部环境变量/请求字符串在边界处转换为 Mode 枚举，
核心层只接受枚举，不做字符串兼容。
"""
from enum import Enum


class Mode(Enum):
    """CAPTCHA 启动模式"""
    OCR = 'ocr'    # 仅加载 OCR 模型
    DET = 'det'    # 仅加载目标检测模型
    BOTH = 'both'  # 两者都加载
