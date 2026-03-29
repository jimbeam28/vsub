# vsub

视频字幕生成工具 - 将视频导出音频，使用 faster-whisper 进行语音转文字，生成标准字幕文件（SRT/VTT）。

## 项目概述

vsub 采用 **Rust + Python** 混合架构：

- **Rust**: 负责 CLI、视频/音频处理、字幕格式化、配置管理
- **Python**: 负责 faster-whisper ASR 推理

## 快速开始

### 安装依赖

```bash
# 1. 安装 FFmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# 2. 安装 Python 依赖
pip install -r python/requirements.txt

# 3. 构建项目
cargo build --release
```

### 使用方法

```bash
# 基本用法
./target/release/vsub input.mp4

# 指定语言
./target/release/vsub input.mp4 -l zh

# 指定输出文件
./target/release/vsub input.mp4 -o output.srt

# 使用配置文件
./target/release/vsub input.mp4 -c config.toml
```

## 系统要求

- **操作系统**: Linux / macOS / Windows
- **内存**: 8GB+ 推荐（取决于模型大小）
- **Python**: 3.8+
- **FFmpeg**: 需系统安装

## 文档

- [架构设计](docs/architecture.md)
- [模块职责](docs/modules.md)
- [CLI 接口](docs/cli.md)
- [配置说明](docs/config.md)
- [开发计划](docs/development.md)

## 项目结构

```
vsub/
├── src/           # Rust 源代码
├── python/        # Python ASR 引擎
├── tests/         # 测试文件
├── docs/          # 文档
└── config.toml    # 配置文件
```

## 许可证

MIT License
# vsub
