# 配置说明

## 配置文件格式

vsub 使用 TOML 格式的配置文件。

## 默认配置

```toml
# config.toml

[asr]
# Whisper 模型大小
# 可选: tiny, base, small, medium, large-v1, large-v2, large-v3
model = "medium"

# 语言代码
# "auto" 表示自动检测，或指定: zh, en, ja, ko, fr, de, es 等
language = "auto"

# 计算设备: auto, cpu, cuda
device = "auto"

# 计算精度: int8, float16, float32
# int8: 速度快，内存占用小（推荐）
# float16: 精度更高，需要更多显存
# float32: 最高精度，CPU 模式使用
compute_type = "int8"

# 解码参数
beam_size = 5
best_of = 5

# 温度采样（0-1）
temperature = 0.0

# 条件概率阈值
condition_on_previous_text = true

[audio]
# 提取音频格式
format = "wav"

# 采样率（Whisper 要求 16kHz）
sample_rate = 16000

# 声道数（1=单声道，2=立体声）
channels = 1

# 音频编码
codec = "pcm_s16le"

[subtitle]
# 输出格式: srt, vtt
format = "srt"

# 每行最大字符数（超过则换行）
max_line_length = 40

# 每段字幕最大行数
max_lines = 2

# 最短持续时间（秒）
min_duration = 1.0

# 最长持续时间（秒）
max_duration = 7.0

# 是否拆分长句
split_long_sentences = true

# 时间偏移（秒，用于校准）
time_offset = 0.0

[output]
# 默认输出目录
dir = "."

# 输出文件名后缀
suffix = "_subtitled"

# 是否覆盖已有文件
overwrite = false

# 保留临时文件
keep_temp = false

[advanced]
# FFmpeg 路径（可选，留空则自动查找）
ffmpeg_path = ""

# Python 路径（可选，留空则自动查找）
python_path = ""

# 模型缓存目录
model_cache_dir = "~/.cache/vsub/models"

# 临时文件目录
temp_dir = "/tmp"

# 最大并发数
max_workers = 1

# 超时设置（秒）
timeout = 3600
```

## 配置项详解

### ASR 配置 `[asr]`

#### model

| 模型 | 大小 | 显存需求 | 速度 | 准确率 |
|------|------|---------|------|--------|
| tiny | ~75MB | ~1GB | 极快 | 较低 |
| base | ~150MB | ~1GB | 很快 | 一般 |
| small | ~500MB | ~2GB | 较快 | 较好 |
| medium | ~1.5GB | ~5GB | 中等 | 好 |
| large-v3 | ~3GB | ~10GB | 较慢 | 最好 |

**推荐**: 8GB 内存用 `medium`，16GB+ 用 `large-v3`

#### language

支持的语言代码（部分）：
- `zh` - 中文
- `en` - 英语
- `ja` - 日语
- `ko` - 韩语
- `fr` - 法语
- `de` - 德语
- `es` - 西班牙语
- `ru` - 俄语
- `auto` - 自动检测

#### device

- `auto` - 自动选择（优先 GPU）
- `cpu` - 强制使用 CPU
- `cuda` - 强制使用 NVIDIA GPU

#### compute_type

- `int8` - 量化推理，速度快，内存占用小（推荐）
- `float16` - 半精度，质量更好，需要更多显存
- `float32` - 全精度，仅在 CPU 模式下可用

### 音频配置 `[audio]`

一般保持默认即可。Whisper 要求 16kHz 单声道音频。

### 字幕配置 `[subtitle]`

#### max_line_length

每行最大字符数。中文建议 20-30，英文建议 35-45。

#### max_lines

每段字幕最多显示几行。建议 1-2 行。

#### min_duration / max_duration

控制每段字幕的显示时间。
- 太短（<1s）观众来不及阅读
- 太长（>7s）可能错过下一句话

### 输出配置 `[output]`

#### suffix

输出文件名后缀。例如输入 `video.mp4`：
- suffix="_subtitled" → `video_subtitled.srt`
- suffix=".zh" → `video.zh.srt`
- suffix="" → `video.srt`

## 配置文件位置

vsub 按以下顺序查找配置文件：

1. 命令行指定的 `-c, --config` 路径
2. 当前目录的 `vsub.toml`
3. 当前目录的 `config.toml`
4. 用户配置目录：
   - Linux: `~/.config/vsub/config.toml`
   - macOS: `~/Library/Application Support/vsub/config.toml`
   - Windows: `%APPDATA%\vsub\config.toml`

## 环境特定配置

### 最小配置文件（快速开始）

```toml
[asr]
model = "small"
language = "zh"
```

### 高质量配置

```toml
[asr]
model = "large-v3"
language = "zh"
compute_type = "float16"

[subtitle]
max_line_length = 30
max_lines = 1
```

### 快速处理配置

```toml
[asr]
model = "base"
device = "cpu"
compute_type = "int8"
beam_size = 1
```

### 批量处理配置

```toml
[asr]
model = "small"
device = "auto"

[output]
overwrite = true
keep_temp = false

[advanced]
max_workers = 4
```

## 配置文件验证

vsub 启动时会验证配置文件：

```bash
# 验证配置文件格式
vsub --config config.toml --dry-run

# 或使用独立命令（如果实现）
vsub config --validate config.toml
```

## 生成默认配置

```bash
# 生成默认配置文件
vsub config --init > vsub.toml
```
