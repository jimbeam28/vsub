# 开发计划

## Phase 1: 基础框架

**目标**: 搭建项目结构，实现基本 CLI 和配置系统

### 任务清单

- [ ] 初始化 Rust 项目
  - [ ] `cargo init --name vsub`
  - [ ] 配置 Cargo.toml 依赖
  - [ ] 添加 clap, anyhow, serde, config, tracing

- [ ] 实现配置系统
  - [ ] 定义 Config 结构体
  - [ ] 实现从文件加载配置
  - [ ] 实现默认配置
  - [ ] 实现配置合并（文件 + 命令行）

- [ ] 实现 CLI 参数解析
  - [ ] 定义 Cli 结构体（clap derive）
  - [ ] 实现 --help, --version
  - [ ] 参数验证

- [ ] 日志和错误处理
  - [ ] 设置 tracing 日志
  - [ ] 定义 VsubError 类型
  - [ ] 友好的错误显示

### 验收标准

```bash
$ cargo build
$ ./target/release/vsub --help
$ ./target/release/vsub --version
$ ./target/release/vsub input.mp4  # 显示"功能未实现"
```

## Phase 2: 核心功能

**目标**: 实现视频处理、音频提取、ASR 桥接、字幕生成

### 任务清单

- [ ] 视频处理模块
  - [ ] 实现 FFmpeg 检测
  - [ ] 实现视频信息探测
  - [ ] 实现视频验证

- [ ] 音频提取模块
  - [ ] 实现 FFmpeg 命令构建
  - [ ] 实现音频提取
  - [ ] 实现临时文件清理

- [ ] Python ASR 引擎
  - [ ] 编写 whisper_engine.py
  - [ ] 测试 faster-whisper 调用
  - [ ] JSON 输出格式定义

- [ ] ASR 桥接模块
  - [ ] 定义 ASREngine trait
  - [ ] 实现 PythonBridge
  - [ ] 实现子进程调用
  - [ ] JSON 结果解析

- [ ] 字幕生成模块
  - [ ] 实现 SRT 格式化
  - [ ] 实现 VTT 格式化
  - [ ] 实现时间戳格式化
  - [ ] 实现文本长度限制

- [ ] 主流程整合
  - [ ] 实现 lib.rs 的 process 函数
  - [ ] 实现文件输出
  - [ ] 错误处理和清理

### 验收标准

```bash
$ ./target/release/vsub input.mp4
[1/3] 提取音频...
[2/3] 语音识别...
[3/3] 生成字幕...
✓ 字幕已保存: input_subtitled.srt

$ cat input_subtitled.srt
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
$ ./target/release/vsub *.mp4
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

- [ ] Web UI 原型
  - [ ] 使用 Tauri 创建桌面应用
  - [ ] 拖拽上传
  - [ ] 实时预览

- [ ] 更多 ASR 引擎支持
  - [ ] 阿里 FunASR
  - [ ] Azure Speech
  - [ ] 可插拔引擎架构

## 依赖安装指南

### Rust 环境

```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 验证
rustc --version
cargo --version
```

### Python 环境

```bash
# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r python/requirements.txt
```

### FFmpeg

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html
# 添加到 PATH
```

### faster-whisper 模型

首次运行时会自动下载，或手动预下载：

```python
from faster_whisper import WhisperModel
# 这会自动下载模型到缓存目录
model = WhisperModel("medium", device="cpu")
```

## 开发命令

```bash
# 构建
cargo build

# 发布构建
cargo build --release

# 运行
cargo run -- input.mp4

# 测试
cargo test

# 格式化
cargo fmt

# 检查
cargo clippy

# 文档
cargo doc --open
```

## 目录结构（最终）

```
vsub/
├── Cargo.toml
├── Cargo.lock
├── config.toml
├── README.md
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── cli/
│   │   ├── mod.rs
│   │   ├── args.rs
│   │   └── progress.rs
│   ├── core/
│   │   ├── mod.rs
│   │   ├── video.rs
│   │   ├── audio.rs
│   │   ├── subtitle.rs
│   │   └── config.rs
│   └── asr/
│       ├── mod.rs
│       ├── engine.rs
│       └── python_bridge.rs
├── python/
│   ├── whisper_engine.py
│   └── requirements.txt
├── tests/
│   ├── integration_tests.rs
│   └── fixtures/
│       ├── sample.mp4
│       └── sample.wav
└── docs/
    ├── README.md
    ├── architecture.md
    ├── modules.md
    ├── cli.md
    ├── config.md
    └── development.md
```

## 里程碑

| 阶段 | 预计功能 | 状态 |
|------|---------|------|
| v0.1.0 | 基础 CLI + 配置系统 | ⬜ |
| v0.2.0 | 核心功能完整 | ⬜ |
| v0.3.0 | 进度显示 + 批量处理 | ⬜ |
| v0.4.0 | 测试 + 文档完善 | ⬜ |
| v1.0.0 | 稳定版本发布 | ⬜ |
