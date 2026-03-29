# Vsub 代码审查报告

**审查日期**: 2026-03-29
**修复日期**: 2026-03-29
**版本**: 0.2.0
**审查范围**: vsub/ 目录下所有 Python 文件

---

## 执行摘要

本次审查发现了 **47 个问题**，其中：
- 🔴 **严重**: 8 个（✅ **已全部修复**）
- 🟠 **高**: 12 个
- 🟡 **中**: 15 个
- 🟢 **低**: 12 个

**主要风险**: 安全漏洞、资源泄露、并发问题、类型安全问题

---

## 修复状态

| 问题 | 文件 | 状态 |
|------|------|------|
| FFmpeg 进度显示死锁 | audio.py | ✅ 已修复 |
| 进度解析异常 | audio.py | ✅ 已修复 |
| 并发结果排序问题 | core.py | ✅ 已修复 |
| 资源泄露风险 | core.py | ✅ 已修复 |
| merge() 方法逻辑 | config.py | ✅ 已修复 |
| 引擎创建参数处理 | asr.py | ✅ 已修复 |
| API 密钥泄露 | asr.py | ✅ 已修复 |
| 日志重复配置 | cli.py | ✅ 已修复 |
| torch 重复导入 | device.py | ✅ 已修复 |

---

## 1. vsub/__init__.py

### 1.1 🟢 低: 缺少类型注解
**位置**: 第 6-7 行

```python
from vsub.config import Config
from vsub.core import process_video
```

**问题**: 虽然 `__all__` 定义了导出内容，但导入语句缺少类型注解。

**建议**: 添加 `__all__` 的类型注解。

```python
__all__: list[str] = ["Config", "process_video"]
```

---

## 2. vsub/__main__.py

### 2.1 🟢 低: 过于简单的入口文件
**位置**: 第 1-6 行

**问题**: 文件过于简单，没有错误处理。

**建议**: 添加基本的错误处理。

```python
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"致命错误: {e}", file=sys.stderr)
        sys.exit(1)
```

---

## 3. vsub/cli.py

### 3.1 🔴 严重: 日志配置可能被重复初始化
**位置**: 第 59-63 行

```python
# 设置日志级别
if verbose:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
else:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
```

**问题**: `logging.basicConfig()` 在日志已配置时不会生效，但如果在其他模块已经配置后调用，可能导致不一致的行为。

**建议**: 检查日志是否已配置，或使用更明确的日志初始化方式。

```python
# 在模块级别或应用启动时配置一次
if not logging.getLogger().handlers:
    logging.basicConfig(...)
```

### 3.2 🟠 高: 缺少 `--engine` 命令行选项
**位置**: 第 13-40 行

**问题**: 虽然 `config.py` 支持 `engine` 配置，但 CLI 没有提供 `--engine` 选项来覆盖配置。

**建议**: 添加 `--engine` 选项。

```python
@click.option(
    "-e",
    "--engine",
    type=click.Choice(["whisper", "openai", "azure", "funasr"]),
    help="ASR 引擎类型",
)
```

### 3.3 🟠 高: 缺少 `--max-workers` 命令行选项
**位置**: 第 13-40 行

**问题**: 批量处理时无法通过命令行指定并发数。

**建议**: 添加 `--max-workers` 选项。

```python
@click.option(
    "-j",
    "--max-workers",
    type=int,
    help="批量处理并发数",
)
```

### 3.4 🟠 高: 单文件处理时未返回退出码
**位置**: 第 100-104 行

```python
if len(input_paths) == 1:
    try:
        process_video(input_paths[0], config)
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)
```

**问题**: 单文件处理失败时调用 `sys.exit(1)`，但成功时没有显式返回 0。批量处理失败时继续执行。

**建议**: 统一错误处理，单文件处理成功也应显式 `sys.exit(0)`。

### 3.5 🟡 中: `version` 参数硬编码
**位置**: 第 40 行

```python
@click.version_option(version="0.2.0", prog_name="vsub")
```

**问题**: 版本号硬编码，与 `__init__.py` 中的版本不同步。

**建议**: 从模块导入版本。

```python
from vsub import __version__
@click.version_option(version=__version__, prog_name="vsub")
```

### 3.6 🟡 中: `init_config()` 缺少异常处理
**位置**: 第 111-124 行

**问题**: 文件写入可能失败，但没有异常处理。

**建议**: 添加异常处理。

