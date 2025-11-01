# ddddocr API 服务

基于 [ddddocr](https://github.com/sml2h3/ddddocr) 的通用验证码识别 OCR HTTP API 服务，提供简单易用的 RESTful 接口。

## ✨ 特性

- 🚀 **完整的API支持**：支持官方 ddddocr 的所有功能
- 🎨 **颜色过滤**：支持预设颜色和自定义HSV范围的颜色过滤
- 📊 **概率输出**：支持返回识别概率信息
- 🔧 **字符集限制**：支持自定义字符集范围，提高识别准确率
- 📦 **模块化设计**：代码结构清晰，易于维护和扩展
- 🔄 **标准化响应**：统一的JSON响应格式（code、msg、data）
- 🐳 **Docker支持**：优化的Docker镜像，一键部署
- 🌐 **CORS支持**：支持跨域请求
- 📝 **完善的日志**：详细的错误日志和请求日志
- ⚡ **高性能**：支持并发请求处理

## 📋 功能列表

| 功能 | 接口 | 方法 | 说明 |
|------|------|------|------|
| OCR文字识别 | `/classification` | POST | 支持颜色过滤、PNG修复、概率输出 |
| 目标检测 | `/detection` | POST | 检测图片中文字或图标的坐标位置 |
| 滑块匹配 | `/capcode` | POST | 滑块验证码识别（匹配算法） |
| 滑块对比 | `/slideComparison` | POST | 滑块验证码识别（对比算法） |
| 计算验证码 | `/calculate` | POST | 识别并计算数学表达式结果 |
| 点选验证码 | `/select` | POST | 识别点选验证码的文字和位置 |
| 图片分割 | `/crop` | POST | 将图片分割为多个部分 |
| 字符集设置 | `/set_ranges` | POST | 设置OCR识别的字符集范围 |
| 健康检查 | `/` 或 `/health` 或 `/status` | GET | 服务运行状态检查 |

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 拉取并运行（使用默认端口7777）
docker run -d \
  -p 7777:7777 \
  --restart=always \
  --name ddddocr \
  yilee01/ddddocr:latest
```

### 本地部署

```bash
# 克隆项目
git clone https://github.com/your-repo/ddddocr.git
cd ddddocr

# 安装依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 运行服务（默认端口7777）
python app.py

# 或使用环境变量自定义配置
export PORT=7777
export HOST=0.0.0.0
export OCR_BETA=true
python app.py

# Windows PowerShell
$env:PORT=7777
$env:HOST="0.0.0.0"
python app.py
```

### 环境变量配置

所有配置通过环境变量进行设置，配置文件位于 `const/setting.py`：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PORT` | 服务端口 | `7777` |
| `HOST` | 监听地址 | `0.0.0.0` |
| `DEBUG` | 调试模式 | `false` |
| `OCR_BETA` | 使用OCR beta模型 | `true` |
| `DET_BETA` | 使用检测beta模型 | `true` |
| `SHOW_AD` | 显示广告 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `logs/app.log` |

## 📖 API 文档

### 响应格式

所有API接口统一返回以下JSON格式：

**成功响应：**
```json
{
  "code": 0,
  "msg": "success",
  "data": {...}
}
```

**错误响应：**
```json
{
  "code": 400,
  "msg": "错误信息",
  "data": null
}
```

### 错误码说明

错误码定义在 `const/errno.py`：

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 失败 |
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 未找到 |
| 500 | 内部服务器错误 |
| 503 | 服务错误 |

### 1. OCR文字识别

**接口地址：** `POST /classification`

**请求参数：**

```json
{
  "image": "图片数据（base64字符串或URL）",
  "png_fix": false,
  "probability": false,
  "color_filter_colors": ["red", "blue"],
  "charset_ranges": "0123456789+-x/="
}
```

**参数说明：**
- `image` (必需): 图片数据，支持格式：
  - Base64编码字符串
  - Data URI格式（`data:image/png;base64,...`）
  - 图片URL地址
- `png_fix` (可选): 是否启用PNG修复，默认 `false`
- `probability` (可选): 是否返回识别概率，默认 `false`
- `color_filter_colors` (可选): 颜色过滤列表
  - 预设颜色：`["red", "blue", "green", "yellow", "orange", "purple", "pink"]`
  - 自定义HSV范围：`[[[0,50,50],[10,255,255]]]`
- `charset_ranges` (可选): 字符集限制，如 `"0123456789+-x/="`

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": "识别结果文本"
}
```

### 2. 目标检测

**接口地址：** `POST /detection`

**请求参数：**

```json
{
  "image": "图片数据（base64字符串或URL）"
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    [x1, y1, x2, y2],
    [x1, y1, x2, y2]
  ]
}
```

### 3. 滑块验证码识别（匹配算法）

**接口地址：** `POST /capcode`

**请求参数：**

```json
{
  "slidingImage": "滑块图片",
  "backImage": "背景图片",
  "simpleTarget": true
}
```

**参数说明：**
- `slidingImage` (必需): 滑块图片，支持base64或URL
- `backImage` (必需): 背景图片，支持base64或URL
- `simpleTarget` (可选): 是否使用简单目标模式，默认 `true`

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": 150
}
```

### 4. 滑块验证码识别（对比算法）

**接口地址：** `POST /slideComparison`

**请求参数：**

```json
{
  "slidingImage": "滑块图片",
  "backImage": "背景图片"
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": 150
}
```

### 5. 计算验证码

**接口地址：** `POST /calculate`

**请求参数：**

```json
{
  "image": "图片数据",
  "charset_ranges": "0123456789+-x/="
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": 42
}
```

### 6. 点选验证码

**接口地址：** `POST /select`

**请求参数：**

