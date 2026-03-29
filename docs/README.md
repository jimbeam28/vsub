# vsub

视频字幕生成工具 - 将视频导出音频，使用 faster-whisper 进行语音转文字，生成标准字幕文件（SRT/VTT）。

## 项目概述

vsub 是一个命令行工具，用于自动为视频生成字幕。它采用 Rust + Python 混合架构：

- **Rust**: 负责 CLI、视频/音频处理、字幕格式化、配置管理
- **Python**: 负责 faster-whisper ASR 推理

## 快速开始

```bash
# 安装依赖
pip install -r python/requirements.txt

# 构建项目
cargo build --release

# 生成字幕
./target/release/vsub input.mp4
```

## 系统要求

- **操作系统**: Linux / macOS / Windows
- **内存**: 8GB+ 推荐
- **Python**: 3.8+
- **FFmpeg**: 系统需安装 FFmpeg

## 文档索引

- [架构设计](architecture.md) - 系统整体架构和数据流
- [模块职责](modules.md) - 各模块详细说明
- [CLI 接口](cli.md) - 命令行使用说明
- [配置说明](config.md) - 配置文件详解
- [开发计划](development.md) - 实现阶段规划

## 项目结构

```
vsub/
├── src/
│   ├── main.rs           # CLI 入口
│   ├── lib.rs            # 库入口
│   ├── cli/              # CLI 模块
│   ├── core/             # 核心处理
│   └── asr/              # ASR 桥接
├── python/               # Python ASR 引擎
├── tests/                # 测试文件
└── docs/                 # 文档目录
```

## 许可

MIT License
