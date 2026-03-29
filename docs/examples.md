# 使用示例

## 基础用法

### 生成字幕

```bash
# 基本用法 - 自动生成 input.srt
vsub input.mp4

# 指定输出文件名
vsub input.mp4 -o subtitle.srt

# 指定输出目录
vsub input.mp4 -o ./output/subtitle.srt
```

### 指定语言

```bash
# 中文视频
vsub input.mp4 -l zh

# 英文视频
vsub input.mp4 -l en

# 日语视频
vsub input.mp4 -l ja

# 留空自动检测（推荐多语言视频）
vsub input.mp4
```

### 选择模型

```bash
# tiny - 最快，精度较低（适合快速测试）
vsub input.mp4 -m tiny

# base - 平衡速度和质量（默认）
vsub input.mp4 -m base

# small - 较好质量
vsub input.mp4 -m small

# medium - 高质量
vsub input.mp4 -m medium

# large - 最高质量，最慢
vsub input.mp4 -m large
```

## 批量处理

### 处理多个文件

```bash
# 处理当前目录所有 mp4
vsub *.mp4

# 处理多个指定文件
vsub video1.mp4 video2.mp4 video3.mp4

# 递归处理
find . -name "*.mp4" -exec vsub {} \;
```

### 批量处理示例输出

```
[1/3] 处理 video1.mp4...
开始处理: video1.mp4
验证视频文件...
视频信息: 1920x1080 @ 30.00fps, 时长: 120.50s
提取音频...
启动 ASR 识别...
语音识别: 100%|████████████████| 100/100 [00:15<00:00]
识别完成: 523 个单词
生成字幕...
生成 47 个字幕片段
✓ 字幕已保存: video1.srt

[2/3] 处理 video2.mp4...
...

完成: 3/3 个文件
```

## 输出格式

### SRT 格式（默认）

```bash
vsub input.mp4              # 生成 input.srt
vsub input.mp4 -f srt       # 显式指定
```

SRT 输出示例：

```srt
1
00:00:00,000 --> 00:00:03,500
Hello, welcome to this video.

2
00:00:03,500 --> 00:00:07,200
Today we'll learn about subtitles.
```

### VTT 格式

```bash
vsub input.mp4 -f vtt       # 生成 input.vtt
```

VTT 输出示例：

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.500
Hello, welcome to this video.

00:00:03.500 --> 00:00:07.200
Today we'll learn about subtitles.
```

## 高级用法

### 保留临时文件

```bash
# 保留提取的音频文件（用于调试）
vsub input.mp4 --keep-audio
```

临时音频文件保存在 `/tmp/` 目录，文件名包含随机后缀。

### 强制覆盖

```bash
# 如果输出文件已存在，强制覆盖
vsub input.mp4 --overwrite
```

### 详细日志

```bash
# 显示 DEBUG 级别日志
vsub input.mp4 -v

# 输出示例
DEBUG: 开始处理: input.mp4
DEBUG: 验证视频文件...
INFO: 视频信息: 1920x1080 @ 30.00fps, 时长: 120.50s
DEBUG: 音频已提取到: /tmp/input_a3b5c7d2.wav
```

## 配置文件

### 创建配置文件

```bash
vsub --init
```

生成 `vsub.yaml`：

```yaml
format: srt
model: base
language: zh
keep_audio: false
overwrite: false
max_line_length: 80
max_line_count: 2
```

### 配置优先级

命令行参数 > 配置文件 > 默认值

```bash
# 配置文件设置 model: base
# 但命令行覆盖为 medium
vsub input.mp4 -m medium
```

### 全局配置

将配置放在用户目录：

```bash
mkdir -p ~/.config/vsub
cp vsub.yaml ~/.config/vsub/config.yaml
```

## 实用脚本

### 处理目录内所有视频

```bash
#!/bin/bash
# process_all.sh

for file in *.mp4 *.mkv *.avi; do
    [ -e "$file" ] || continue
    echo "处理: $file"
    vsub "$file" -l zh
done
```

### 生成并转换格式

```bash
#!/bin/bash
# generate_and_convert.sh

input=$1

# 生成 SRT
vsub "$input" -f srt

# 同时生成 VTT
vsub "$input" -f vtt --overwrite
```

### 检查处理结果

```bash
#!/bin/bash
# check_results.sh

for video in *.mp4; do
    subtitle="${video%.mp4}.srt"
    if [ -f "$subtitle" ]; then
        lines=$(wc -l < "$subtitle")
        echo "✓ $video -> $subtitle ($lines 行)"
    else
        echo "✗ $video - 未生成字幕"
    fi
done
```

## 与其他工具结合

### 使用 FFmpeg 烧录字幕

```bash
# 将字幕烧录到视频
ffmpeg -i input.mp4 -vf "subtitles=input.srt" -c:a copy output_subtitled.mp4

# 指定字幕样式
ffmpeg -i input.mp4 -vf "subtitles=input.srt:force_style='FontSize=24,PrimaryColour=&H00FFFFFF'" output.mp4
```

### 合并多个字幕

```bash
# 合并双语字幕（需要 srt-tools）
srt-tool join chinese.srt english.srt -o bilingual.srt
```

### 翻译字幕

```bash
# 使用 translate-cli 翻译字幕
# 先安装: pip install translate

# 中译英
translate -i input.srt -o output_en.srt zh en
```

## 故障排除

### 常见问题

1. **FFmpeg 未找到**
   ```bash
   which ffmpeg
   # 如果为空，需要安装 FFmpeg 并添加到 PATH
   ```

2. **模型下载失败**
   ```bash
   # 手动下载模型
   python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
   ```

3. **内存不足**
   ```bash
   # 使用更小的模型
   vsub input.mp4 -m tiny
   ```

4. **识别质量差**
   ```bash
   # 尝试更大的模型
   vsub input.mp4 -m medium -l zh
   ```