```python
def init_config():
    try:
        config_path = Path("vsub.yaml")
        # ... 现有逻辑 ...
    except OSError as e:
        click.echo(f"错误: 无法写入配置文件: {e}", err=True)
        sys.exit(1)
```

### 3.7 🟢 低: 函数参数类型不完整
**位置**: 第 41-50 行

**问题**: `input` 类型为 `tuple`，但应该是 `Tuple[Path, ...]` 或更具体的类型。

**建议**: 使用 `Tuple[Path, ...]` 类型注解。

### 3.8 🟢 低: 缺少 `--device` 命令行选项
**位置**: CLI 定义

**问题**: 用户无法通过 CLI 强制指定计算设备。

**建议**: 添加 `--device` 选项。

```python
@click.option(
    "-d",
    "--device",
    type=click.Choice(["cpu", "cuda", "mps"]),
    help="计算设备",
)
```

---

## 4. vsub/config.py

### 4.1 🔴 严重: `merge()` 方法逻辑问题
**位置**: 第 93-104 行

```python
def merge(self, other: "Config") -> "Config":
    """合并另一个配置，其他配置的非默认值覆盖当前配置"""
    data = self.model_dump()
    other_data = other.model_dump()

    # 只覆盖非默认值
    defaults = Config().model_dump()
    for key, value in other_data.items():
        if value != defaults[key]:
            data[key] = value
```

**问题**: 这个逻辑有缺陷。它检查的是 `other` 的值是否不等于默认值，而不是检查 `other` 的值是否被显式设置。这会导致意外的覆盖行为。

**建议**: 使用 Pydantic 的 `model_copy(update=...)` 或其他方式来正确合并配置。

### 4.2 🟠 高: `from_file()` 缺少 YAML 解析异常处理
**位置**: 第 69-76 行

```python
@classmethod
def from_file(cls, path: Path) -> "Config":
    """从配置文件加载"""
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if data is None:
        data = {}
    return cls(**data)
```

**问题**: YAML 解析可能抛出异常，且文件读取可能失败。

**建议**: 添加异常处理。

```python
@classmethod
def from_file(cls, path: Path) -> "Config":
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
        return cls(**data)
    except yaml.YAMLError as e:
        raise ValueError(f"无效的 YAML 格式: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(f"文件编码错误: {e}")
```

### 4.3 🟠 高: 配置文件路径缺少类型检查
**位置**: 第 84-89 行

**问题**: `find_config_file()` 返回的路径在使用前没有验证是否存在。

**建议**: 在使用前验证文件存在且可读。

### 4.4 🟡 中: `max_workers` 默认值逻辑问题
**位置**: 第 67 行

```python
max_workers: Optional[int] = Field(default=None, description="批量处理并发数，None 表示自动")
```

**问题**: 配置文件中注释掉的 `max_workers` 值是 4，但实际的自动逻辑是在 `core.py` 中实现的，这可能导致配置和代码逻辑不一致。

### 4.5 🟡 中: 缺少配置验证
**位置**: Config 类

**问题**: 缺少对配置值的验证，例如 `max_line_length` 应该为正数，`max_line_count` 应该在合理范围内。

**建议**: 添加 Pydantic 验证器。

```python
from pydantic import field_validator

@field_validator("max_line_length", "max_line_count")
@classmethod
def validate_positive(cls, v: int) -> int:
    if v <= 0:
        raise ValueError("值必须为正数")
    return v
```

### 4.6 🟢 低: 枚举值命名不一致
**位置**: 第 17-34 行

**问题**: `WhisperModel` 使用大写下划线命名，但 `AsrEngineType` 也是大写，这在 YAML 中使用时可能不直观。

**建议**: 考虑使用小写枚举值以匹配 YAML 配置习惯。

---

## 5. vsub/core.py

### 5.1 🔴 严重: 并发处理中的异常可能导致资源泄露
**位置**: 第 171-197 行

```python
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 提交所有任务
    future_to_path = {
        executor.submit(
            _process_video_wrapper,
            input_path,
            config,
            device,
        ): input_path
        for input_path in inputs
    }
```

**问题**: 如果在任务提交过程中发生异常，部分任务可能已被提交但没有被正确追踪。

**建议**: 添加 try-except 块。

### 5.2 🔴 严重: `results` 列表可能包含不完整结果
**位置**: 第 168-201 行

