# ddddocr API 服务

基于 [ddddocr](https://github.com/sml2h3/ddddocr) 的通用验证码识别 OCR HTTP API 服务，提供简单易用的 RESTful 接口。

## ✨ 特性

- 🚀 **核心功能全覆盖**：覆盖官方 ddddocr 的 OCR/目标检测/滑块/概率输出/字符集能力，仅使用 ddddocr 内置模型，不支持自定义模型导入
- 🎨 **颜色过滤**：透传官方库原生颜色过滤，支持预设颜色和自定义HSV范围
- 📊 **概率输出**：支持返回识别概率信息
- 🔧 **字符集限制**：仅支持内置字符集索引（0-7），且按请求隔离、不污染全局状态
- 📦 **模块化设计**：代码结构清晰，易于维护和扩展
- 🔄 **标准化响应**：统一的JSON响应格式（code、msg、data）
- 📤 **文件上传**：单图接口支持 multipart 文件上传
- 🐳 **Docker支持**：优化的Docker镜像，一键部署
- 🌐 **CORS支持**：支持跨域请求
- 📝 **完善的日志**：详细的错误日志与访问日志（werkzeug 默认输出）
- ⚡ **线程安全**：OCR 识别加锁串行，字符集状态不串扰
- 🛡️ **安全加固**：请求体/图片大小限制、数学表达式白名单计算

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
| MoviePilot兼容 | `/captcha/base64` | POST | 识别base64图片文字（`{"base64_img": "..."}` → `{"result": "文本"}`） |
| 健康检查 | `/` 或 `/health` | GET | 服务运行状态检查 |
| 状态查询 | `/status` | GET | 服务状态、版本与当前OCR字符集信息 |

> 图片类接口（`/classification`、`/detection`、`/calculate`、`/select`、`/capcode`、`/slideComparison`、`/crop`）
> 同时支持 multipart 文件上传（表单字段名与 JSON 字段名一致），无需手动 base64 编码。
> `/crop` 的 `y_coordinate` 也支持表单字段。

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 拉取并运行（使用默认端口7777）
docker run -d \
  -p 7777:7777 \
  --restart=always \
  --name ddddocr \
  ghcr.io/liheji/ddddocr:latest
```

> 镜像内使用 gunicorn（生产级 WSGI 服务器）运行，不会出现 Flask 开发服务器提示。

### 本地部署

```bash
# 克隆项目
git clone https://github.com/your-repo/ddddocr.git
cd ddddocr

# 安装依赖（依赖由 pyproject.toml 管理）
pip install -e .

# 创建日志目录
mkdir -p logs

# 运行服务（默认端口7777）
python app.py

# 注：python app.py 使用 Flask 内置开发服务器，仅适合本地调试；
# 生产环境请使用 Docker 镜像（内部为 gunicorn）。

# 或使用环境变量自定义配置
export PORT=7777
export HOST=0.0.0.0
export MODE=both
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
| `MODE` | 启动模式：`ocr`=仅OCR，`det`=仅目标检测，`both`=两者都加载 | `both` |
| `SHOW_AD` | 显示广告 | `false` |
| `USE_GPU` | 使用GPU加速 | `false` |
| `DEVICE_ID` | GPU设备ID | `0` |
| `MAX_IMAGE_BYTES` | 请求体与单张图片的统一大小上限（字节），base64/URL/bytes均生效 | `16777216`（16MB） |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `logs/app.log` |
| `APP_VERSION` | 服务版本号（默认取自 pyproject.toml，可用环境变量覆盖） | `1.1.0` |

## 📖 API 文档

### 响应格式

除 `/captcha/base64` 兼容接口外，所有API接口统一返回以下JSON格式：

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
  "msg": "错误信息"
}
```

> `data` 为 `null` 时直接省略该字段（如错误响应、清除字符集范围）。

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
  "charset_ranges": 0
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
  - 预设颜色：`["red", "blue", "green", "yellow", "orange", "purple", "cyan", "black", "white", "gray"]`（其他颜色不支持，会返回错误）
  - 自定义HSV范围：`[[[0,50,50],[10,255,255]]]`
- `charset_ranges` (可选): 本次请求的字符集限制，仅支持内置索引 `0-7`（如 `0`=纯数字）。仅对当前请求生效，不会改变全局状态

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": "识别结果文本"
}
```

`probability: true` 时 `data` 为字典，结构与官方库一致：

```json
{
  "text": "识别结果文本",
  "probabilities": [[0.01, 0.02, ...], ...],
  "charset": ["", "0", "1", ...],
  "confidence": 0.98
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
  "charset_ranges": 0
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
- `y_coordinate` (必需): Y坐标分割线，上半部分为 `0..y`，下半部分为 `y..图片高度`

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
  "ranges": 0
}
```

`ranges` 仅支持内置字符集索引（简称）：
- `0`=纯数字，`1`=纯小写，`2`=纯大写，`3`=大小写，`4`=小写+数字，`5`=大写+数字，`6`=大小写+数字，`7`=默认字符库

不接受自定义字符集字符串或列表（如 `"0123456789+-x/="` 会返回 400）。

传 `null` 可清除已设置的全局字符集限制。

**响应示例：**

```json
{
  "code": 0,
  "msg": "字符集范围设置成功",
  "data": 0
}
```

### 9. MoviePilot 兼容接口：`/captcha/base64`

