"""
Flask应用入口文件
"""
import os
import logging
from flask import Flask
from flask_cors import CORS

from api import api_bp, init_routes
from const import (
    APP_VERSION, DEBUG, HOST, LOG_FILE, LOG_LEVEL, MAX_IMAGE_BYTES, PORT,
)
from const.errno import Errno
from utils import R

# 确保日志目录存在，避免首次启动因目录缺失而崩溃
os.makedirs(os.path.dirname(LOG_FILE) or '.', exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 限制请求体大小（与图片大小限制统一为 MAX_IMAGE_BYTES）
app.config['MAX_CONTENT_LENGTH'] = MAX_IMAGE_BYTES

CORS(app)

init_routes()

app.register_blueprint(api_bp)


@app.route('/', methods=['GET'])
def index():
    """根路径健康检查"""
    return R.ok(data={
        'status': 'running',
        'version': APP_VERSION
    }, msg='API运行成功！').json()


@app.errorhandler(413)
def too_large(error):
    return R.error(Errno.PARAM, f'请求体过大，最大 {MAX_IMAGE_BYTES // (1024 * 1024)}MB').json(), 413


@app.errorhandler(404)
def not_found(error):
    return R.error(Errno.NOTFOUND, '接口不存在').json(), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}", exc_info=True)
    return R.error(Errno.INTERNAL, '服务器内部错误').json(), 500


if __name__ == '__main__':
    logger.info(f"启动DDDDOcr API服务，监听地址: {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