```json
{
  "image": "图片数据"
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "text": "识别文字",
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

### 7. 图片分割

**接口地址：** `POST /crop`

**请求参数：**

```json
{
  "image": "图片数据",
  "y_coordinate": 150
}
```

**参数说明：**
- `image` (必需): 图片数据
- `y_coordinate` (必需): Y坐标分割点

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "slidingImage": "base64编码的上半部分图片",
    "backImage": "base64编码的下半部分图片"
  }
}
```

### 8. 设置字符集范围

**接口地址：** `POST /set_ranges`

**请求参数：**

```json
{
  "ranges": "0123456789+-x/="
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "字符集范围设置成功",
  "data": "0123456789+-x/="
}
```

### 9. 健康检查

**接口地址：** `GET /` 或 `GET /health` 或 `GET /status`

**响应示例：**

```json
{
  "code": 0,
  "msg": "API运行成功！",
  "data": {
    "status": "running",
    "version": "1.0.0"
  }
}
```

## 💡 使用示例

### Python 示例

```python
import requests
import base64

# 读取图片并转换为base64
with open("captcha.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# OCR识别
response = requests.post(
    "http://localhost:7777/classification",
    json={
        "image": image_data,
        "color_filter_colors": ["red", "blue"],
        "probability": False
    }
)
result = response.json()
if result["code"] == 0:
    print(f"识别结果: {result['data']}")
else:
    print(f"错误: {result['msg']}")

# 滑块验证码
with open("sliding.png", "rb") as f:
    sliding_image = base64.b64encode(f.read()).decode()
with open("back.png", "rb") as f:
    back_image = base64.b64encode(f.read()).decode()

response = requests.post(
    "http://localhost:7777/capcode",
    json={
        "slidingImage": sliding_image,
        "backImage": back_image,
        "simpleTarget": True
    }
)
result = response.json()
if result["code"] == 0:
    print(f"滑块位置: {result['data']}")
else:
    print(f"错误: {result['msg']}")
```

### JavaScript 示例

```javascript
// OCR识别
async function recognizeCaptcha(imageBase64) {
  const response = await fetch('http://localhost:7777/classification', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: imageBase64,
      color_filter_colors: ['red', 'blue'],
      probability: false
    })
  });
  
  const result = await response.json();
  if (result.code === 0) {
    return result.data;
  } else {
    throw new Error(result.msg);
  }
}
```

### cURL 示例

```bash
# OCR识别
curl -X POST http://localhost:7777/classification \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image_data",
    "color_filter_colors": ["red", "blue"]
  }'

# 滑块验证码
curl -X POST http://localhost:7777/capcode \
  -H "Content-Type: application/json" \
  -d '{
    "slidingImage": "base64_encoded_sliding_image",
    "backImage": "base64_encoded_back_image"
  }'

# 健康检查
curl http://localhost:7777/health
```

## 🐳 Docker 构建

```bash
# 构建镜像
docker build -t yilee01/ddddocr .

# 运行容器（默认端口7777）
docker run -d -p 7777:7777 --name ddddocr yilee01/ddddocr

# 运行容器（自定义端口）
docker run -d -p 8888:8888 -e PORT=8888 --name ddddocr yilee01/ddddocr

# 查看日志
docker logs -f ddddocr

# 停止容器
docker stop ddddocr

# 删除容器
docker rm ddddocr
```

## 🔧 开发

### 项目结构

```
ddddocr/
├── app.py             # Flask应用入口文件
├── requirements.txt   # Python依赖
├── Dockerfile         # Docker镜像构建文件
├── README.md          # 项目说明文档
├── build.sh           # 构建脚本
├── utils/             # 工具类目录
│   ├── __init__.py
│   ├── response.py    # 标准化响应工具类
│   └── image_utils.py # 图片处理工具类
├── core/              # 核心功能目录
│   ├── __init__.py
│   └── captcha.py     # CAPTCHA核心识别类
├── api/               # API路由目录
│   ├── __init__.py
│   └── routes.py      # 路由定义
├── const/             # 常量配置目录
│   ├── __init__.py
│   ├── setting.py     # 配置常量
│   └── errno.py       # 错误码常量
└── logs/              # 日志目录
    └── app.log        # 应用日志
```

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 运行服务（开发模式）
export DEBUG=true
export PORT=7777
python app.py

# Windows PowerShell
$env:DEBUG="true"
$env:PORT="7777"
python app.py
```

### 代码说明

#### 响应格式

所有API接口使用统一的响应格式类 `R`（位于 `utils/response.py`）：

```python
# 成功响应
R.ok(data={"result": "success"}).json()

# 错误响应
R.error(code=400, msg="参数错误").json()
```

#### 配置管理

配置通过环境变量管理，配置常量定义在 `const/setting.py`：

```python
# 读取环境变量，如果没有则使用默认值
PORT = int(os.getenv('PORT', 7777))
HOST = os.getenv('HOST', '0.0.0.0')
```

#### 错误码定义

错误码定义在 `const/errno.py`：

```python
SUCCESS = 0
FAILURE = 1
PARAM_ERROR = 400
NOT_FOUND = 404
INTERNAL_ERROR = 500
SERVICE_ERROR = 503
```

## 📝 更新日志

### v1.0.0
- ✅ **模块化重构**：拆分代码为多个模块，结构更清晰
- ✅ **标准化响应**：统一JSON响应格式（code、msg、data）
- ✅ 完善所有API接口功能
- ✅ 支持颜色过滤功能
- ✅ 支持概率输出
- ✅ 支持字符集限制
- ✅ 优化Docker镜像
- ✅ 完善错误处理和日志
- ✅ 添加CORS支持

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 🙏 致谢

- [ddddocr](https://github.com/sml2h3/ddddocr) - 强大的OCR识别库

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
