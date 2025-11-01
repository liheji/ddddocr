"""
图片处理工具类
"""
import re
import base64
import requests
from io import BytesIO
from PIL import Image
from typing import Union


def get_image_bytes(image_data: Union[str, bytes]) -> bytes:
    """
    获取图片字节流，支持多种输入格式
    :param image_data: 图片数据（支持URL、base64、bytes）
    :return: 图片字节流
    """
    if isinstance(image_data, bytes):
        return image_data
    elif isinstance(image_data, str):
        if image_data.startswith('http://') or image_data.startswith('https://'):
            response = requests.get(image_data, verify=False, timeout=10)
            response.raise_for_status()
            return response.content
        elif image_data.startswith('data:image'):
            image_data = re.sub('^data:image/.+;base64,', '', image_data)
            return base64.b64decode(image_data)
        else:
            # 尝试作为base64解码
            try:
                return base64.b64decode(image_data)
            except:
                raise ValueError("Unsupported image data format")
    else:
        raise ValueError("Unsupported image data type")


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    将PIL图片转换为base64字符串
    :param image: PIL图片对象
    :param format: 图片格式
    :return: base64编码字符串
    """
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str