为 [MoviePilot](https://github.com/jxxghp/MoviePilot) 等现有调用方提供的兼容端点，
参数与响应完全对齐其 `OcrHelper` 的使用方式：

**接口地址：** `POST /captcha/base64`

**请求参数：**

```json
{
  "base64_img": "图片base64字符串"
}
```

**成功响应（HTTP 200）：**

```json
{
  "result": "识别结果文本"
}
```

**错误响应（HTTP 400/500/503）：**

```json
{
  "result": null
}
```

调用方通过 `resp.json().get("result")` 取值，失败时 HTTP 状态码 ≥ 400，
调用方会将结果视为空字符串。

### 10. 健康检查与状态

**接口地址：** `GET /` 或 `GET /health`（健康检查）；`GET /status`（状态查询）

`/status` 在健康检查基础上合并了原 `/charset` 接口的字符集信息：

**`/health` 响应示例：**

```json
{
  "code": 0,
  "msg": "API运行成功！",
  "data": {
    "status": "running",
    "version": "1.1.0"
  }
}
```

**`/status` 响应示例：**

```json
{
  "code": 0,
  "msg": "API运行成功！",
  "data": {
    "status": "running",
    "version": "1.1.0",
    "charset": ["", "0", "1", ...],
    "ranges": null
  }
}
```

> `MODE=det`（仅目标检测）时 `/status` 仅返回 `status` 与 `version`，不包含字符集信息。

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
docker build -t ghcr.io/liheji/ddddocr .

# 运行容器（默认端口7777）
docker run -d -p 7777:7777 --name ddddocr ghcr.io/liheji/ddddocr

# 运行容器（自定义端口）
docker run -d -p 8888:8888 -e PORT=8888 --name ddddocr ghcr.io/liheji/ddddocr

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
├── pyproject.toml     # 项目元数据与依赖管理
├── LICENSE            # MIT 开源协议
├── Dockerfile         # Docker镜像构建文件
├── README.md          # 项目说明文档
├── build.sh           # 构建脚本
├── utils/             # 工具类目录
│   ├── __init__.py
│   ├── response.py    # 标准化响应工具类
│   └── image.py       # 图片处理工具类
├── core/              # 核心功能目录
│   ├── __init__.py
│   └── captcha.py     # CAPTCHA核心识别类
├── api/               # API路由目录
│   ├── __init__.py
│   ├── helpers.py     # 请求参数解析与统一错误响应
│   └── routes.py      # 路由定义
├── const/             # 常量配置目录
│   ├── __init__.py
│   ├── setting.py     # 配置常量
│   ├── errno.py       # 错误码常量
│   ├── charset.py     # 内置字符集与范围归一化
│   └── color.py       # 颜色过滤预设与校验
├── tests/             # pytest 测试套件（真实 ddddocr，无 mock）
└── logs/              # 日志目录
    └── app.log        # 应用日志
```

### 本地开发

```bash
# 安装开发依赖（含 pytest）
pip install -e ".[dev]"

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

### 运行测试

测试基于**真实 ddddocr 模型**与真实生成的验证码图片，不使用任何 mock：

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

覆盖范围：OCR 识别、概率输出、PNG 修复、字符集隔离与内置索引映射、
颜色过滤、滑块两套算法、目标检测、点选、图片分割、计算验证码、
图片大小限制、Flask 全部路由（含文件上传）。

### 代码说明

#### 响应格式

所有API接口使用统一的响应格式类 `R`（位于 `utils/response.py`）：

```python
from const.errno import Errno

# 成功响应
R.ok(data={"result": "success"}).json()

# 错误响应
R.error(Errno.PARAM, msg="参数错误").json()
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
class Errno(IntEnum):
    """统一错误码（code + 默认响应文案）"""
    SUCCESS = (0, "success")
    FAILURE = (1, "failure")
    PARAM = (400, "参数错误")
    UNAUTHORIZED = (401, "未授权")
    FORBIDDEN = (403, "禁止访问")
    NOTFOUND = (404, "接口不存在")
    INTERNAL = (500, "服务器内部错误")
    SERVICE = (503, "服务错误")
```

## 📝 更新日志

### v1.1.0
- 🗑️ 移除所有 beta 配置（`OCR_BETA`/`DET_BETA`），新增 `MODE` 启动模式（`ocr`/`det`/`both`），按需加载模型节省内存
- 🐛 修复 `/crop` 下半部分裁剪坐标错误（`y_coordinate * 2` → `y_coordinate`）
- 🐛 修复 `probability=True` 时 `png_fix` 被忽略的问题
- 🐛 修复字符集状态泄漏与并发串扰：`charset_ranges` 按请求隔离，设置-识别-恢复原子化
- 🐛 修复 `set_ranges` 内置索引（int 0-7）映射，兼容官方 README 语义
- 🐛 移除 `calculate` 的 `eval`，改用 simpleeval 白名单计算，杜绝大数幂 DoS
- 🐛 颜色过滤改为透传官方库原生实现，仅支持库预设颜色，未知预设返回明确错误
- 🛡️ 请求体与图片大小统一限制（`MAX_IMAGE_BYTES`），base64 解码严格校验
- 🗑️ 字符集表与校验抽离到 `const/charset.py`，字符集参数仅接受内置索引 0-7，拒绝自定义字符集
- 🗑️ 颜色过滤预设与校验抽离到 `const/color.py`
- 🗑️ 删除 URL 内网地址黑名单（SSRF）与 `pink` 颜色兼容
- ✅ 单图接口支持 multipart 文件上传；新增 `/captcha/base64`（MoviePilot 兼容）
- 🗑️ 删除 `/charset`、`/config` 接口，字符集信息合并到 `/status`；功能未启用时统一返回 503
- ✅ 支持 `USE_GPU`/`DEVICE_ID` 配置；仅使用 ddddocr 内置模型，禁止自定义模型导入
- ✅ 新增基于真实 ddddocr 的 pytest 测试套件

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
