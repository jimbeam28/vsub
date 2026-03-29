# CLI 接口设计

## 基本用法

```bash
vsub [OPTIONS] <INPUT> [OUTPUT]
```

## 参数说明

### 位置参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `<INPUT>` | 输入视频文件路径 | `input.mp4` |
| `[OUTPUT]` | 输出字幕文件路径（可选） | `output.srt` |

### 选项参数

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--language` | `-l` | 语言代码 (zh/en/ja/...) | `auto` |
| `--model` | `-m` | Whisper 模型大小 | `medium` |
| `--format` | `-f` | 输出格式 (srt/vtt) | `srt` |
| `--output-dir` | `-d` | 输出目录 | `.` |
| `--config` | `-c` | 配置文件路径 | - |
| `--keep-audio` | `-k` | 保留临时音频文件 | `false` |
| `--device` | - | 设备 (auto/cpu/cuda) | `auto` |
| `--verbose` | `-v` | 详细输出 | `false` |
| `--help` | `-h` | 显示帮助 | - |
| `--version` | `-V` | 显示版本 | - |

## 使用示例

### 基本用法

```bash
# 自动生成字幕（输出 input_subtitled.srt）
vsub input.mp4

# 指定输出文件
vsub input.mp4 output.srt

# 指定输出目录（生成 input_subtitled.srt）
vsub input.mp4 -d ./subs/
```

### 语言设置

```bash
# 自动检测语言（默认）
vsub input.mp4

# 指定中文
vsub input.mp4 -l zh

# 指定英文
vsub input.mp4 -l en

# 指定日文
vsub input.mp4 -l ja
```

### 模型选择

```bash
# 快速模型（准确率较低）
vsub input.mp4 --model tiny

# 平衡模型（推荐）
vsub input.mp4 --model medium

# 高质量模型（最准确）
vsub input.mp4 --model large-v3
```

### 输出格式

```bash
# 输出 SRT 格式（默认）
vsub input.mp4 -f srt

# 输出 WebVTT 格式
vsub input.mp4 -f vtt
```

### 高级用法

```bash
# 使用配置文件
vsub input.mp4 -c config.toml

# 保留临时音频文件（用于调试）
vsub input.mp4 --keep-audio

# 强制使用 CPU（禁用 GPU）
vsub input.mp4 --device cpu

# 详细输出（显示 FFmpeg 和 Whisper 日志）
vsub input.mp4 -v
```

### 批量处理

```bash
# 处理多个文件（shell 循环）
for f in *.mp4; do vsub "$f"; done

# 或使用 find
find . -name "*.mp4" -exec vsub {} \;
```

## 配置文件

使用 `-c` 选项加载配置文件：

```bash
vsub input.mp4 -c myconfig.toml
```

配置项详见 [config.md](config.md)

## 输出文件命名

| 输入 | 输出（默认） | 说明 |
|------|-------------|------|
| `video.mp4` | `video_subtitled.srt` | 添加 `_subtitled` 后缀 |
| `video.mp4` | `output.srt` | 使用指定的输出文件名 |
| `video.mp4` | `./subs/video_subtitled.srt` | 输出到指定目录 |

## 进度显示

```
$ vsub input.mp4
[1/3] 提取音频... ████████████ 100% (2.5s)
[2/3] 语音识别... ████████░░░░  67% (15.2s/22.8s)
[3/3] 生成字幕... ████████████ 100% (0.1s)
✓ 字幕已保存: input_subtitled.srt
```

## 退出状态码

| 状态码 | 说明 |
|--------|------|
| `0` | 成功 |
| `1` | 一般错误 |
| `2` | 无效参数 |
| `3` | FFmpeg 错误 |
| `4` | ASR 引擎错误 |
| `5` | 配置文件错误 |

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `VSUB_CONFIG` | 默认配置文件路径 | `~/.config/vsub/config.toml` |
| `VSUB_MODEL_PATH` | 模型缓存目录 | `~/.cache/vsub/models` |
| `FFMPEG_PATH` | FFmpeg 可执行文件路径 | `/usr/bin/ffmpeg` |
| `PYTHON_PATH` | Python 解释器路径 | `/usr/bin/python3` |

## 命令行参数定义（代码）

```rust
use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "vsub")]
#[command(about = "视频字幕生成工具")]
#[command(version)]
pub struct Cli {
    /// 输入视频文件
    #[arg(value_name = "INPUT")]
    pub input: PathBuf,

    /// 输出字幕文件（可选）
    #[arg(value_name = "OUTPUT")]
    pub output: Option<PathBuf>,

    /// 语言代码
    #[arg(short, long, value_name = "LANG")]
    pub language: Option<String>,

    /// Whisper 模型
    #[arg(short, long, value_name = "MODEL")]
    pub model: Option<String>,

    /// 输出格式
    #[arg(short, long, value_name = "FORMAT")]
    pub format: Option<String>,

    /// 输出目录
    #[arg(short, long, value_name = "DIR")]
    pub output_dir: Option<PathBuf>,

    /// 配置文件
    #[arg(short, long, value_name = "FILE")]
    pub config: Option<PathBuf>,

    /// 保留临时音频文件
    #[arg(long)]
    pub keep_audio: bool,

    /// 计算设备
    #[arg(long, value_name = "DEVICE")]
    pub device: Option<String>,

    /// 详细输出
    #[arg(short, long)]
    pub verbose: bool,
}
```
