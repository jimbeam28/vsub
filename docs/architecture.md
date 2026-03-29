# 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                          CLI Layer                          │
│                    (vsub/cli.py - Click)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Configuration                          │
│              (vsub/config.py - Pydantic)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  命令行参数   │  │  配置文件     │  │   默认值      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Pipeline                          │
│                     (vsub/core.py)                          │
│                                                             │
│   输入视频 → 验证 → 提取音频 → ASR识别 → 生成字幕 → 输出   │
└─────────────────────────────────────────────────────────────┘
         │              │              │             │
         ▼              ▼              ▼             ▼
┌────────────┐  ┌────────────┐  ┌────────────┐ ┌────────────┐
│   Video    │  │   Audio    │  │    ASR     │ │  Subtitle  │
│  (视频处理) │  │  (音频处理) │  │  (语音识别) │ │  (字幕生成) │
└────────────┘  └────────────┘  └────────────┘ └────────────┘
```

## 模块职责

### 1. CLI 模块 (`vsub/cli.py`)

**职责**: 命令行接口，解析用户输入

```python
# 主要功能
- 定义命令行参数 (--help, --version, -l, -m, etc.)
- 验证输入参数
- 初始化日志系统
- 调用核心处理流程
```

**关键类/函数**:
- `cli()` - Click 命令定义
- `main()` - 入口点
- `init_config()` - 生成默认配置

### 2. 配置模块 (`vsub/config.py`)

**职责**: 配置管理和合并

```python
# 配置优先级（从高到低）
1. 命令行参数
2. 配置文件 (vsub.yaml, ~/.config/vsub/config.yaml)
3. 默认配置
```

**关键类**:
- `Config` - 配置数据模型 (Pydantic)
- `OutputFormat` - 输出格式枚举
- `WhisperModel` - 模型枚举

**配置项**:
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| format | OutputFormat | SRT | 输出格式 |
| model | WhisperModel | BASE | ASR模型 |
| language | str | None | 语言代码 |
| keep_audio | bool | False | 保留临时音频 |
| overwrite | bool | False | 强制覆盖 |
| max_line_length | int | 80 | 最大行长度 |
| max_line_count | int | 2 | 最大行数 |

### 3. 核心模块 (`vsub/core.py`)

**职责**: 主处理流程编排

```python
# 处理流程
def process_video(input_path, config):
    1. validate_video()      # 验证视频
    2. probe_video()         # 获取视频信息
    3. extract_to_wav()      # 提取音频
    4. engine.transcribe()   # ASR识别
    5. segments_from_asr()   # 生成字幕片段
    6. write_to_file()       # 写入文件
```

### 4. 视频模块 (`vsub/video.py`)

**职责**: 视频信息探测和验证

```python
VideoInfo                    # 视频信息数据类
├── path                     # 文件路径
├── duration                 # 时长
├── resolution               # 分辨率 (1920x1080)
├── fps                      # 帧率
├── has_audio                # 是否有音频
└── audio/video_codec        # 编码信息

Functions:
├── check_ffmpeg()           # 检查 FFmpeg
├── probe_video()            # 探测视频信息
└── validate_video()         # 验证视频文件
```

### 5. 音频模块 (`vsub/audio.py`)

**职责**: 音频提取和处理

```python
AudioExtractor               # 音频提取器
├── extract_to_wav()         # 提取为 WAV (16kHz, mono, PCM)
└── get_audio_duration()     # 获取音频时长

Functions:
├── temp_audio_path()        # 生成临时文件路径
├── cleanup_audio()          # 清理临时文件
└── parse_duration()         # 解析时长字符串

# 输出格式: PCM 16-bit, 16kHz, mono
# 这是 ASR 的最佳输入格式
```

### 6. ASR 模块 (`vsub/asr.py`)

**职责**: 语音识别

```python
AsrEngine (ABC)              # ASR 引擎接口
├── transcribe()             # 识别音频
├── is_available()           # 检查可用性
└── name                     # 引擎名称

WhisperEngine (AsrEngine)    # Whisper 实现
├── _load_model()            # 延迟加载模型
└── transcribe()             # 调用 faster-whisper