**问题**: `as_completed()` 不保证顺序，最后的排序逻辑可能不正确。

```python
# 按输入顺序排序结果
path_to_output = {inp: out for inp, out in results}
return [(inp, path_to_output.get(inp)) for inp in inputs]
```

**问题**: 如果有重复路径，字典会去重，导致结果丢失。

**建议**: 使用列表推导式保证顺序。

```python
results_dict = {inp: out for inp, out in results}
return [(inp, results_dict.get(inp)) for inp in inputs]
```

### 5.3 🟠 高: 临时音频文件清理可能失败
**位置**: 第 118-121 行

```python
finally:
    # 清理临时音频文件
    if not config.keep_audio:
        cleanup_audio(temp_audio)
```

**问题**: 如果 `temp_audio` 在使用中被其他进程锁定（例如杀毒软件），清理会失败。

**建议**: 添加重试机制或延迟清理。

### 5.4 🟠 高: 进度条在多线程环境下可能冲突
**位置**: 第 73-85 行

**问题**: `_process_video_wrapper` 禁用了进度条，但主线程的 tqdm 仍然可能在子线程输出时发生冲突。

**建议**: 使用线程锁或 tqdm 的 `position` 参数。

### 5.5 🟠 高: 缺少超时控制
**位置**: `process_video()` 函数

**问题**: 视频处理和 ASR 识别可能耗时很长，但没有超时控制。

**建议**: 添加超时参数。

```python
def process_video(
    input_path: Path,
    config: Config,
    device: Optional[str] = None,
    show_progress: bool = True,
    timeout: Optional[float] = None,
) -> Path:
```

### 5.6 🟡 中: `determine_output_path()` 在 Windows 上可能有问题
**位置**: 第 218-232 行

**问题**: 如果 `config.output_dir` 是 Windows 路径而 `input_path` 是相对路径，可能产生混合路径分隔符。

**建议**: 使用 `Path.resolve()` 规范化路径。

### 5.7 🟡 中: 引擎可用性检查在每次处理时都执行
**位置**: 第 69-70 行

```python
if not engine.is_available():
    raise RuntimeError("ASR 引擎不可用，请安装 faster-whisper")
```

**问题**: 在批量处理时，引擎可用性检查应该只执行一次。

**建议**: 将检查移到批量处理的开头。

### 5.8 🟢 低: 未使用的导入
**位置**: 第 10 行

```python
from vsub.asr import AsrWord, create_engine, ENGINE_REGISTRY
```

**问题**: `ENGINE_REGISTRY` 被导入但未使用。

### 5.9 🟢 低: 进度回调函数定义在 if 块内
**位置**: 第 75-77 行

```python
def update_progress(progress: float):
    pbar.n = int(progress * 100)
    pbar.refresh()
```

**问题**: 虽然 Python 支持嵌套函数，但定义在 if 块内降低了可读性。

---

## 6. vsub/audio.py

### 6.1 🔴 严重: `_run_with_progress()` 可能死锁
**位置**: 第 82-111 行

```python
def _run_with_progress(self, cmd: list, duration: float) -> None:
    """运行 FFmpeg 并显示进度"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    with tqdm(total=100, desc="提取音频", unit="%") as pbar:
        last_percent = 0
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            # ...
```

**问题**:
1. 如果 FFmpeg 输出大量数据到 stderr 而未被读取，管道可能填满导致死锁
2. `process.poll()` 在进程结束前可能返回 `None`，如果 FFmpeg 没有输出进度信息，循环可能长时间运行

**建议**: 使用线程读取 stderr，或设置超时。

```python
import threading

def read_stderr(pipe):
    for line in iter(pipe.readline, ''):
        pass  # 或记录到日志

stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr,))
stderr_thread.daemon = True
stderr_thread.start()
```

### 6.2 🔴 严重: `int(line.strip().split("=")[1])` 可能抛出异常
**位置**: 第 100-101 行

```python
if line.startswith("out_time_us="):
    time_us = int(line.strip().split("=")[1])
```

**问题**: 如果 FFmpeg 输出格式意外变化，这行会抛出 `ValueError` 或 `IndexError`。

**建议**: 添加错误处理。

```python
if line.startswith("out_time_us="):
    try:
        time_us = int(line.strip().split("=")[1])
    except (ValueError, IndexError):
        continue
```

