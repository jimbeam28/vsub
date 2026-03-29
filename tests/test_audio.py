"""音频处理模块测试"""

from pathlib import Path
from unittest.mock import patch

import pytest

from vsub.audio import (
    AudioExtractor,
    cleanup_audio,
    parse_duration,
    temp_audio_path,
)


class TestAudioExtractor:
    """音频提取器测试"""

    def test_check_ffmpeg_success(self):
        """测试成功找到 ffmpeg"""
        with patch("vsub.audio.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            extractor = AudioExtractor()
            assert extractor.ffmpeg_path == Path("/usr/bin/ffmpeg")

    def test_check_ffmpeg_not_found(self):
        """测试未找到 ffmpeg"""
        with patch("vsub.audio.shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(RuntimeError, match="未找到 FFmpeg"):
                AudioExtractor()


class TestParseDuration:
    """时长解析测试"""

    def test_parse_duration_standard(self):
        """测试标准格式"""
        assert parse_duration("00:01:30.500") == 90.5
        assert parse_duration("01:00:00.000") == 3600.0
        assert parse_duration("00:00:12.340") == 12.34

    def test_parse_duration_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValueError):
            parse_duration("invalid")

    def test_parse_duration_wrong_parts(self):
        """测试错误的部分数"""
        with pytest.raises(ValueError):
            parse_duration("00:30")


class TestTempAudioPath:
    """临时音频路径测试"""

    def test_temp_audio_path(self, tmp_path):
        """测试生成临时路径"""
        video_path = tmp_path / "test_video.mp4"
        temp_path = temp_audio_path(video_path)

        assert temp_path.suffix == ".wav"
        assert "test_video" in temp_path.name
        assert temp_path.parent == Path("/tmp") or str(temp_path.parent).startswith("/tmp")


class TestCleanupAudio:
    """音频清理测试"""

    def test_cleanup_existing_file(self, tmp_path):
        """测试清理存在的文件"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_text("dummy")
        assert audio_file.exists()

        cleanup_audio(audio_file)
        assert not audio_file.exists()

    def test_cleanup_nonexistent_file(self, tmp_path):
        """测试清理不存在的文件"""
        audio_file = tmp_path / "nonexistent.wav"
        # 不应抛出异常
        cleanup_audio(audio_file)
