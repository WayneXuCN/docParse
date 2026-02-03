<h1 align="center">DocParse</h1>

<p align="center" style="color: #888; font-size: 0.95em; margin-top: -0.5em; margin-bottom: 0.5em;">
  <a href="README.md">中文</a> | <b>English</b>
</p>

A simple document parsing tool that supports multi-provider OCR for extracting text from PDFs, images, and other document formats.

## Installation

### Install from Source

```bash
# Clone repository
git clone https://github.com/waynexucn/docParse.git
cd docParse

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Install Built Package

```bash
# Download or build wheel package
uv build

# Install wheel package
uv pip install dist/docparse-0.1.0-py3-none-any.whl
```

## Configuration

### Running from Source

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` file:

```env
# SiliconFlow API configuration
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# Application configuration (optional)
OUTPUT_DIR=output
```

### After Installing Package

After installing the wheel package, it's recommended to use a configuration file (configuration file takes precedence over environment variables):

**macOS / Linux:**

```bash
# Create configuration file
mkdir -p ~/.config/docparse
touch ~/.config/docparse/config

# Edit configuration file
nano ~/.config/docparse/config
```

Add the following:

```env
# SiliconFlow API configuration
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# Application configuration (optional)
OUTPUT_DIR=output
```

**Windows (PowerShell):**

```powershell
# Create configuration directory and file
New-Item -ItemType Directory -Path "$env:APPDATA\docparse" -Force
New-Item -ItemType File -Path "$env:APPDATA\docparse\config" -Force

# Edit configuration file
notepad $env:APPDATA\docparse\config
```

Add the following:

```env
# SiliconFlow API configuration
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# Application configuration (optional)
OUTPUT_DIR=output
```

**Alternative: Using Environment Variables**

If you prefer not to use a configuration file, you can set environment variables:

**macOS / Linux (bash/zsh):**

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export SILICONFLOW_API_KEY="your_siliconflow_api_key_here"
export SILICONFLOW_MODEL="PaddlePaddle/PaddleOCR-VL-1.5"
export OPENAI_API_KEY="your_openai_api_key_here"
export OPENAI_MODEL="gpt-4o"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OUTPUT_DIR="output"
```

Then run `source ~/.bashrc` or `source ~/.zshrc` to apply changes.

**Windows (PowerShell):**

Add to PowerShell profile:

```powershell
$env:SILICONFLOW_API_KEY="your_siliconflow_api_key_here"
$env:SILICONFLOW_MODEL="PaddlePaddle/PaddleOCR-VL-1.5"
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:OPENAI_MODEL="gpt-4o"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OUTPUT_DIR="output"
```

Or set temporarily in command line:

```powershell
$env:SILICONFLOW_API_KEY="your_key"
docparse file document.pdf
```

## Running

### Running from Source

```bash
# Method 1: Use uv run
uv run -m docparse.main file document.pdf

# Method 2: Direct run after development install
docparse file document.pdf
```

### After Installing Package

```bash
# Use command directly
docparse file document.pdf

# Or use python -m
python -m docparse.main file document.pdf
```

## Usage

### Process Single File

```bash
# Use default provider
docparse file document.pdf

# Specify provider
docparse file document.pdf --provider openai

# Specify model
docparse file document.pdf --provider siliconflow --model "your-model"

# Custom OpenAI-compatible API
docparse file document.pdf --provider openai --base-url "https://your-api.com/v1"
```

### Batch Process Files

```bash
docparse batch --file file1.png --file file2.jpg --provider siliconflow
```

### Process Directory

```bash
# Process all files in directory
docparse dir ./input

# Process files matching pattern
docparse dir ./input --pattern "doc_*"
```

### View Configuration

```bash
# View all configuration
docparse config --show

# View specific provider configuration
docparse config --show-provider siliconflow
docparse config --show-provider openai
```

## Changing Models

### Running from Source

Edit `.env` file:

**SiliconFlow:**
```env
SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5
```

**OpenAI:**
```env
OPENAI_MODEL=gpt-4o
```

Or specify via command line:

```bash
docparse file document.pdf --provider siliconflow --model "your-model-name"
```

### After Installing Package

**Recommended: Edit Configuration File**

**macOS / Linux:**
```bash
nano ~/.config/docparse/config
```

**Windows:**
```powershell
notepad $env:APPDATA\docparse\config
```

Modify the corresponding model configuration:

```env
SILICONFLOW_MODEL=your-model-name
OPENAI_MODEL=your-model-name
```

**Alternative: Modify Environment Variables**

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

Or specify temporarily:

```bash
docparse file document.pdf --provider siliconflow --model "your-model-name"
```

### Custom API

Use OpenAI-compatible API services:

```bash
docparse file document.pdf \
  --provider openai \
  --base-url "https://your-api.com/v1" \
  --model "your-model-name"
```

## Supported File Formats

PDF, PNG, JPG, JPEG, BMP, TIF, TIFF

## Command Options

| Option | Description |
|--------|-------------|
| `--provider` | Select provider (siliconflow, openai) |
| `--api-key, -k` | API key |
| `--model` | Model name |
| `--base-url` | API base URL |
| `--output, -o` | Output directory |
| `--prompt, -p` | Custom prompt |

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