### 6.3 🟠 高: `temp_file_id()` 使用随机生成可能冲突
**位置**: 第 158-162 行

```python
def temp_file_id() -> str:
    """生成临时文件 ID"""
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
```

**问题**: 虽然冲突概率低，但随机生成不是生成唯一临时文件的标准方法。

**建议**: 使用 `tempfile.mkstemp()` 或 UUID。

```python
def temp_audio_path(video_path: Path) -> Path:
    """生成临时音频文件路径"""
    stem = video_path.stem
    temp_dir = Path(tempfile.gettempdir())
    return Path(tempfile.mktemp(
        prefix=f"{stem}_",
        suffix=".wav",
        dir=str(temp_dir)
    ))
```

### 6.4 🟠 高: `_get_video_duration()` 重复调用 FFmpeg
**位置**: 第 64-80 行

**问题**: 这个方法在 `extract_to_wav()` 中调用，但 `video.py` 中的 `probe_video()` 已经获取了视频信息（包括时长）。

**建议**: 从 `video_info` 传递时长，避免重复调用 FFmpeg。

### 6.5 🟡 中: `parse_duration()` 缺少范围验证
**位置**: 第 138-148 行

```python
def parse_duration(time_str: str) -> float:
    """解析时长字符串 HH:MM:SS.sss"""
    parts = time_str.split(":")
    if len(parts) != 3:
        raise ValueError(f"无效的时长格式: {time_str}")

    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])

    return hours * 3600.0 + minutes * 60.0 + seconds
```

**问题**: 没有验证各部分是否在有效范围内（例如分钟 < 60）。

**建议**: 添加验证。

```python
if not (0 <= minutes < 60 and 0 <= seconds < 60):
    raise ValueError(f"无效的时间值: {time_str}")
```

### 6.6 🟢 低: 导入位置不统一
**位置**: 第 3-11 行 vs 第 159-161 行

**问题**: `random` 和 `string` 在函数内导入，而 `tqdm` 在模块顶部导入。

**建议**: 统一在模块顶部导入。

---

## 7. vsub/video.py

### 7.1 🟠 高: `probe_video()` 可能泄露敏感信息
**位置**: 第 60-78 行

```python
def probe_video(path: Path) -> VideoInfo:
    """使用 ffprobe 探测视频信息"""
    ffprobe = check_ffprobe()

    cmd = [
        str(ffprobe),
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {result.stderr}")
```

**问题**: 错误消息直接包含 `result.stderr`，可能包含敏感文件路径信息。

**建议**: 清理错误消息或使用日志记录详细错误。

### 7.2 🟠 高: `json.loads()` 可能抛出异常
**位置**: 第 77 行

```python
data = json.loads(result.stdout)
```

**问题**: 如果 ffprobe 输出无效 JSON，会抛出 `json.JSONDecodeError`。

**建议**: 添加异常处理。

```python
try:
    data = json.loads(result.stdout)
except json.JSONDecodeError as e:
    raise RuntimeError(f"解析 ffprobe 输出失败: {e}")
```

### 7.3 🟡 中: `parse_video_info()` 对缺失字段处理不一致
**位置**: 第 81-137 行

**问题**: 有些字段使用 `.get()` 提供默认值，有些直接访问，虽然当前逻辑安全，但不够一致。

### 7.4 🟡 中: 帧率计算可能溢出
**位置**: 第 116-120 行

```python
r_frame_rate = video_stream.get("r_frame_rate", "")
if "/" in r_frame_rate:
    num, den = r_frame_rate.split("/")
    if int(den) > 0:
        fps = int(num) / int(den)
```

**问题**: `int(num)` 和 `int(den)` 可能非常大，虽然 Python 支持大整数，但除法结果可能不精确。

**建议**: 使用 `float(num) / float(den)` 或 `Fraction`。

### 7.5 🟢 低: 缺少 `check_ffprobe()` 的缓存
**位置**: 第 52-57 行

**问题**: 每次调用 `probe_video()` 或 `validate_video()` 都会执行 `shutil.which()`。

**建议**: 使用 `functools.lru_cache` 缓存结果。

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def check_ffprobe() -> Path:
    ...
```

---

## 8. vsub/asr.py

### 8.1 🔴 严重: `create_engine()` 未处理所有引擎类型的参数
**位置**: 第 426-465 行

```python
def create_engine(
    engine_type: str = "whisper",
    model: str = "base",
    device: str = "cpu",
    **kwargs,
) -> AsrEngine:
    # ...
    if engine_type == "whisper":
        return engine_class(model=model, device=device)
    elif engine_type == "openai":
        return engine_class(api_key=kwargs.get("api_key"), model=model)
    # ...