AsrWord                      # 识别结果单词
├── text                     # 文本内容
├── start/end                # 时间戳
└── confidence               # 置信度
```

### 7. 字幕模块 (`vsub/subtitle.py`)

**职责**: 字幕生成和格式化

```python
SubtitleSegment              # 字幕片段
├── index                    # 序号
├── start/end                # 时间戳
└── text                     # 文本内容

SubtitleGenerator            # 字幕生成器
├── generate_srt()           # 生成 SRT
├── generate_vtt()           # 生成 VTT
├── _wrap_text()             # 自动换行
└── write_to_file()          # 写入文件

Functions:
└── segments_from_asr_result()  # ASR结果转字幕
```

## 数据流

```
输入视频 (MP4/MKV/...)
       │
       ▼
┌──────────────┐
│ probe_video  │ ──▶ VideoInfo (时长、分辨率、是否有音频)
└──────────────┘
       │
       ▼
┌──────────────┐
│extract_to_wav│ ──▶ 临时 WAV 文件 (16kHz, mono, PCM)
└──────────────┘
       │
       ▼
┌──────────────┐
│  transcribe  │ ──▶ List[AsrWord] (单词级时间戳)
└──────────────┘
       │
       ▼
┌──────────────┐
│segments_from_│ ──▶ List[SubtitleSegment] (按时间分片)
│  asr_result  │
└──────────────┘
       │
       ▼
┌──────────────┐
│write_to_file │ ──▶ 字幕文件 (SRT/VTT)
└──────────────┘
```

## 依赖关系

```
vsub/
├── __init__.py              # 导出 Config, process_video
├── __main__.py              # python -m vsub 入口
├── cli.py                   # 依赖: config, core, click
├── config.py                # 依赖: pydantic, yaml
├── core.py                  # 依赖: video, audio, asr, subtitle, config
├── video.py                 # 依赖: 标准库 (subprocess, json)
├── audio.py                 # 依赖: 标准库 (subprocess, tempfile)
├── asr.py                   # 依赖: faster-whisper (optional)
└── subtitle.py              # 依赖: 标准库 (re)
```

## 扩展点

### 添加新的 ASR 引擎

```python
# vsub/asr.py

class NewAsrEngine(AsrEngine):
    def transcribe(self, audio_path, language=None):
        # 实现识别逻辑
        return [AsrWord(...), ...]

    def is_available(self):
        # 检查依赖是否安装
        return True
```

### 添加新的字幕格式

```python
# vsub/subtitle.py

class SubtitleGenerator:
    def generate_ass(self, segments):
        # 生成 ASS 格式
        pass
```

### 添加新的配置源

```python
# vsub/config.py

class Config:
    @staticmethod
    def find_config_file():
        # 添加新的配置查找位置
        candidates = [
            Path("vsub.yaml"),
            Path.home() / ".vsub.yaml",  # 新增
            # ...
        ]
```

## 测试架构

```
tests/
├── __init__.py
├── conftest.py              # pytest fixtures
├── test_config.py           # 配置测试
├── test_video.py            # 视频模块测试 (mock)
├── test_audio.py            # 音频模块测试 (mock)
├── test_asr.py              # ASR 模块测试 (mock)
├── test_subtitle.py         # 字幕模块测试
└── test_integration.py      # 集成测试
```

## 性能考虑

1. **模型缓存**: WhisperModel 延迟加载并缓存
2. **临时文件**: 使用系统 temp 目录，自动清理
3. **内存优化**: 流式处理音频，不加载整个视频
4. **GPU 加速**: faster-whisper 自动检测 CUDA

## 安全考虑

1. **路径安全**: 使用 Path 对象，防止路径遍历
2. **临时文件**: 随机文件名，避免冲突
3. **命令注入**: 使用列表传参，避免 shell 注入
4. **资源限制**: 建议添加超时机制

## 未来改进

1. **并发处理**: 批量处理时使用线程池
2. **进度回调**: 支持自定义进度回调函数
3. **插件系统**: 支持第三方扩展
4. **Web UI**: 提供图形界面
