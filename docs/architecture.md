# 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI 层 (Rust)                         │
│  - 参数解析、进度显示、错误处理、配置文件管理                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心处理引擎 (Rust)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  视频处理器  │  │  音频提取器  │  │    字幕生成器        │  │
│  │ VideoProcessor│ │AudioExtractor│ │  SubtitleGenerator  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ASR 引擎桥接层                            │
│              (Python 子进程 / PyO3 嵌入)                     │
│                    faster-whisper                           │
└─────────────────────────────────────────────────────────────┘
```

## 数据流

```
输入视频文件
    │
    ▼
[视频处理器] ──检测格式、提取信息──┐
    │                              │
    ▼                              │
[音频提取器] ── FFmpeg 提取音频 ──┤
    │                              │
    ▼                              │
[ASR 桥接层] ──调用 faster-whisper │
    │    ──返回带时间戳的文本段 ────┘
    ▼
[字幕生成器] ──格式化时间戳、生成 SRT/VTT
    │
    ▼
输出字幕文件
```

## 技术选型

### Rust 依赖

| 用途 | Crate | 说明 |
|------|-------|------|
| CLI 解析 | clap | 命令行参数解析 |
| 进度显示 | indicatif | 进度条和旋转指示器 |
| 配置管理 | config + serde | 配置文件读取 |
| 音视频处理 | ffmpeg-next | FFmpeg 绑定 |
| 异步处理 | tokio | 异步运行时 |
| 错误处理 | anyhow + thiserror | 错误处理工具 |
| 日志 | tracing | 结构化日志 |

### Python 依赖

| 包 | 版本 | 说明 |
|----|------|------|
| faster-whisper | 1.0.0 | Whisper 推理引擎 |
| numpy | >=1.24.0 | 数值计算 |

## 通信机制

### Rust 与 Python 通信

采用**子进程通信**方式（Tokio process）：

```rust
// Rust 侧：启动 Python 子进程
let output = Command::new("python")
    .arg("python/whisper_engine.py")
    .arg("--audio").arg(audio_path)
    .arg("--model").arg(model)
    .arg("--language").arg(language)
    .output()
    .await?;

// 解析 JSON 输出
let segments: Vec<Segment> = serde_json::from_slice(&output.stdout)?;
```

```python
# Python 侧：接收参数，执行推理，输出 JSON
import json
from faster_whisper import WhisperModel

# ... 加载模型、推理 ...
segments = [
    {"start": 0.0, "end": 3.5, "text": "Hello world"},
    # ...
]
print(json.dumps(segments))
```

**优点**：
- 简单稳定，无需复杂的 FFI 绑定
- Python 环境隔离，避免依赖冲突
- 易于调试和替换 ASR 引擎

## 扩展性设计

### 未来 Web UI 支持

```rust
// src/lib.rs 暴露核心 API
pub struct SubtitleEngine {
    config: Config,
}

impl SubtitleEngine {
    pub async fn process(&self, input: PathBuf) -> Result<SubtitleResult>;
    pub fn subscribe_progress(&self) -> mpsc::Receiver<ProgressEvent>;
}
```

Web UI 方案：
1. **Tauri**: Rust 后端 + Web 前端（推荐）
2. **Axum/Rocket**: HTTP API 服务
3. **直接调用**: 使用 `lib.rs` 作为后端库

### 支持更多 ASR 引擎

```rust
trait ASREngine {
    async fn transcribe(&self, audio: PathBuf) -> Result<Vec<Segment>>;
}

struct WhisperEngine;    // faster-whisper
struct FunASREngine;     // 阿里 FunASR
struct AzureEngine;      // Azure Speech
```

## 跨平台支持

### 平台差异处理

| 功能 | Linux/macOS | Windows |
|------|------------|---------|
| FFmpeg 查找 | `which ffmpeg` | `where ffmpeg` |
| 路径分隔 | `/` | `\` |
| 进程创建 | `Command::new("python3")` | `Command::new("python")` |
| 环境变量 | `PATH` | `Path` |

### Windows 额外依赖

- 需手动安装 FFmpeg 并添加到 PATH
- GPU 加速需要 CUDA Toolkit（可选）
