# 模块职责

## 文件结构

```
src/
├── main.rs              # CLI 入口
├── lib.rs               # 库入口（供未来 UI 使用）
├── cli/
│   ├── mod.rs           # CLI 模块聚合
│   ├── args.rs          # 参数定义（clap）
│   └── progress.rs      # 进度条显示
├── core/
│   ├── mod.rs           # 核心模块聚合
│   ├── video.rs         # 视频处理
│   ├── audio.rs         # 音频提取
│   ├── subtitle.rs      # 字幕格式处理
│   └── config.rs        # 配置管理
└── asr/
    ├── mod.rs           # ASR 模块聚合
    ├── engine.rs        # ASR 引擎接口
    └── python_bridge.rs # Python 子进程通信
```

## 模块详解

### 1. CLI 模块 (`src/cli/`)

**职责**: 用户交互层

#### args.rs
- 定义命令行参数结构（使用 clap derive macro）
- 参数验证和默认值设置
- 帮助信息生成

#### progress.rs
- 进度条显示（文件处理进度）
- ASR 推理进度（从 Python 进程接收）
- 旋转指示器（等待状态）

### 2. Core 模块 (`src/core/`)

**职责**: 核心业务逻辑

#### video.rs
```rust
pub struct VideoProcessor;

impl VideoProcessor {
    // 检测视频信息
    pub fn probe(input: &Path) -> Result<VideoInfo>;

    // 验证输入文件
    pub fn validate(input: &Path) -> Result<()>;
}

pub struct VideoInfo {
    pub duration: f64,
    pub has_audio: bool,
    pub audio_streams: Vec<AudioStreamInfo>,
}
```

#### audio.rs
```rust
pub struct AudioExtractor;

impl AudioExtractor {
    // 提取音频为 Whisper 需要的格式
    pub fn extract(
        input: &Path,
        output: &Path,
        config: &AudioConfig
    ) -> Result<()>;

    // 清理临时音频文件
    pub fn cleanup(path: &Path) -> Result<()>;
}

pub struct AudioConfig {
    pub format: String,      // "wav"
    pub sample_rate: u32,    // 16000
    pub channels: u32,       // 1 (mono)
}
```

#### subtitle.rs
```rust
pub struct SubtitleGenerator;

impl SubtitleGenerator {
    // 从 ASR 结果生成字幕
    pub fn generate(
        segments: &[Segment],
        config: &SubtitleConfig
    ) -> Result<String>;
}

pub enum SubtitleFormat {
    Srt,
    Vtt,
}

pub struct Segment {
    pub start: f64,
    pub end: f64,
    pub text: String,
}
```

#### config.rs
```rust
#[derive(Debug, Deserialize)]
pub struct Config {
    pub asr: AsrConfig,
    pub audio: AudioConfig,
    pub subtitle: SubtitleConfig,
    pub output: OutputConfig,
}

impl Config {
    // 从文件加载配置
    pub fn from_file(path: &Path) -> Result<Self>;

    // 默认配置
    pub fn default() -> Self;

    // 合并命令行参数
    pub fn merge_with_args(&mut self, args: &CliArgs);
}
```

### 3. ASR 模块 (`src/asr/`)

**职责**: 语音识别引擎桥接

#### engine.rs
```rust
#[async_trait]
pub trait ASREngine: Send + Sync {
    async fn transcribe(&self, audio: &Path) -> Result<Vec<Segment>>;
    fn name(&self) -> &str;
}

// 引擎工厂
pub struct EngineFactory;

impl EngineFactory {
    pub fn create(config: &AsrConfig) -> Result<Box<dyn ASREngine>>;
}
```

#### python_bridge.rs
```rust
pub struct PythonBridge {
    script_path: PathBuf,
    config: AsrConfig,
}

impl PythonBridge {
    pub fn new(script_path: PathBuf, config: AsrConfig) -> Self;

    // 启动 Python 进程执行推理
    pub async fn transcribe(&self, audio: &Path) -> Result<Vec<Segment>>;
}

#[async_trait]
impl ASREngine for PythonBridge {
    async fn transcribe(&self, audio: &Path) -> Result<Vec<Segment>> {
        // 实现子进程调用逻辑
    }
}
```

### 4. Python 脚本 (`python/`)

**职责**: ASR 推理实现

#### whisper_engine.py
```python
#!/usr/bin/env python3
"""
Whisper ASR 引擎脚本
接收命令行参数，执行推理，输出 JSON 结果
"""

import argparse
import json
import sys
from faster_whisper import WhisperModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--model", default="medium")
    parser.add_argument("--language", default="auto")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    # 加载模型
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type
    )

    # 推理
    segments, info = model.transcribe(
        args.audio,
        language=args.language if args.language != "auto" else None
    )

    # 输出 JSON
    result = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments
    ]
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

## 数据流详细说明

### 1. 视频输入处理
```
输入: PathBuf
  ↓
VideoProcessor::probe() → VideoInfo
  ↓
验证通过 → 继续
验证失败 → 返回错误
```

### 2. 音频提取
```
输入: PathBuf (视频), AudioConfig
  ↓
AudioExtractor::extract()
  ↓
调用 FFmpeg → 输出 temp.wav
  ↓
返回: PathBuf (音频文件)
```

### 3. ASR 推理
```
输入: PathBuf (音频), AsrConfig
  ↓
PythonBridge::transcribe()
  ↓
启动 Python 子进程
  ↓
读取 stdout JSON
  ↓
解析 → Vec<Segment>
```

### 4. 字幕生成
```
输入: Vec<Segment>, SubtitleConfig
  ↓
SubtitleGenerator::generate()
  ↓
格式化时间戳
  ↓
应用长度限制
  ↓
输出: String (SRT/VTT 内容)
```

## 错误处理策略

### 错误类型定义

```rust
#[derive(Error, Debug)]
pub enum VsubError {
    #[error("视频文件无效: {0}")]
    InvalidVideo(String),

    #[error("FFmpeg 错误: {0}")]
    FFmpegError(String),

    #[error("ASR 引擎错误: {0}")]
    ASRError(String),

    #[error("配置错误: {0}")]
    ConfigError(String),

    #[error("IO 错误: {0}")]
    IOError(#[from] std::io::Error),
}
```

### 错误传播

- 所有模块返回 `Result<T, VsubError>`
- CLI 层统一处理错误并显示友好消息
- 临时文件清理使用 `Drop` trait 确保执行
