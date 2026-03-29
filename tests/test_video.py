"""视频处理模块测试"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsub.video import (
    VideoInfo,
    check_ffmpeg,
    check_ffprobe,
    parse_video_info,
    probe_video,
    validate_video,
)


class TestVideoInfo:
    """视频信息类测试"""

    def test_video_info_creation(self):
        """测试视频信息创建"""
        info = VideoInfo(
            path=Path("test.mp4"),
            duration=120.5,
            width=1920,
            height=1080,
            has_audio=True,
            audio_codec="aac",
            video_codec="h264",
            fps=30.0,
        )
        assert info.resolution == "1920x1080"
        assert "1920x1080" in repr(info)
        assert "30.00fps" in repr(info)

    def test_video_info_default(self):
        """测试视频信息默认值"""
        info = VideoInfo(path=Path("test.mp4"))
        assert info.duration == 0.0
        assert info.width == 0
        assert info.height == 0
        assert info.has_audio is False


class TestCheckFFmpeg:
    """FFmpeg 检查测试"""

    def test_check_ffmpeg_success(self):
        """测试成功找到 ffmpeg"""
        with patch("vsub.video.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            result = check_ffmpeg()
            assert result == Path("/usr/bin/ffmpeg")

    def test_check_ffmpeg_not_found(self):
        """测试未找到 ffmpeg"""
        with patch("vsub.video.shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(RuntimeError, match="未找到 FFmpeg"):
                check_ffmpeg()

    def test_check_ffprobe_success(self):
        """测试成功找到 ffprobe"""
        with patch("vsub.video.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffprobe"
            result = check_ffprobe()
            assert result == Path("/usr/bin/ffprobe")


class TestProbeVideo:
    """视频探测测试"""

    def test_parse_video_info(self):
        """测试解析视频信息"""
        data = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30000/1001",
                    "duration": "120.5",
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                },
            ],
            "format": {
                "duration": "120.5",
            },
        }

        info = parse_video_info(Path("test.mp4"), data)
        assert info.width == 1920
        assert info.height == 1080
        assert info.has_audio is True
        assert info.video_codec == "h264"
        assert info.audio_codec == "aac"
        assert abs(info.fps - 29.97) < 0.01  # 30000/1001 ≈ 29.97

    def test_parse_video_info_no_audio(self):
        """测试无音频的视频"""
        data = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                },
            ],
            "format": {},
        }

        info = parse_video_info(Path("test.mp4"), data)
        assert info.has_audio is False
        assert info.audio_codec is None

    def test_parse_video_info_no_video_stream(self):
        """测试无视频流（只有音频）"""
        data = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                },
            ],
            "format": {},
        }

        info = parse_video_info(Path("test.mp4"), data)
        assert info.width == 0
        assert info.height == 0
        assert info.has_audio is True


class TestValidateVideo:
    """视频验证测试"""

    def test_validate_nonexistent_file(self, tmp_path):
        """测试不存在的文件"""
        with pytest.raises(FileNotFoundError):
            validate_video(tmp_path / "nonexistent.mp4")

    def test_validate_directory(self, tmp_path):
        """测试目录而非文件"""
        with pytest.raises(ValueError, match="不是文件"):
            validate_video(tmp_path)
