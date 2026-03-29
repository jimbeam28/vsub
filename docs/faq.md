# 常见问题 (FAQ)

## 安装问题

### Q: 安装时提示 "No module named faster_whisper"

**A:** faster-whisper 是核心依赖，需要单独安装：

```bash
pip install faster-whisper
```

或者在安装 vsub 时包含所有依赖：

```bash
pip install -e ".[dev]"
```

### Q: 提示 "未找到 FFmpeg"

**A:** FFmpeg 是系统依赖，需要单独安装：

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. 下载 https://ffmpeg.org/download.html#build-windows
2. 解压到 `C:\ffmpeg`
3. 添加 `C:\ffmpeg\bin` 到系统 PATH
4. 重启终端

验证安装：
```bash
ffmpeg -version
ffprobe -version
```

### Q: 安装后命令找不到

**A:** 检查 pip 安装路径是否在 PATH 中：

```bash
# 查看 vsub 安装位置
which vsub
# 或
python -m site

# 如果不在 PATH，使用 python -m 运行
python -m vsub input.mp4
```

## 使用问题

### Q: 识别准确率不高怎么办？

**A:** 尝试以下方法：

1. **使用更大的模型**
   ```bash
   vsub input.mp4 -m medium  # 或 large
   ```

2. **指定正确的语言**
   ```bash
   vsub input.mp4 -l zh  # 中文
   vsub input.mp4 -l en  # 英文
   ```

3. **检查音频质量**
   - 确保视频有清晰的音频
   - 避免背景噪音过大的视频

### Q: 处理速度很慢怎么办？

**A:**

1. **使用更小的模型**
   ```bash
   vsub input.mp4 -m tiny  # 最快的模型
   ```

2. **使用 GPU 加速**（如果可用）
   - 确保安装了 CUDA 版本的 PyTorch
   - 自动检测 GPU，无需额外配置

3. **模型已缓存后速度会提升**
   - 首次运行需要下载模型
   - 后续使用已缓存的模型

### Q: 生成的字幕时间不准？

**A:**

1. 这是 ASR 模型的固有限制，单词级时间戳可能不够精确
2. 可以尝试使用更大的模型（medium/large）
3. 后期可以使用字幕编辑软件微调

### Q: 支持哪些视频格式？

**A:** vsub 支持 FFmpeg 支持的所有格式：

- **常见格式**: MP4, MKV, AVI, MOV, WMV, FLV, WebM
- **高清格式**: M2TS, TS (蓝光/电视录制)
- **其他**: 3GP, OGV, 等

只要 FFmpeg 能解码的格式都可以处理。

### Q: 如何批量处理视频？

**A:**

```bash
# 方法1: 通配符
vsub *.mp4

# 方法2: 循环
for f in *.mp4; do vsub "$f"; done

# 方法3: find 命令
find . -name "*.mp4" -exec vsub {} \;
```

## 配置问题

### Q: 配置文件放在哪里？

**A:** 按优先级查找：

1. 当前目录 `vsub.yaml`
2. 用户配置 `~/.config/vsub/config.yaml`
3. 系统配置 `/etc/vsub/config.yaml`

### Q: 命令行参数和配置文件冲突？

**A:** 优先级：命令行 > 配置文件 > 默认值

例如配置文件设置 `model: base`，但命令行可以覆盖：

```bash
vsub input.mp4 -m medium  # 使用 medium，忽略配置文件的 base
```

### Q: 如何重置配置？

**A:**

```bash
# 删除本地配置
rm vsub.yaml

# 删除用户配置
rm ~/.config/vsub/config.yaml

# 重新生成默认配置
vsub --init
```

## 输出问题

### Q: 如何生成 VTT 格式？

**A:**

```bash
vsub input.mp4 -f vtt
```

或在配置文件中设置：

```yaml
format: vtt
```

### Q: 字幕文件输出到哪里？

**A:** 默认输出到视频同目录，文件名为 `<视频名>.srt`。

例如：
- 输入: `/home/user/videos/lecture.mp4`
- 输出: `/home/user/videos/lecture.srt`

### Q: 如何自定义输出目录？

**A:**

```bash
# 方法1: 指定完整输出路径
vsub input.mp4 -o /path/to/output.srt

# 方法2: 在配置文件中设置
vsub --init
# 编辑 vsub.yaml，设置 output_dir
```

### Q: 字幕太长，如何换行？

**A:** 调整配置：

```yaml
# vsub.yaml
max_line_length: 40  # 每行最大字符数
max_line_count: 2    # 每段最多行数
```

## 性能问题

### Q: 需要多少内存？

**A:** 取决于模型：

| 模型 | 推荐内存 |
|------|----------|
| tiny | 2GB |
| base | 4GB |
| small | 6GB |
| medium | 8GB |
| large | 16GB |

### Q: 支持 GPU 加速吗？

**A:** 支持，需要：

1. NVIDIA GPU（CUDA）
2. 安装 CUDA 版本的 PyTorch
3. 自动检测，无需额外配置

验证 GPU 可用：
```python
python -c "import torch; print(torch.cuda.is_available())"
```

### Q: 处理一个视频需要多久？

**A:** 取决于：

- 视频时长
- 选择的模型
- CPU/GPU 性能

大致时间（10分钟视频，base模型，CPU）：
- 音频提取: 10-20 秒
- 语音识别: 30-60 秒
- 字幕生成: <1 秒

## 其他问题

### Q: 支持哪些语言？

**A:** 支持 Whisper 支持的所有语言：

- **中文**: zh
- **英语**: en
- **日语**: ja
- **韩语**: ko
- **法语**: fr
- **德语**: de
- **西班牙语**: es
- 等 99+ 种语言

完整列表: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py

### Q: 可以在 Docker 中使用吗？

**A:** 可以，创建 Dockerfile：

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install vsub

WORKDIR /workspace

ENTRYPOINT ["vsub"]
```

使用：
```bash
docker build -t vsub .
docker run -v $(pwd):/workspace vsub input.mp4
```

### Q: 如何报告 bug？

**A:**

1. 确认使用最新版本
2. 提供复现步骤
3. 提供错误信息（使用 `-v` 获取详细日志）
4. 在 GitHub Issues 提交

### Q: 如何贡献代码？

**A:**

1. Fork 仓库
2. 创建分支: `git checkout -b feature-name`
3. 提交更改: `git commit -am 'Add feature'`
4. 推送分支: `git push origin feature-name`
5. 提交 Pull Request

确保：
- 通过所有测试: `pytest`
- 代码格式正确: `black vsub/ tests/`
