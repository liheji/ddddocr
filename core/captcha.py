"""
CAPTCHA 核心识别类
"""
import logging
import re
import threading
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import cv2
import ddddocr
import numpy as np
from PIL import Image
from simpleeval import simple_eval

from const.charset import CharsetRange
from const.color import split_color_filters
from const.mode import Mode
from utils.image import image_to_base64

logger = logging.getLogger(__name__)


class FeatureDisabledError(RuntimeError):
    """当前启动模式下未加载对应功能（如 det 模式下调用 OCR）"""


class CAPTCHA:
    """验证码识别核心类"""

    def __init__(self, mode: Mode = Mode.BOTH, show_ad: bool = False,
                 use_gpu: bool = False, device_id: int = 0) -> None:
        """
        初始化识别器
        :param mode: 启动模式（Mode 枚举）：OCR=仅OCR，DET=仅目标检测，BOTH=两者都加载（默认）
        :param show_ad: 是否显示广告（官方参数）
        :param use_gpu: 是否使用GPU加速
        :param device_id: GPU设备ID
        """
        if not isinstance(mode, Mode):
            raise ValueError(f"mode 必须是 Mode 枚举（ocr/det/both），当前: {mode}")
        self.mode: Mode = mode
        try:
            self.ocr: Optional[ddddocr.DdddOcr] = None
            self.det: Optional[ddddocr.DdddOcr] = None
            if mode in (Mode.OCR, Mode.BOTH):
                self.ocr = ddddocr.DdddOcr(
                    ocr=True, det=False,
                    use_gpu=use_gpu, device_id=device_id, show_ad=show_ad,
                )
            if mode in (Mode.DET, Mode.BOTH):
                self.det = ddddocr.DdddOcr(
                    ocr=False, det=True,
                    use_gpu=use_gpu, device_id=device_id, show_ad=show_ad,
                )
            self.charset_range: Optional[CharsetRange] = None  # 全局字符集限制（/set_ranges 设置）
            # 字符集状态由全局实例共享，用锁保证"设置-识别-恢复"的原子性
            self._charset_lock: threading.RLock = threading.RLock()
            logger.info(f"CAPTCHA识别器初始化成功，启动模式: {mode}")
        except Exception as e:
            logger.error(f"CAPTCHA识别器初始化失败: {e}")
            raise

    def _require_ocr(self) -> None:
        """OCR 功能未加载时抛出明确错误（当前为 det 模式）"""
        if self.ocr is None:
            raise FeatureDisabledError("OCR 功能未启用（当前启动模式: det）")

    def _require_det(self) -> None:
        """目标检测功能未加载时抛出明确错误（当前为 ocr 模式）"""
        if self.det is None:
            raise FeatureDisabledError("目标检测功能未启用（当前启动模式: ocr）")

    def _slide_engine(self) -> ddddocr.DdddOcr:
        """滑块引擎在 ocr/det/both 模式下都可用，任取一个已加载实例"""
        engine = self.ocr or self.det
        if engine is None:
            raise RuntimeError("识别器未初始化")
        return engine

    def _charset_manager(self) -> Any:
        """访问 ddddocr 内部的字符集管理器（1.6.1 模块化结构）"""
        self._require_ocr()
        return self.ocr.ocr_engine.charset_manager

    def _save_charset_state(self) -> Tuple[List[str], List[int]]:
        mgr = self._charset_manager()
        return list(mgr.charset_range), list(mgr.valid_charset_range_index)

    def _restore_charset_state(self, state: Tuple[List[str], List[int]]) -> None:
        mgr = self._charset_manager()
        mgr.charset_range = state[0]
        mgr.valid_charset_range_index = state[1]

    def _apply_ranges(self, ranges: str) -> None:
        try:
            self.ocr.set_ranges(ranges)
        except Exception as e:
            raise ValueError(f"字符集范围无效: {e}") from e

    def _classify(self, image_bytes: bytes, png_fix: bool, probability: bool,
                  preset_colors: Optional[List[str]], custom_ranges: Optional[list]) -> Any:
        """调用库原生 classification（颜色过滤由库完成）"""
        try:
            res = self.ocr.classification(
                image_bytes,
                png_fix=png_fix,
                probability=probability,
                color_filter_colors=preset_colors,
                color_filter_custom_ranges=custom_ranges,
            )
        except Exception as e:
            logger.error(f"OCR识别错误: {e}", exc_info=True)
            return None
        if probability and isinstance(res, str):
            # 兼容库在概率模式下返回纯文本的情况，构造与库一致的返回结构
            return {
                'text': res,
                'probabilities': [],
                'charset': self.get_charset(),
                'confidence': None,
            }
        return res

    def _run_with_charset(self, charset_range: Optional[CharsetRange], image_bytes: bytes,
                          action: Callable[[bytes], Any]) -> Any:
        """
        在字符集锁保护下执行识别动作：
        - 涉及字符集（本次请求或全局）时：临时设置 -> 执行 -> 恢复，不污染全局状态；
        - 未涉及字符集时同样持锁，防止与 set_ranges 并发读到字符集管理器中间状态。
        """
        if charset_range is not None and not isinstance(charset_range, CharsetRange):
            raise ValueError("字符集仅支持内置索引 0-7，不接受自定义字符集字符串或列表")
        with self._charset_lock:
            if charset_range is not None or self.charset_range is not None:
                saved = self._save_charset_state()
                try:
                    charset_range = charset_range if charset_range is not None else self.charset_range
                    self._apply_ranges(charset_range.charset)
                    return action(image_bytes)
                finally:
                    self._restore_charset_state(saved)
            return action(image_bytes)

    @staticmethod
    def _extract_target(res: Any) -> Any:
        """兼容库返回 dict（含 target）或直接坐标两种形态，提取缺口中心 x 坐标"""
        if isinstance(res, dict) and 'target' in res:
            return res['target'][0] if isinstance(res['target'], list) else res['target']
        return res

    def capcode(self, sliding_image: bytes, back_image: bytes,
                simple_target: bool = True) -> Any:
        """
        滑块验证码识别（匹配算法）
        :param sliding_image: 滑块图片（bytes）
        :param back_image: 背景图片（bytes）
        :param simple_target: 是否使用简单目标模式
        :return: 目标位置坐标
        """
        try:
            res = self._slide_engine().slide_match(
                sliding_image, back_image, simple_target=simple_target
            )
            return self._extract_target(res)
        except Exception as e:
            logger.error(f"滑块识别错误: {e}", exc_info=True)
            return None

    def slide_comparison(self, sliding_image: bytes, back_image: bytes) -> Any:
        """
        滑块对比算法（比较算法）
        :param sliding_image: 滑块图片（bytes）
        :param back_image: 背景图片（bytes）
        :return: 目标位置坐标
        """
        try:
            res = self._slide_engine().slide_comparison(sliding_image, back_image)
            return self._extract_target(res)
        except Exception as e:
            logger.error(f"滑块对比错误: {e}", exc_info=True)
            return None

    def set_ranges(self, charset_range: CharsetRange) -> None:
        """
        设置全局字符集范围
        :param charset_range: CharsetRange 枚举（内置索引 0-7）
        """
        self._require_ocr()
        if not isinstance(charset_range, CharsetRange):
            raise ValueError("字符集仅支持内置索引 0-7，不接受自定义字符集字符串或列表")
        with self._charset_lock:
            self._apply_ranges(charset_range.charset)
            self.charset_range = charset_range
            logger.info(f"字符集范围已设置: {charset_range}")

    def clear_ranges(self) -> None:
        """清除全局字符集范围，恢复完整字符集"""
        self._require_ocr()
        with self._charset_lock:
            self.charset_range = None
            mgr = self._charset_manager()
            mgr.charset_range = []
            mgr._update_valid_indices()
            logger.info("字符集范围已清除")

    def classification(self, image: bytes, png_fix: bool = False, probability: bool = False,
                       color_filter_colors: Optional[list] = None,
                       charset_range: Optional[CharsetRange] = None) -> Any:
        """
        OCR识别函数
        :param image: 图片字节（bytes）
        :param png_fix: 是否启用PNG修复（针对某些PNG图片的兼容性修复）
        :param probability: 是否返回识别概率
        :param color_filter_colors: 归一化后的颜色过滤参数（ColorPreset 或自定义HSV范围）
        :param charset_range: 本次请求的字符集限制（不污染全局状态），CharsetRange 枚举
        :return: 识别结果（字符串或包含概率的字典）
        """
        self._require_ocr()
        preset_colors, custom_ranges = split_color_filters(color_filter_colors)
        return self._run_with_charset(
            charset_range, image,
            lambda b: self._classify(b, png_fix, probability, preset_colors, custom_ranges),
        )

    def detection(self, image: bytes) -> Optional[List[List[int]]]:
        """
        目标检测函数
        :param image: 图片字节（bytes）
        :return: 检测到的目标位置列表 [[x1,y1,x2,y2], ...]
        """
        self._require_det()
        try:
            poses = self.det.detection(image)
            return poses or []
        except Exception as e:
            logger.error(f"目标检测错误: {e}", exc_info=True)
            return None

    def calculate(self, image: bytes,
                  charset_range: Optional[CharsetRange] = None) -> Optional[Union[int, float]]:
        """
        计算类验证码处理
        :param image: 图片字节（bytes）
        :param charset_range: 字符集限制（CharsetRange 枚举）
        :return: 计算结果
        """
        self._require_ocr()
        return self._run_with_charset(
            charset_range, image, self._calculate_expression
        )

    def _calculate_expression(self, image_bytes: bytes) -> Optional[Union[int, float]]:
        try:
            expression = self.ocr.classification(image_bytes)
            # 清理表达式：去掉 "=" 及等号后的内容，再剔除非法字符
            expression = re.sub('=.*$', '', str(expression))
            expression = re.sub(r'[^0-9+\-*/()]', '', expression)
            if not expression or len(expression) > 64:
                raise ValueError("无法识别有效的数学表达式")
            result = simple_eval(expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            logger.info(f"计算验证码: {expression} = {result}")
            return result
        except Exception as e:
            logger.error(f"计算验证码错误: {e}", exc_info=True)
            return None

    def crop(self, image: bytes, y_coordinate: int) -> Optional[Dict[str, str]]:
        """
        图片分割处理
        :param image: 图片字节（bytes）
        :param y_coordinate: Y坐标分割点
        :return: 分割后的图片（base64格式）
        """
        try:
            img = Image.open(BytesIO(image))
            y_coordinate = int(y_coordinate)
            if not (0 < y_coordinate < img.height):
                raise ValueError(f"y_coordinate 必须在 (0, {img.height}) 之间")
            upper_half = img.crop((0, 0, img.width, y_coordinate))
            lower_half = img.crop((0, y_coordinate, img.width, img.height))
            sliding_image = image_to_base64(upper_half)
            back_image = image_to_base64(lower_half)
            return {'slidingImage': sliding_image, 'backImage': back_image}
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"图片分割错误: {e}", exc_info=True)
            return None

    def select(self, image: bytes) -> Optional[List[Dict[str, Any]]]:
        """
        点选验证码处理
        :param image: 图片字节（bytes）
        :return: 识别结果和坐标的列表
        """
        self._require_det()
        self._require_ocr()
        try:
            image_array = np.frombuffer(image, dtype=np.uint8)
            im = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if im is None:
                raise ValueError("无法解码图片数据")

            bboxes = self.det.detection(image)
            result_list = []
            for bbox in bboxes:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                # 裁剪区域边界保护
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(im.shape[1], x2), min(im.shape[0], y2)
                if x2 <= x1 or y2 <= y1:
                    continue
                cropped_image = im[y1:y2, x1:x2]
                _, buffer = cv2.imencode('.png', cropped_image)
                result = self.ocr.classification(buffer.tobytes())
                result_list.append({'text': result, 'bbox': [x1, y1, x2, y2]})

            return result_list
        except Exception as e:
            logger.error(f"点选验证码错误: {e}", exc_info=True)
            return None

    def get_charset(self) -> List[str]:
        """获取当前 OCR 字符集列表"""
        self._require_ocr()
        return self.ocr.get_charset()