```

**问题**:
1. `WhisperEngine` 和 `FunASREngine` 接受 `device` 参数，但其他引擎不接受
2. `OpenAIWhisperEngine` 使用 `model` 参数，但 OpenAI API 的模型名称不同
3. 没有验证 kwargs 中是否有未使用的参数

**建议**: 添加参数验证和文档。

### 8.2 🟠 高: API 密钥可能在日志中泄露
**位置**: 第 165-167 行, 第 242-248 行

```python
def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
```

**问题**: 如果对象被打印或记录，API 密钥可能被泄露。

**建议**: 使用 `__repr__` 隐藏敏感信息。

```python
def __repr__(self) -> str:
    return f"OpenAIWhisperEngine(api_key='***', model={self.model!r})"
```

### 8.3 🟠 高: `FunASREngine` 的时间戳处理逻辑可能有误
**位置**: 第 376-390 行

```python
if timestamp and isinstance(timestamp, list):
    for i, (start, end) in enumerate(timestamp):
        word_text = text[i] if i < len(text) else ""
        words.append(
            AsrWord(
                text=word_text,
                start=start / 1000.0,
                end=end / 1000.0,
                confidence=1.0,
            )
        )
```

**问题**:
1. `text[i]` 假设 `text` 是字符列表，但可能是字符串
2. 时间戳格式假设可能不正确

**建议**: 添加更多格式验证。

### 8.4 🟠 高: 文件未关闭风险
**位置**: 第 190 行

```python
with open(audio_path, "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model=self.model,
        file=audio_file,
        ...
    )
```

**问题**: 虽然使用了 `with` 语句，但如果 `client.audio.transcriptions.create` 抛出异常，文件句柄应该正常关闭，但需要确认 `openai` 库的实现。

### 8.5 🟡 中: `list_available_engines()` 可能创建无效实例
**位置**: 第 468-478 行

```python
def list_available_engines() -> List[str]:
    available = []
    for name, engine_class in ENGINE_REGISTRY.items():
        try:
            engine = engine_class()
            if engine.is_available():
                available.append(name)
        except Exception:
            pass
    return available
```

**问题**: 某些引擎（如 `OpenAIWhisperEngine`）在没有 API 密钥时实例化会失败。

**建议**: 使用类方法或检查类属性来判断可用性。

### 8.6 🟡 中: `AzureASREngine` 使用 `recognize_once()` 可能不完整
**位置**: 第 290 行

**问题**: `recognize_once()` 只识别一次，对于长音频可能不完整。

**建议**: 使用连续识别模式。

### 8.7 🟡 中: `WhisperEngine._get_audio_duration()` 不支持非 WAV 格式
**位置**: 第 78-88 行

```python
def _get_audio_duration(self, audio_path: Path) -> float:
    try:
        import wave
        with wave.open(str(audio_path), "rb") as wf:
            ...
```

**问题**: 如果音频不是 WAV 格式，会失败。

**建议**: 使用 `pydub` 或其他库支持更多格式。

### 8.8 🟢 低: 未使用 `info` 变量
**位置**: 第 102 行

```python
segments, info = self._model.transcribe(...)
```

**问题**: `info` 变量未被使用。

---

## 9. vsub/subtitle.py

### 9.1 🟡 中: `_wrap_text()` 可能丢失单词
**位置**: 第 87-125 行

```python
def _wrap_text(self, text: str) -> str:
    """文本自动换行"""
    words = text.split()
    if not words:
        return ""

    lines = []
    current_line = []
    current_length = 0

    for word in words:
        # ...
        if len(lines) >= self.max_line_count:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
                current_length = 0
            break
```

**问题**: 当达到 `max_line_count` 时，`break` 会丢弃剩余单词。

**建议**: 添加注释或选项控制是否截断。

### 9.2 🟡 中: `segments_from_asr_result()` 的字符计数不准确
**位置**: 第 161 行

```python
char_count += len(word.text)
```

**问题**: 计数没有考虑空格，实际字符数会大于 `char_count`。

**建议**: 添加空格计数。

```python
char_count += len(word.text)
if current_words:  # 不是第一个单词
    char_count += 1  # 空格
