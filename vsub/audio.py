"""音频处理模块"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from tqdm import tqdm


class AudioExtractor:
    """音频提取器"""

    def __init__(self):
        self.ffmpeg_path = self._check_ffmpeg()

    @staticmethod
    def _check_ffmpeg() -> Path:
        """检查 FFmpeg 是否可用"""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("未找到 FFmpeg")
        return Path(ffmpeg_path)

    def extract_to_wav(
        self, video_path: Path, output_path: Path, show_progress: bool = True
    ) -> None:
        """提取音频为 WAV 格式（PCM 16-bit, 16kHz, mono）"""
        # 如果输出文件已存在，先删除
        if output_path.exists():
            output_path.unlink()

        # 获取视频时长
        duration = self._get_video_duration(video_path)

        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-i", str(video_path),
            "-vn",  # 无视频
            "-acodec", "pcm_s16le",  # PCM 16-bit 小端
            "-ar", "16000",  # 16kHz 采样率
            "-ac", "1",  # 单声道
            "-progress", "pipe:1",  # 输出进度到 stdout
            str(output_path),
        ]

        if show_progress and duration > 0:
            self._run_with_progress(cmd, duration)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"音频提取失败: {result.stderr}")

        # 验证输出文件
        if not output_path.exists():
            raise RuntimeError("输出文件未生成")

        if output_path.stat().st_size == 0:
            raise RuntimeError("输出文件为空")

    def _get_video_duration(self, video_path: Path) -> float:
        """获取视频时长（秒）"""
        cmd = [
            str(self.ffmpeg_path),
            "-i", str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # FFmpeg 输出到 stderr
        for line in result.stderr.split("\n"):
            if "Duration: " in line:
                match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    seconds = float(match.group(3))
                    return hours * 3600 + minutes * 60 + seconds
        return 0.0

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

                # 解析 out_time_us
                if line.startswith("out_time_us="):
                    time_us = int(line.strip().split("=")[1])
                    current_time = time_us / 1_000_000  # 转换为秒
                    percent = min(int(current_time / duration * 100), 100)
                    if percent > last_percent:
                        pbar.update(percent - last_percent)
                        last_percent = percent

        # 等待进程结束并检查返回值
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"音频提取失败: {stderr}")

    def get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        cmd = [
            str(self.ffmpeg_path),
            "-i", str(audio_path),
            "-f", "null",
            "-",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # FFmpeg 输出到 stderr
        for line in result.stderr.split("\n"):
            if "Duration: " in line:
                # 解析 Duration: 00:00:12.34
                start = line.find("Duration: ") + 10
                end = line.find(",", start)
                if end == -1:
                    end = len(line)
                time_str = line[start:end].strip()
                return parse_duration(time_str)

        raise RuntimeError("无法获取音频时长")


def parse_duration(time_str: str) -> float:
    """解析时长字符串 HH:MM:SS.sss"""
    parts = time_str.split(":")
    if len(parts) != 3:
        raise ValueError(f"无效的时长格式: {time_str}")

    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])

    return hours * 3600.0 + minutes * 60.0 + seconds


def temp_audio_path(video_path: Path) -> Path:
    """生成临时音频文件路径"""
    stem = video_path.stem
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / f"{stem}_{temp_file_id()}.wav"


def temp_file_id() -> str:
    """生成临时文件 ID"""
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def cleanup_audio(path: Path) -> None:
    """清理临时音频文件"""
    if path.exists():
        try:
            path.unlink()
        except OSError as e:
            print(f"警告: 无法删除临时音频文件 {path}: {e}")
