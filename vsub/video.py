"""视频处理模块"""

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional


class VideoInfo:
    """视频信息"""

    def __init__(
        self,
        path: Path,
        duration: float = 0.0,
        width: int = 0,
        height: int = 0,
        has_audio: bool = False,
        audio_codec: Optional[str] = None,
        video_codec: Optional[str] = None,
        fps: float = 0.0,
    ):
        self.path = path
        self.duration = duration
        self.width = width
        self.height = height
        self.has_audio = has_audio
        self.audio_codec = audio_codec
        self.video_codec = video_codec
        self.fps = fps

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    def __repr__(self) -> str:
        return (
            f"VideoInfo({self.path.name}, {self.resolution}, "
            f"{self.fps:.2f}fps, {self.duration:.2f}s, audio={self.has_audio})"
        )


@lru_cache(maxsize=1)
def check_ffmpeg() -> Path:
    """检查 FFmpeg 是否可用（带缓存）"""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("未找到 FFmpeg，请确保 FFmpeg 已安装并在 PATH 中")
    return Path(ffmpeg_path)


@lru_cache(maxsize=1)
def check_ffprobe() -> Path:
    """检查 ffprobe 是否可用（带缓存）"""
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        raise RuntimeError("未找到 ffprobe，请确保 FFmpeg 已安装并在 PATH 中")
    return Path(ffprobe_path)


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
        # 清理错误消息，移除敏感路径信息
        error_msg = _sanitize_ffprobe_error(result.stderr)
        raise RuntimeError(f"ffprobe 失败: {error_msg}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 ffprobe 输出失败: {e}")

    return parse_video_info(path, data)


def _sanitize_ffprobe_error(error_msg: str) -> str:
    """清理 ffprobe 错误消息中的敏感信息"""
    lines = error_msg.split('\n')
    sanitized = []
    for line in lines[:3]:  # 只保留前3行
        # 如果行太长，截断
        if len(line) > 150:
            line = line[:150] + "..."
        sanitized.append(line)
    return '\n'.join(sanitized)


def parse_video_info(path: Path, data: dict) -> VideoInfo:
    """解析 ffprobe 输出"""
    streams = data.get("streams", [])
    format_info = data.get("format", {})

    # 查找视频流
    video_stream = None
    audio_stream = None

    for stream in streams:
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            video_stream = stream
        elif codec_type == "audio":
            audio_stream = stream

    # 获取时长
    duration = 0.0
    if "duration" in format_info:
        duration = float(format_info["duration"])
    elif video_stream and "duration" in video_stream:
        duration = float(video_stream["duration"])

    # 获取分辨率
    width = 0
    height = 0
    fps = 0.0
    video_codec = None

    if video_stream:
        width = video_stream.get("width", 0)
        height = video_stream.get("height", 0)
        video_codec = video_stream.get("codec_name")

        # 解析帧率（使用 float 避免溢出）
        r_frame_rate = video_stream.get("r_frame_rate", "")
        if "/" in r_frame_rate:
            try:
                num, den = r_frame_rate.split("/")
                den_val = float(den)
                if den_val > 0:
                    fps = float(num) / den_val
            except (ValueError, ZeroDivisionError):
                fps = 0.0

    # 获取音频信息
    audio_codec = None
    has_audio = audio_stream is not None
    if audio_stream:
        audio_codec = audio_stream.get("codec_name")

    return VideoInfo(
        path=path,
        duration=duration,
        width=width,
        height=height,
        has_audio=has_audio,
        audio_codec=audio_codec,
        video_codec=video_codec,
        fps=fps,
    )


def validate_video(path: Path) -> None:
    """验证视频文件"""
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    if not path.is_file():
        raise ValueError(f"不是文件: {path}")

    # 使用 ffprobe 验证
    probe_video(path)
