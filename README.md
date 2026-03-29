# vsub

视频字幕生成工具 - 将视频导出音频，使用语音识别进行文字转录，生成标准字幕文件（SRT/VTT）。

## 特性

- 🎯 **简单易用**: 一行命令生成字幕
- 🌍 **跨平台**: 支持 Linux、macOS、Windows
- ⚡ **高效识别**: 基于 faster-whisper，支持 GPU 加速
- 📝 **标准格式**: 输出 SRT/VTT 标准字幕格式
- 🔧 **可配置**: 支持配置文件和命令行参数

## 快速开始

### 安装

```bash
# 1. 安装 FFmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows: 下载 https://ffmpeg.org/download.html 并添加到 PATH

# 2. 安装 vsub
pip install vsub
```

### 使用方法

```bash
# 基本用法
vsub input.mp4

# 指定语言
vsub input.mp4 -l zh

# 指定输出文件
vsub input.mp4 -o output.srt

# 使用不同模型
vsub input.mp4 -m medium

# 显示详细日志
vsub input.mp4 -v

# 批量处理
vsub *.mp4
```

### 配置文件

生成默认配置文件：

```bash
vsub --init
```

编辑 `vsub.yaml`：

```yaml
# 输出格式: srt 或 vtt
format: srt

# Whisper 模型: tiny, base, small, medium, large
model: base

# 语言代码 (如 zh, en，留空自动检测)
language: zh

# 保留临时音频文件
keep_audio: false

# 强制覆盖输出文件
overwrite: false

# 字幕最大行长度
max_line_length: 80

# 字幕每行最大单词数
max_line_count: 2
```

## 系统要求

- **操作系统**: Linux / macOS / Windows
- **内存**: 8GB+ 推荐（取决于模型大小）
- **Python**: 3.8+
- **FFmpeg**: 需系统安装

## 跨平台支持

| 平台 | 支持状态 | GPU 加速 |
|------|----------|----------|
| Linux | ✅ 完整支持 | CUDA |
| macOS | ✅ 完整支持 | Metal (M1/M2) |
| Windows | ✅ 完整支持 | CUDA |
| WSL | ✅ 完整支持 | CUDA |

## 开发

### 安装开发依赖

```bash
git clone https://github.com/jimbeam28/vsub.git
cd vsub
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 显示详细输出
pytest -v

# 代码覆盖率
pytest --cov=vsub --cov-report=html
```

### 代码质量

```bash
# 格式化代码
black vsub/ tests/
isort vsub/ tests/

# 类型检查
mypy vsub/

# 代码检查
flake8 vsub/ tests/
```

## 文档

- [开发计划](docs/development.md)
- [架构设计](docs/architecture.md)
- [使用示例](docs/examples.md)
- [常见问题](docs/faq.md)
- [配置说明](docs/config.md)

## 许可证

MIT License
