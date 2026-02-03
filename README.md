<h1 align="center">DocParse</h1>

<p align="center" style="color: #888; font-size: 0.95em; margin-top: -0.5em; margin-bottom: 0.5em;">
  <a href="README_EN.md">English</a> | <b>中文</b>
</p>

一个简单的文档解析工具，支持多服务商 OCR，可提取 PDF、图片等格式文档中的文本内容。

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/waynexucn/docParse.git
cd docParse

# 安装依赖
uv sync
```

### 安装构建包

```bash
# 下载或构建 wheel 包
uv build

# 安装 wheel 包
uv pip install dist/docparse-0.1.0-py3-none-any.whl
```

## 配置

### 配置优先级

配置读取优先级（从高到低）：

1. **命令行参数**：通过 `--api-key`、`--model` 等选项指定的参数
2. **配置文件**：`~/.config/docparse/config`（自动创建示例文件）
3. **项目配置**：项目根目录的 `.env` 文件
4. **环境变量**：系统环境变量
5. **默认值**：程序内置的默认配置

### 从源码运行

复制 `.env.example` 为 `.env`，填入 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# SiliconFlow API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# 应用配置（可选）
OUTPUT_DIR=output
# 请求超时时间（秒），留空或注释掉表示无限制
# REQUEST_TIMEOUT=120
```

### 安装包后配置

安装 wheel 包后，推荐使用配置文件进行配置（配置文件优先于环境变量）：

**macOS / Linux:**

```bash
# 创建配置文件
mkdir -p ~/.config/docparse
touch ~/.config/docparse/config

# 编辑配置文件
nano ~/.config/docparse/config
```

首次运行会自动创建 `.env.example` 示例文件。

添加以下内容：

```env
# SiliconFlow API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# 应用配置（可选）
OUTPUT_DIR=output
# 请求超时时间（秒），留空或注释掉表示无限制
# REQUEST_TIMEOUT=120
```

**Windows (PowerShell):**

```powershell
# 创建配置目录和文件
New-Item -ItemType Directory -Path "$env:APPDATA\docparse" -Force
New-Item -ItemType File -Path "$env:APPDATA\docparse\config" -Force

# 编辑配置文件
notepad $env:APPDATA\docparse\config
```

添加以下内容：

```env
# SiliconFlow API 配置
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# 应用配置（可选）
OUTPUT_DIR=output
# 请求超时时间（秒），留空或注释掉表示无限制
# REQUEST_TIMEOUT=120
```

**备选：使用环境变量**

如果不想使用配置文件，也可以设置环境变量：

**macOS / Linux (bash/zsh):**

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
export SILICONFLOW_API_KEY="your_siliconflow_api_key_here"
export SILICONFLOW_MODEL="PaddlePaddle/PaddleOCR-VL-1.5"
export OPENAI_API_KEY="your_openai_api_key_here"
export OPENAI_MODEL="gpt-4o"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OUTPUT_DIR="output"
export REQUEST_TIMEOUT=120
```

然后执行 `source ~/.bashrc` 或 `source ~/.zshrc` 使配置生效。

**Windows (PowerShell):**

在 PowerShell 配置文件中添加：

```powershell
$env:SILICONFLOW_API_KEY="your_siliconflow_api_key_here"
$env:SILICONFLOW_MODEL="PaddlePaddle/PaddleOCR-VL-1.5"
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:OPENAI_MODEL="gpt-4o"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OUTPUT_DIR="output"
$env:REQUEST_TIMEOUT=120
```

或在命令行中临时设置：

```powershell
$env:SILICONFLOW_API_KEY="your_key"
docparse file document.pdf
```

## 运行

### 从源码运行

```bash
# 方式 1: 使用 uv run
uv run -m docparse.main file document.pdf

# 方式 2: 以开发模式安装后直接运行
docparse file document.pdf
```

### 安装包后运行

```bash
# 直接使用命令
docparse file document.pdf

# 或使用 python -m
python -m docparse.main file document.pdf
```

## 使用

### 处理单个文件

```bash
# 使用默认服务商（默认无超时限制）
docparse file document.pdf

# 指定服务商
docparse file document.pdf --provider openai

# 指定模型
docparse file document.pdf --provider siliconflow --model "your-model"

# 自定义 OpenAI 兼容 API
docparse file document.pdf --provider openai --base-url "https://your-api.com/v1"

# 设置超时时间（秒）
docparse file document.pdf --timeout 120

# 无限制超时（默认行为）
docparse file document.pdf --timeout 0
```

### 批量处理文件

```bash
docparse batch --file file1.png --file file2.jpg --provider siliconflow
```

### 处理目录

```bash
# 处理目录中所有文件
docparse dir ./input

# 处理特定模式文件
docparse dir ./input --pattern "doc_*"
```

### 查看配置

```bash
# 查看所有配置
docparse config --show

# 查看特定服务商配置
docparse config --show-provider siliconflow
docparse config --show-provider openai
```

## 更换模型

### 从源码运行

修改 `.env` 文件中的配置：

**SiliconFlow:**

```env
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5
```

**OpenAI:**

```env
OPENAI_MODEL=gpt-4o
```

或在命令行中指定：

```bash
docparse file document.pdf --provider siliconflow --model "your-model-name"
```

### 安装包后

**推荐：修改配置文件**

**macOS / Linux:**

```bash
nano ~/.config/docparse/config
```

**Windows:**

```powershell
notepad $env:APPDATA\docparse\config
```

修改对应的模型配置：

```env
SILICONFLOW_MODEL=your-model-name
OPENAI_MODEL=your-model-name
```

**备选：修改环境变量**

**macOS / Linux:**

```bash
export SILICONFLOW_MODEL="your-model-name"
export OPENAI_MODEL="your-model-name"
```

**Windows:**

```powershell
$env:SILICONFLOW_MODEL="your-model-name"
$env:OPENAI_MODEL="your-model-name"
```

或在命令行中临时指定：

```bash
docparse file document.pdf --provider siliconflow --model "your-model-name"
```

### 自定义 API

使用 OpenAI 兼容的 API 服务：

```bash
docparse file document.pdf \
  --provider openai \
  --base-url "https://your-api.com/v1" \
  --model "your-model-name"
```

## 支持的文件格式

PDF、PNG、JPG、JPEG、BMP、TIF、TIFF

**PDF 处理说明：**

程序会自动将 PDF 文件转换为图片，逐页处理并合并结果。输出文件会按照页面顺序，使用 Markdown 格式标记每一页：

```markdown
## 第 1 页

[第 1 页的 OCR 内容]

## 第 2 页

[第 2 页的 OCR 内容]

...
```

## 命令选项

| 选项 | 说明 |
|------|------|
| `--provider` | 选择服务商 (siliconflow, openai) |
| `--api-key, -k` | API 密钥 |
| `--model` | 模型名称 |
| `--base-url` | API 基础 URL |
| `--timeout, -t` | 请求超时时间（秒），0 或不指定表示无限制 |
| `--output, -o` | 输出目录 |
| `--prompt, -p` | 自定义提示词 |

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
