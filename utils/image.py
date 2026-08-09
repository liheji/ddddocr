"""
图片处理工具类
"""
import base64
import re
from io import BytesIO
from typing import Union

import requests
from PIL import Image

from const.setting import MAX_IMAGE_BYTES


def get_image_bytes(image_data: Union[str, bytes]) -> bytes:
    """
    获取图片字节流，支持多种输入格式
    :param image_data: 图片数据（支持URL、base64、bytes）
    :return: 图片字节流
    """
    if isinstance(image_data, bytes):
        return _check_image_size(image_data)
    if not isinstance(image_data, str):
        raise ValueError("Unsupported image data type")
    if image_data.startswith('http://') or image_data.startswith('https://'):
        return _download_image(image_data)
    if '://' in image_data:
        raise ValueError("仅支持 http/https 图片URL")
    if image_data.startswith('data:image'):
        image_data = re.sub('^data:image/.+;base64,', '', image_data)
    return _decode_base64(image_data)


def image_to_base64(image: Image.Image, img_format: str = 'PNG') -> str:
    """
    将PIL图片转换为base64字符串
    :param image: PIL图片对象
    :param img_format: 图片格式
    :return: base64编码字符串
    """
    buffered = BytesIO()
    image.save(buffered, format=img_format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def _check_image_size(data: bytes) -> bytes:
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"图片数据超过 {MAX_IMAGE_BYTES // (1024 * 1024)}MB 大小限制"
        )
    return data


def _decode_base64(data: str) -> bytes:
    """解码 base64，兼容无填充与 URL-safe 编码，解码结果做大小限制"""
    padded = data + '=' * (-len(data) % 4)
    try:
        raw = base64.b64decode(padded, validate=True)
    except Exception:
        try:
            raw = base64.b64decode(padded, altchars=b'-_', validate=True)
        except Exception:
            raise ValueError("Unsupported image data format")
    return _check_image_size(raw)


def _download_image(url: str) -> bytes:
    """下载远程图片（调用方已校验 http/https），限制下载大小"""
    with requests.get(url, timeout=10, stream=True) as response:
        response.raise_for_status()

        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise ValueError(
                    f"图片数据超过 {MAX_IMAGE_BYTES // (1024 * 1024)}MB 大小限制"
                )
            chunks.append(chunk)
        return b''.join(chunks)
