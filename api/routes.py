"""
API路由定义
"""
import logging
from typing import Optional
from flask import Blueprint, request

from core import CAPTCHA, FeatureDisabledError
from const import APP_VERSION
from const.charset import parse_ranges
from const.color import parse_color_filters
from const.errno import Errno
from utils import R
from .helpers import error_response, require_single_image, service_result

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# 初始化CAPTCHA实例（将在app.py中注入）
captcha: Optional[CAPTCHA] = None


@api_bp.route('/capcode', methods=['POST'])
def capcode():
    """
    滑块验证码识别接口（匹配算法）
    请求参数:
    - slidingImage: 滑块图片（必需，支持URL、base64、bytes，或 multipart 文件字段 slidingImage）
    - backImage: 背景图片（必需，支持URL、base64、bytes，或 multipart 文件字段 backImage）
    - simpleTarget: 是否使用简单目标模式（可选，默认true）
    成功响应 data 为缺口中心 x 坐标
    """
    try:
        sliding_image = require_single_image(request, field='slidingImage')
        back_image = require_single_image(request, field='backImage')
        simple_target = (request.get_json(silent=True) or {}).get('simpleTarget', True)

        result = captcha.capcode(sliding_image, back_image, simple_target)
        return service_result(result, '滑块识别过程中出现错误')
    except Exception as e:
        logger.error(f"滑块识别接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/slideComparison', methods=['POST'])
def slide_comparison():
    """
    滑块对比算法接口
    请求参数:
    - slidingImage: 带缺口的图片（必需，支持URL、base64、bytes，或 multipart 文件字段 slidingImage）
    - backImage: 完整背景图片（必需，支持URL、base64、bytes，或 multipart 文件字段 backImage）
    成功响应 data 为缺口中心 x 坐标
    """
    try:
        sliding_image = require_single_image(request, field='slidingImage')
        back_image = require_single_image(request, field='backImage')

        result = captcha.slide_comparison(sliding_image, back_image)
        return service_result(result, '滑块对比过程中出现错误')
    except Exception as e:
        logger.error(f"滑块对比接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/classification', methods=['POST'])
def classification():
    """
    OCR文字识别接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes，或 multipart 文件字段 image）
    - png_fix: 是否启用PNG修复（可选，默认false）
    - probability: 是否返回识别概率（可选，默认false）
    - color_filter_colors: 颜色过滤列表（可选），如 ["red", "blue"] 或自定义HSV范围 [[[0,50,50],[10,255,255]]]
    - charset_ranges: 本次请求的字符集限制（可选），仅支持内置索引 int 0-7
    成功响应 data 为识别文本；probability=true 时为 {text, probabilities, charset, confidence}
    """
    try:
        data = request.get_json(silent=True) or {}
        image = require_single_image(request, field='image')
        png_fix = data.get('png_fix', False)
        probability = data.get('probability', False)
        color_filter_colors = parse_color_filters(data.get('color_filter_colors'))
        charset_range = data.get('charset_ranges')
        if charset_range is not None:
            charset_range = parse_ranges(charset_range)

        result = captcha.classification(
            image,
            png_fix=png_fix,
            probability=probability,
            color_filter_colors=color_filter_colors,
            charset_range=charset_range,
        )

        return service_result(result, 'OCR识别过程中出现错误')
    except Exception as e:
        logger.error(f"OCR识别接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/captcha/base64', methods=['POST'])
def captcha_base64():
    """
    MoviePilot 兼容接口：识别 base64 图片文字
    请求: {"base64_img": "图片base64"}
    成功: 200 {"result": "识别文本"}
    失败: 4xx/5xx {"result": null}
    """
    try:
        image = require_single_image(request, field='base64_img')
        result = captcha.classification(image)
        if result is None:
            logger.error('captcha/base64 识别过程中出现错误')
            return {'result': None}, 500
        return {'result': result}
    except FeatureDisabledError as e:
        logger.error(f"captcha/base64 兼容接口错误: {e}", exc_info=True)
        return {'result': None}, 503
    except Exception as e:
        logger.error(f"captcha/base64 兼容接口错误: {e}", exc_info=True)
        return {'result': None}, 400


@api_bp.route('/detection', methods=['POST'])
def detection():
    """
    目标检测接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes，或 multipart 文件字段 image）
    成功响应 data 为边界框列表 [[x1,y1,x2,y2], ...]
    """
    try:
        image = require_single_image(request, field='image')

        result = captcha.detection(image)
        return service_result(result, '目标检测过程中出现错误')
    except Exception as e:
        logger.error(f"目标检测接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    计算类验证码处理接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes，或 multipart 文件字段 image）
    - charset_ranges: 字符集限制（可选），仅支持内置索引 int 0-7
    成功响应 data 为计算结果（int/float）
    """
    try:
        data = request.get_json(silent=True) or {}
        image = require_single_image(request, field='image')
        charset_range = data.get('charset_ranges')
        if charset_range is not None:
            charset_range = parse_ranges(charset_range)
        result = captcha.calculate(image, charset_range=charset_range)
        return service_result(result, '计算验证码过程中出现错误')
    except Exception as e:
        logger.error(f"计算验证码接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/crop', methods=['POST'])
def crop():
    """
    图片分割接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes，或 multipart 文件字段 image）
    - y_coordinate: Y坐标分割线（必需，JSON 或 multipart 表单字段），上半部分为 0..y，下半部分为 y..图片高度
    成功响应 data 为 {slidingImage: 上半部分base64, backImage: 下半部分base64}
    """
    try:
        image = require_single_image(request, field='image')
        data = request.get_json(silent=True) or {}
        y_value = data.get('y_coordinate')
        if y_value is None:
            y_value = request.form.get('y_coordinate')
        if y_value is None:
            raise ValueError('缺少必需参数: y_coordinate')
        y_coordinate = int(y_value)

        result = captcha.crop(image, y_coordinate)
        return service_result(result, '图片分割过程中出现错误')
    except Exception as e:
        logger.error(f"图片分割接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/select', methods=['POST'])
def select():
    """
    点选验证码接口
    请求参数:
    - image: 图片数据（必需，支持URL、base64、bytes，或 multipart 文件字段 image）
    成功响应 data 为 [{text, bbox: [x1,y1,x2,y2]}, ...]
    """
    try:
        image = require_single_image(request, field='image')

        result = captcha.select(image)
        return service_result(result, '点选验证码处理过程中出现错误')
    except Exception as e:
        logger.error(f"点选验证码接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/set_ranges', methods=['POST'])
def set_ranges():
    """
    设置OCR字符集范围接口（全局生效，仅OCR模式可用）
    请求参数:
    - ranges: 内置字符集索引 int 0-7（仅支持简称）；传 null 清除限制
    """
    try:
        data = request.get_json(silent=True)
        if data is None or 'ranges' not in data:
            return R.error(Errno.PARAM, '缺少必需参数: ranges').json()

        ranges = data['ranges']
        if ranges is None:
            captcha.clear_ranges()
            return R.ok(data=None, msg='字符集范围已清除').json()
        ranges = parse_ranges(ranges)
        captcha.set_ranges(ranges)
        return R.ok(data=ranges, msg='字符集范围设置成功').json()
    except Exception as e:
        logger.error(f"设置字符集范围接口错误: {e}", exc_info=True)
        return error_response(e)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return R.ok(data={'status': 'running', 'version': APP_VERSION}, msg='API运行成功！').json()


@api_bp.route('/status', methods=['GET'])
def status():
    """
    状态查询接口：返回服务状态、版本与当前OCR字符集信息
    """
    data = {'status': 'running', 'version': APP_VERSION}
    if captcha.ocr is not None:
        data['charset'] = captcha.get_charset()
        data['ranges'] = captcha.charset_range
    return R.ok(data=data, msg='API运行成功！').json()
