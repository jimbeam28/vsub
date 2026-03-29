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

## 文档

- [开发计划](docs/development.md)
- [架构设计](docs/architecture.md)
- [配置说明](docs/config.md)

## 许可证

MIT License
