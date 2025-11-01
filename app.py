"""
Flask应用入口文件
"""
import os
import logging
from flask import Flask
from flask_cors import CORS

from api import api_bp, init_routes
from const import *
from utils import R

# 设置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 允许跨域请求
CORS(app)

# 初始化路由
init_routes()

# 注册蓝图
app.register_blueprint(api_bp)


# 根路径健康检查
@app.route('/', methods=['GET'])
def index():
    """根路径健康检查"""
    return R.ok(data={
        'status': 'running',
        'version': '1.0.0'
    }, msg='API运行成功！').json()


# 错误处理
@app.errorhandler(404)
def not_found(error):
    return R.error(NOT_FOUND, '接口不存在').json(), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}", exc_info=True)
    return R.error(INTERNAL_ERROR, '服务器内部错误').json(), 500


# 启动应用
if __name__ == '__main__':
    logger.info(f"启动DDDDOcr API服务，监听地址: {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
