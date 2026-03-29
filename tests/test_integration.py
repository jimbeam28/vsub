"""集成测试"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsub.config import Config, OutputFormat
from vsub.core import determine_output_path, process_video


class TestDetermineOutputPath:
    """输出路径确定测试"""

    def test_default_output_path(self, tmp_path):
        """测试默认输出路径"""
        input_path = tmp_path / "video.mp4"
        config = Config()

        output = determine_output_path(input_path, config)

        assert output.parent == tmp_path
        assert output.name == "video.srt"

    def test_vtt_format(self, tmp_path):
        """测试 VTT 格式输出路径"""
        input_path = tmp_path / "video.mp4"
        config = Config(format=OutputFormat.VTT)

        output = determine_output_path(input_path, config)

        assert output.suffix == ".vtt"

    def test_custom_output_dir(self, tmp_path):
        """测试自定义输出目录"""
        input_path = tmp_path / "input" / "video.mp4"
        output_dir = tmp_path / "output"
        config = Config(output_dir=output_dir)

        output = determine_output_path(input_path, config)

        assert output.parent == output_dir
        assert output.name == "video.srt"


class TestProcessVideo:
    """视频处理流程测试"""

    @pytest.fixture
    def mock_video_info(self):
        """模拟视频信息"""
        info = MagicMock()
        info.resolution = "1920x1080"
        info.fps = 30.0
        info.duration = 10.0
        info.has_audio = True
        return info

    @pytest.fixture
    def mock_asr_words(self):
        """模拟 ASR 结果"""
        from vsub.asr import AsrWord
        return [
            AsrWord("Hello", 0.0, 0.5),
            AsrWord("world", 0.6, 1.0),
        ]

    def test_process_video_success(
        self,
        tmp_path,
        mock_video_info,
        mock_asr_words,
    ):
        """测试成功处理视频"""
        # 创建模拟视频文件
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")

        config = Config(keep_audio=True)  # 保留音频以便检查

        with patch("vsub.core.validate_video") as mock_validate, \
             patch("vsub.core.probe_video") as mock_probe, \
             patch("vsub.core.AudioExtractor") as mock_extractor, \
             patch("vsub.core.create_engine") as mock_create_engine:

            mock_probe.return_value = mock_video_info

            # 模拟音频提取
            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance

            # 模拟 ASR 引擎
            mock_engine = MagicMock()
            mock_engine.is_available.return_value = True
            mock_engine.transcribe.return_value = mock_asr_words
            mock_create_engine.return_value = mock_engine

            output = process_video(video_file, config)

            assert output.exists()
            assert output.suffix == ".srt"

            content = output.read_text()
            assert "Hello" in content or "1" in content

    def test_process_video_no_audio(self, tmp_path, mock_video_info):
        """测试无音频视频"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        mock_video_info.has_audio = False
        config = Config()

        with patch("vsub.core.validate_video"), \
             patch("vsub.core.probe_video") as mock_probe:
            mock_probe.return_value = mock_video_info

            with pytest.raises(RuntimeError, match="没有音频"):
                process_video(video_file, config)


class TestConfigIntegration:
    """配置集成测试"""

    def test_full_config_flow(self, tmp_path):
        """测试完整配置流程"""
        # 创建配置文件
        config_file = tmp_path / "vsub.yaml"
        config_file.write_text("""
format: vtt
model: small
language: en
max_line_length: 60
""")

        with patch("vsub.config.Config.find_config_file") as mock_find:
            mock_find.return_value = config_file

            config = Config.load()

            assert config.format == OutputFormat.VTT
            assert config.model.value == "small"
            assert config.language == "en"
            assert config.max_line_length == 60
