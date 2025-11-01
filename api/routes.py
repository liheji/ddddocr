"""
API路由定义
"""
import logging
from flask import Blueprint, request

from core import CAPTCHA
from const import *
from utils import R

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 初始化CAPTCHA实例（将在app.py中注入）
captcha: CAPTCHA = None


def init_routes():
    """初始化路由，注入CAPTCHA实例"""
    global captcha
    captcha = CAPTCHA(ocr_beta=OCR_BETA, det_beta=DET_BETA, show_ad=SHOW_AD)


@api_bp.route('/capcode', methods=['POST'])
def capcode():
    """
    滑块验证码识别接口（匹配算法）
    请求参数:
    - slidingImage: 滑块图片（必需）
    - backImage: 背景图片（必需）
    - simpleTarget: 是否使用简单目标模式（可选，默认true）
    """
    try:
        data = request.get_json()
        if not data or 'slidingImage' not in data or 'backImage' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: slidingImage, backImage').json()

        sliding_image = data['slidingImage']
        back_image = data['backImage']
        simple_target = data.get('simpleTarget', True)

        result = captcha.capcode(sliding_image, back_image, simple_target)
        if result is None:
            logger.error('滑块识别过程中出现错误')
            return R.error(SERVICE_ERROR, '滑块识别过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"滑块识别接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/slideComparison', methods=['POST'])
def slide_comparison():
    """
    滑块对比算法接口
    请求参数:
    - slidingImage: 滑块图片（必需）
    - backImage: 背景图片（必需）
    """
    try:
        data = request.get_json()
        if not data or 'slidingImage' not in data or 'backImage' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: slidingImage, backImage').json()

        sliding_image = data['slidingImage']
        back_image = data['backImage']

        result = captcha.slide_comparison(sliding_image, back_image)
        if result is None:
            logger.error('滑块对比过程中出现错误')
            return R.error(SERVICE_ERROR, '滑块对比过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"滑块对比接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/classification', methods=['POST'])
def classification():
    """
    OCR文字识别接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes）
    - png_fix: 是否启用PNG修复（可选，默认false）
    - probability: 是否返回识别概率（可选，默认false）
    - color_filter_colors: 颜色过滤列表（可选），如 ["red", "blue"] 或 [[[0,50,50],[10,255,255]]]
    - charset_ranges: 字符集限制（可选），如 "0123456789+-x/="
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: image').json()

        image = data['image']
        png_fix = data.get('png_fix', False)
        probability = data.get('probability', False)
        color_filter_colors = data.get('color_filter_colors', None)
        charset_ranges = data.get('charset_ranges', None)

        # 如果提供了字符集，先设置
        if charset_ranges:
            captcha.set_ranges(charset_ranges)

        result = captcha.classification(
            image,
            png_fix=png_fix,
            probability=probability,
            color_filter_colors=color_filter_colors
        )

        if result is None:
            logger.error('OCR识别过程中出现错误')
            return R.error(SERVICE_ERROR, 'OCR识别过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"OCR识别接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/detection', methods=['POST'])
def detection():
    """
    目标检测接口
    请求参数:
    - image: 图片数据（必需）
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: image').json()

        image = data['image']
        result = captcha.detection(image)

        if result is None:
            logger.error('目标检测过程中出现错误')
            return R.error(SERVICE_ERROR, '目标检测过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"目标检测接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    计算类验证码处理接口
    请求参数:
    - image: 图片数据（必需）
    - charset_ranges: 字符集限制（可选），如 "0123456789+-x/="
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: image').json()

        image = data['image']
        charset_ranges = data.get('charset_ranges', None)
        result = captcha.calculate(image, charset_ranges=charset_ranges)

        if result is None:
            logger.error('计算验证码过程中出现错误')
            return R.error(SERVICE_ERROR, '计算验证码过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"计算验证码接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/crop', methods=['POST'])
def crop():
    """
    图片分割接口
    请求参数:
    - image: 图片数据（必需）
    - y_coordinate: Y坐标分割点（必需）
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data or 'y_coordinate' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: image, y_coordinate').json()

        image = data['image']
        y_coordinate = int(data['y_coordinate'])

        result = captcha.crop(image, y_coordinate)
        if result is None:
            logger.error('图片分割过程中出现错误')
            return R.error(SERVICE_ERROR, '图片分割过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"图片分割接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/select', methods=['POST'])
def select():
    """
    点选验证码接口
    请求参数:
    - image: 图片数据（必需）
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: image').json()

        image = data['image']
        result = captcha.select(image)

        if result is None:
            logger.error('点选验证码处理过程中出现错误')
            return R.error(SERVICE_ERROR, '点选验证码处理过程中出现错误').json()

        return R.ok(data=result).json()
    except Exception as e:
        logger.error(f"点选验证码接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/set_ranges', methods=['POST'])
def set_ranges():
    """
    设置OCR字符集范围接口
    请求参数:
    - ranges: 字符集字符串，如 "0123456789+-x/="
    """
    try:
        data = request.get_json()
        if not data or 'ranges' not in data:
            return R.error(PARAM_ERROR, '缺少必需参数: ranges').json()

        ranges = data['ranges']
        captcha.set_ranges(ranges)
        return R.ok(data=ranges, msg='字符集范围设置成功').json()
    except Exception as e:
        logger.error(f"设置字符集范围接口错误: {e}", exc_info=True)
        return R.error(PARAM_ERROR, str(e)).json()


@api_bp.route('/health', methods=['GET'])
@api_bp.route('/status', methods=['GET'])
def health_check():
    """健康检查接口"""
    return R.ok(data={'status': 'running', 'version': '1.0.0'}, msg='API运行成功！').json()
