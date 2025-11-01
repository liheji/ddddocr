"""
CAPTCHA 核心识别类
"""
import cv2
import numpy as np
import re
import base64
import logging
from io import BytesIO
from PIL import Image
import ddddocr

from utils.image_utils import get_image_bytes, image_to_base64

logger = logging.getLogger(__name__)


class CAPTCHA:
    """验证码识别核心类"""

    def __init__(self, ocr_beta=True, det_beta=True, show_ad=False):
        """
        初始化识别器
        :param ocr_beta: 是否使用OCR beta模型
        :param det_beta: 是否使用检测 beta模型
        :param show_ad: 是否显示广告（官方参数）
        """
        try:
            self.ocr = ddddocr.DdddOcr(ocr=True, beta=ocr_beta, show_ad=show_ad)
            self.det = ddddocr.DdddOcr(det=True, beta=det_beta, show_ad=show_ad)
            self.charset_ranges = None  # 字符集限制
            logger.info("CAPTCHA识别器初始化成功")
        except Exception as e:
            logger.error(f"CAPTCHA识别器初始化失败: {e}")
            raise

    def capcode(self, sliding_image, back_image, simple_target=True):
        """
        滑块验证码识别（匹配算法）
        :param sliding_image: 滑块图片
        :param back_image: 背景图片
        :param simple_target: 是否使用简单目标模式
        :return: 目标位置坐标
        """
        try:
            sliding_bytes = get_image_bytes(sliding_image)
            back_bytes = get_image_bytes(back_image)
            res = self.ocr.slide_match(sliding_bytes, back_bytes, simple_target=simple_target)
            if isinstance(res, dict) and 'target' in res:
                return res['target'][0] if isinstance(res['target'], list) else res['target']
            return res
        except Exception as e:
            logger.error(f"滑块识别错误: {e}", exc_info=True)
            return None

    def slide_comparison(self, sliding_image, back_image):
        """
        滑块对比算法（比较算法）
        :param sliding_image: 滑块图片
        :param back_image: 背景图片
        :return: 目标位置坐标
        """
        try:
            sliding_bytes = get_image_bytes(sliding_image)
            back_bytes = get_image_bytes(back_image)
            res = self.ocr.slide_comparison(sliding_bytes, back_bytes)
            if isinstance(res, dict) and 'target' in res:
                return res['target'][0] if isinstance(res['target'], list) else res['target']
            return res
        except Exception as e:
            logger.error(f"滑块对比错误: {e}", exc_info=True)
            return None

    def set_ranges(self, ranges):
        """
        设置字符集范围
        :param ranges: 字符集字符串，如 "0123456789+-x/="
        """
        try:
            self.ocr.set_ranges(ranges)
            self.charset_ranges = ranges
            logger.info(f"字符集范围已设置: {ranges}")
        except Exception as e:
            logger.error(f"设置字符集范围失败: {e}")
            raise

    def classification(self, image, png_fix=False, probability=False, color_filter_colors=None):
        """
        OCR识别函数
        :param image: 图片数据（支持URL、base64、bytes）
        :param png_fix: 是否启用PNG修复（针对某些PNG图片的兼容性修复）
        :param probability: 是否返回识别概率
        :param color_filter_colors: 颜色过滤列表，如 ["red", "blue"] 或自定义HSV范围
        :return: 识别结果（字符串或包含概率的字典）
        """
        try:
            image_bytes = get_image_bytes(image)

            # 应用颜色过滤
            if color_filter_colors:
                image_bytes = self._apply_color_filter(image_bytes, color_filter_colors)

            # 调用OCR识别
            if probability:
                res = self.ocr.classification(image_bytes, probability=True)
                if isinstance(res, dict):
                    return res
                else:
                    # 如果没有返回字典格式，构造一个
                    return {'text': res, 'probability': []}
            else:
                res = self.ocr.classification(image_bytes, png_fix=png_fix)
                return res
        except Exception as e:
            logger.error(f"OCR识别错误: {e}", exc_info=True)
            return None

    def _apply_color_filter(self, image_bytes, colors):
        """
        应用颜色过滤
        :param image_bytes: 图片字节流
        :param colors: 颜色列表或HSV范围
        """
        try:
            # 将字节流转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return image_bytes

            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # 颜色映射表（根据官方文档）
            color_ranges = {
                'red': [(0, 50, 50), (10, 255, 255)],
                'green': [(50, 50, 50), (70, 255, 255)],
                'blue': [(100, 50, 50), (130, 255, 255)],
                'yellow': [(20, 50, 50), (30, 255, 255)],
                'orange': [(10, 50, 50), (20, 255, 255)],
                'purple': [(130, 50, 50), (160, 255, 255)],
                'pink': [(160, 50, 50), (180, 255, 255)],
            }

            # 创建掩码
            mask = np.zeros(img.shape[:2], dtype=np.uint8)

            for color in colors:
                if isinstance(color, list) and len(color) == 2:
                    # 自定义HSV范围
                    lower = np.array(color[0])
                    upper = np.array(color[1])
                elif color in color_ranges:
                    # 预设颜色
                    lower = np.array(color_ranges[color][0])
                    upper = np.array(color_ranges[color][1])
                else:
                    continue

                mask += cv2.inRange(hsv, lower, upper)

            # 应用掩码
            result = cv2.bitwise_and(img, img, mask=mask)

            # 转换回字节流
            _, encoded = cv2.imencode('.png', result)
            return encoded.tobytes()
        except Exception as e:
            logger.warning(f"颜色过滤失败，使用原图: {e}")
            return image_bytes

    def detection(self, image):
        """
        目标检测函数
        :param image: 图片数据
        :return: 检测到的目标位置列表 [[x1,y1,x2,y2], ...]
        """
        try:
            image_bytes = get_image_bytes(image)
            poses = self.det.detection(image_bytes)
            return poses if poses else []
        except Exception as e:
            logger.error(f"目标检测错误: {e}", exc_info=True)
            return None

    def calculate(self, image, charset_ranges=None):
        """
        计算类验证码处理
        :param image: 图片数据
        :param charset_ranges: 字符集限制，如 "0123456789+-x/="
        :return: 计算结果
        """
        try:
            image_bytes = get_image_bytes(image)

            # 如果提供了字符集，先设置
            if charset_ranges:
                self.set_ranges(charset_ranges)

            expression = self.ocr.classification(image_bytes)
            # 清理表达式
            expression = re.sub('=.*$', '', str(expression))
            expression = re.sub(r'[^0-9+\-*/()]', '', expression)

            if not expression:
                raise ValueError("无法识别有效的数学表达式")

            # 安全计算（限制可用的内置函数）
            result = eval(expression, {"__builtins__": {}})
            return result
        except Exception as e:
            logger.error(f"计算验证码错误: {e}", exc_info=True)
            return None

    def crop(self, image, y_coordinate):
        """
        图片分割处理
        :param image: 图片数据
        :param y_coordinate: Y坐标分割点
        :return: 分割后的图片（base64格式）
        """
        try:
            image_bytes = get_image_bytes(image)
            image = Image.open(BytesIO(image_bytes))
            # 分割图片
            upper_half = image.crop((0, 0, image.width, y_coordinate))
            lower_half = image.crop((0, y_coordinate * 2, image.width, image.height))
            # 将分割后的图片转换为Base64编码
            slidingImage = image_to_base64(upper_half)
            backImage = image_to_base64(lower_half)
            return {'slidingImage': slidingImage, 'backImage': backImage}
        except Exception as e:
            logger.error(f"图片分割错误: {e}", exc_info=True)
            return None

    def select(self, image):
        """
        点选验证码处理
        :param image: 图片数据
        :return: 识别结果和坐标的列表
        """
        try:
            image_bytes = get_image_bytes(image)
            # 将二进制数据转换为 numpy 数组
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            # 使用 cv2.imdecode 将 numpy 数组解码为图像
            im = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if im is None:
                raise ValueError("无法解码图片数据")

            bboxes = self.det.detection(image_bytes)
            result_list = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cropped_image = im[y1:y2, x1:x2]
                # 将图像编码为内存中的字节流（如png格式）
                _, buffer = cv2.imencode('.png', cropped_image)
                # 将字节流转换为 Base64 编码
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                result = self.ocr.classification(image_base64)
                result_list.append({'text': result, 'bbox': bbox})

            return result_list
        except Exception as e:
            logger.error(f"点选验证码错误: {e}", exc_info=True)
            return None