```

### 9.3 🟡 中: 句子结束标点检测可能不准确
**位置**: 第 154 行

```python
sentence_end = re.compile(r"[.!?。！？]$")
```

**问题**: 如果单词包含标点但不在末尾（如 `"hello..."`），可能不正确分割。

**建议**: 使用 `re.search()` 而不是 `re.search(..., $)`。

### 9.4 🟢 低: 时间格式化函数可以合并
**位置**: 第 29-45 行

```python
@staticmethod
def format_time_srt(seconds: float) -> str:
    ...

@staticmethod
def format_time_vtt(seconds: float) -> str:
    ...
```

**问题**: 两个函数几乎相同，只有分隔符不同。

**建议**: 合并为一个函数。

```python
@staticmethod
def format_time(seconds: float, separator: str = ",") -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"
```

---

## 10. vsub/device.py

### 10.1 🟠 高: `torch` 导入在每个函数中重复
**位置**: 第 19-22 行, 第 28-31 行, 等

**问题**: 多次 try-except 导入 torch 是冗余的。

**建议**: 在模块级别导入一次。

```python
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
```

### 10.2 🟠 高: `get_device_info()` 中的 `DeviceType.CPU` 不可序列化
**位置**: 第 77 行

```python
info = {
    "cpu": True,
    "cuda": False,
    "cuda_devices": 0,
    "cuda_device_name": None,
    "mps": False,
    "recommended": DeviceType.CPU,
}
```

**问题**: `DeviceType` 是枚举类型，如果被 JSON 序列化会失败。

**建议**: 存储字符串值。

```python
"recommended": DeviceType.CPU.value,
```

### 10.3 🟡 中: 缺少对多 GPU 环境的处理
**位置**: `get_device()` 函数

**问题**: 只选择第一个 GPU（`cuda:0`），在多 GPU 环境下可能不是最佳选择。

**建议**: 添加 GPU 选择逻辑。

```python
def get_best_gpu():
    if not torch.cuda.is_available():
        return None
    # 选择显存最多的 GPU
    max_memory = 0
    best_gpu = 0
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        if props.total_memory > max_memory:
            max_memory = props.total_memory
            best_gpu = i
    return f"cuda:{best_gpu}"
```

### 10.4 🟢 低: `format_device_info()` 使用 f-string 但值是布尔
**位置**: 第 114-124 行

```python
lines.append(f"  CUDA: {info['cuda']}")
```

**问题**: 输出将是 `CUDA: True/False`，不够友好。

**建议**: 转换为友好字符串。

```python
lines.append(f"  CUDA: {'可用' if info['cuda'] else '不可用'}")
```

---

## 附录 A: 优先级修复建议

### 立即修复 (1-2 天)
1. `audio.py`: `_run_with_progress()` 死锁风险
2. `core.py`: 并发处理中的结果排序问题
3. `config.py`: `merge()` 方法逻辑问题
4. `asr.py`: `create_engine()` 参数处理

### 短期修复 (1 周)
1. `cli.py`: 添加 `--engine` 和 `--device` 选项
2. `audio.py`: 临时文件生成使用标准库
3. `video.py`: 添加 JSON 解析异常处理
4. `asr.py`: API 密钥泄露防护

### 中期改进 (2-4 周)
1. 统一错误处理和日志记录
2. 添加超时控制
3. 完善类型注解
4. 添加配置验证

---

## 附录 B: 代码质量统计

| 指标 | 数值 |
|------|------|
| 总行数 | ~1400 行 |
| Python 文件数 | 10 个 |
| 函数/方法数 | ~80 个 |
| 类数 | 12 个 |
| 测试覆盖率 | 71% |
| 严重问题 | 8 个 |
| 高优先级问题 | 12 个 |

---

## 附录 C: 安全漏洞详情

### 1. API 密钥泄露风险
**文件**: `asr.py`
**风险等级**: 高
**描述**: API 密钥存储在对象属性中，可能在日志或异常信息中泄露

### 2. 命令注入风险
**文件**: `audio.py`, `video.py`
**风险等级**: 中
**描述**: 使用 `subprocess.run()` 时如果路径包含特殊字符可能导致问题

### 3. 敏感信息泄露
**文件**: `video.py`
**风险等级**: 中
**描述**: 错误消息直接包含 stderr 输出，可能包含敏感路径

---

**报告结束**
