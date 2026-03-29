# 开发计划

## 概述

vsub 是一款视频字幕生成工具，将视频导出音频后进行语音识别，生成标准字幕文件（SRT/VTT）。

## Phase 1: 基础框架

**目标**: 搭建项目结构，实现基本 CLI 和配置系统

### 任务清单

- [ ] 项目初始化
  - [ ] 创建项目目录结构
  - [ ] 配置依赖管理
  - [ ] 添加 CLI、配置、日志相关依赖

- [ ] 实现配置系统
  - [ ] 定义配置数据结构
  - [ ] 实现从文件加载配置
  - [ ] 实现默认配置
  - [ ] 实现配置合并（文件 + 命令行）

- [ ] 实现 CLI 参数解析
  - [ ] 定义 CLI 接口
  - [ ] 实现 --help, --version
  - [ ] 参数验证

- [ ] 日志和错误处理
  - [ ] 设置日志系统
  - [ ] 定义错误类型
  - [ ] 友好的错误显示

### 验收标准

```bash
$ vsub --help
$ vsub --version
$ vsub input.mp4  # 显示"功能未实现"
```

## Phase 2: 核心功能

**目标**: 实现视频处理、音频提取、ASR 识别、字幕生成

### 任务清单

- [ ] 视频处理模块
  - [ ] 实现 FFmpeg 检测
  - [ ] 实现视频信息探测
  - [ ] 实现视频验证

- [ ] 音频提取模块
  - [ ] 实现音频提取调用
  - [ ] 实现音频提取 (PCM 16-bit, 16kHz, mono)
  - [ ] 实现临时文件清理

- [ ] ASR 识别模块
  - [ ] 集成 ASR 引擎
  - [ ] 支持多种模型 (tiny, base, small, medium, large)
  - [ ] 支持语言自动检测
  - [ ] 单词级时间戳输出

- [ ] 字幕生成模块
  - [ ] 实现 SRT 格式化
  - [ ] 实现 VTT 格式化
  - [ ] 实现时间戳格式化
  - [ ] 实现文本自动换行

- [ ] 主流程整合
  - [ ] 实现视频处理流程函数
  - [ ] 实现文件输出
  - [ ] 错误处理和清理

### 验收标准

```bash
$ vsub input.mp4
[1/3] 提取音频...
[2/3] 语音识别...
[3/3] 生成字幕...
✓ 字幕已保存: input.srt

$ cat input.srt
1
00:00:00,000 --> 00:00:03,500
Hello, world!
...
```

## Phase 3: 优化完善

**目标**: 添加进度显示、批量处理、更多格式、完善测试

### 任务清单

- [ ] 进度显示
  - [ ] 音频提取进度
  - [ ] ASR 推理进度
  - [ ] 总体进度条

- [ ] 批量处理
  - [ ] 支持通配符输入
  - [ ] 并发处理控制
  - [ ] 批量进度显示

- [ ] 额外功能
  - [ ] 实现 --keep-audio
  - [ ] 实现 --verbose
  - [ ] 实现 --overwrite

- [ ] 测试
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 添加测试视频/音频

- [ ] 文档
  - [ ] README 完善
  - [ ] 使用示例
  - [ ] 常见问题

### 验收标准

```bash
$ vsub *.mp4
[1/4] 处理 video1.mp4...
[2/4] 处理 video2.mp4...
...
✓ 完成 4/4 个文件
```

## Phase 4: 扩展功能（可选）

**目标**: 添加高级功能

### 任务清单

- [ ] 字幕翻译（可选）
  - [ ] 集成翻译 API
  - [ ] 支持双语字幕

- [ ] 字幕烧录（可选）
  - [ ] 使用 FFmpeg 将字幕烧录到视频
  - [ ] 支持样式设置

- [ ] GUI 界面（可选）
  - [ ] 图形界面实现
  - [ ] 拖拽上传
  - [ ] 实时预览

- [ ] 更多 ASR 引擎支持
  - [ ] 阿里 FunASR
  - [ ] Azure Speech
  - [ ] OpenAI Whisper API

## 依赖安装指南

### 环境要求

- **操作系统**: Linux / macOS / Windows
- **内存**: 8GB+ 推荐（取决于模型大小）
- **Python**: 3.8+
- **FFmpeg**: 需系统安装

### FFmpeg 安装

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html
# 添加到 PATH
```

### ASR 模型

首次运行时会自动下载，或手动预下载。

## 开发命令

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行
vsub input.mp4

# 测试
pytest

# 代码格式化
black vsub/
isort vsub/

# 类型检查
mypy vsub/

# 代码检查
flake8 vsub/

# 构建发布包
python -m build
```

## 目录结构（最终）

```
vsub/
├── pyproject.toml
├── setup.py
├── README.md
├── requirements.txt
├── vsub/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI 入口
│   ├── config.py           # 配置管理
│   ├── video.py            # 视频处理
│   ├── audio.py            # 音频提取
│   ├── asr.py              # ASR 识别
│   ├── subtitle.py         # 字幕生成
│   └── utils.py            # 工具函数
├── tests/
│   ├── test_video.py
│   ├── test_audio.py
│   ├── test_asr.py
│   ├── test_subtitle.py
│   └── fixtures/
│       ├── sample.mp4
│       └── sample.wav
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── modules.md
│   ├── cli.md
│   ├── config.md
│   └── development.md
└── examples/
    └── example.py
```

## 跨平台支持

| 平台 | 支持状态 | 注意事项 |
|------|----------|----------|
| Linux | ✅ 完整支持 | 推荐使用 CUDA 加速 |
| macOS | ✅ 完整支持 | M1/M2 使用 Metal Performance Shaders |
| Windows | ✅ 完整支持 | 需安装 FFmpeg 并添加到 PATH |
| WSL | ✅ 完整支持 | 与 Linux 相同 |

## 里程碑

| 阶段 | 预计功能 | 状态 |
|------|---------|------|
| v0.1.0 | 基础 CLI + 配置系统 | ⬜ |
| v0.2.0 | 核心功能完整 | ⬜ |
| v0.3.0 | 进度显示 + 批量处理 | ⬜ |
| v0.4.0 | 测试 + 文档完善 | ⬜ |
| v1.0.0 | 稳定版本发布 | ⬜ |
