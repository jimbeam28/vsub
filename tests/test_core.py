"""核心模块单元测试"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsub.config import Config, OutputFormat, WhisperModel
from vsub.core import determine_output_path, process_video, process_videos


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

    def test_nested_input(self, tmp_path):
        """测试嵌套目录输入"""
        input_path = tmp_path / "2024" / "01" / "video.mp4"
        config = Config()

        output = determine_output_path(input_path, config)

        assert output.name == "video.srt"
        assert output.parent == input_path.parent


class TestProcessVideo:
    """视频处理测试"""

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

        config = Config(keep_audio=True)

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

    def test_process_video_asr_not_available(self, tmp_path, mock_video_info):
        """测试 ASR 引擎不可用"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        config = Config()

        with patch("vsub.core.validate_video"), \
             patch("vsub.core.probe_video") as mock_probe, \
             patch("vsub.core.AudioExtractor") as mock_extractor, \
             patch("vsub.core.create_engine") as mock_create_engine:

            mock_probe.return_value = mock_video_info

            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance

            mock_engine = MagicMock()
            mock_engine.is_available.return_value = False
            mock_create_engine.return_value = mock_engine

            with pytest.raises(RuntimeError, match="ASR 引擎不可用"):
                process_video(video_file, config)

    def test_process_video_no_words(self, tmp_path, mock_video_info):
        """测试无识别结果"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        config = Config()

        with patch("vsub.core.validate_video"), \
             patch("vsub.core.probe_video") as mock_probe, \
             patch("vsub.core.AudioExtractor") as mock_extractor, \
             patch("vsub.core.create_engine") as mock_create_engine:

            mock_probe.return_value = mock_video_info

            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance

            mock_engine = MagicMock()
            mock_engine.is_available.return_value = True
            mock_engine.transcribe.return_value = []
            mock_create_engine.return_value = mock_engine

            with pytest.raises(RuntimeError, match="未识别到任何语音"):
                process_video(video_file, config)

    def test_process_video_cleanup_on_error(self, tmp_path, mock_video_info):
        """测试错误时清理临时文件"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        config = Config(keep_audio=False)

        with patch("vsub.core.validate_video"), \
             patch("vsub.core.probe_video") as mock_probe, \
             patch("vsub.core.AudioExtractor") as mock_extractor, \
             patch("vsub.core.cleanup_audio") as mock_cleanup:

            mock_probe.return_value = mock_video_info

            mock_extractor_instance = MagicMock()
            mock_extractor.return_value = mock_extractor_instance

            # 模拟 ASR 失败
            mock_extractor_instance.extract_to_wav.side_effect = RuntimeError("提取失败")

            with pytest.raises(RuntimeError):
                process_video(video_file, config)

            # 验证清理函数被调用
            mock_cleanup.assert_called_once()


class TestProcessVideos:
    """批量处理测试"""

    @patch("vsub.core.process_video")
    def test_process_videos_all_success(self, mock_process, tmp_path):
        """测试全部成功"""
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        video1.write_text("dummy")
        video2.write_text("dummy")

        mock_process.return_value = tmp_path / "output.srt"

        config = Config()
        results = process_videos([video1, video2], config)

        assert len(results) == 2
        assert all(out is not None for _, out in results)

    @patch("vsub.core.process_video")
    def test_process_videos_partial_failure(self, mock_process, tmp_path):
        """测试部分失败"""
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        video1.write_text("dummy")
        video2.write_text("dummy")

        def side_effect(path, config):
            if "video1" in str(path):
                return tmp_path / "video1.srt"
            raise RuntimeError("失败")

        mock_process.side_effect = side_effect

        config = Config()
        results = process_videos([video1, video2], config)

        assert len(results) == 2
        assert results[0][1] is not None
        assert results[1][1] is None

    @patch("vsub.core.process_video")
    def test_process_videos_all_failure(self, mock_process, tmp_path):
        """测试全部失败"""
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        video1.write_text("dummy")
        video2.write_text("dummy")

        mock_process.side_effect = RuntimeError("失败")

        config = Config()
        results = process_videos([video1, video2], config)

        assert len(results) == 2
        assert all(out is None for _, out in results)
