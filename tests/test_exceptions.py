"""异常处理和边界条件测试"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsub.asr import AsrWord, WhisperEngine
from vsub.audio import AudioExtractor, cleanup_audio
from vsub.config import Config, OutputFormat, WhisperModel
from vsub.subtitle import SubtitleGenerator, segments_from_asr_result
from vsub.video import validate_video


class TestAudioExceptions:
    """音频模块异常测试"""

    def test_extract_to_wav_failure(self, tmp_path):
        """测试音频提取失败"""
        with patch("vsub.audio.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            extractor = AudioExtractor()

            # 模拟 FFmpeg 执行失败
            with patch("vsub.audio.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stderr="Error: Invalid file format"
                )

                video_path = tmp_path / "invalid.mp4"
                output_path = tmp_path / "output.wav"

                with pytest.raises(RuntimeError, match="音频提取失败"):
                    extractor.extract_to_wav(video_path, output_path)

    def test_extract_to_wav_no_output(self, tmp_path):
        """测试音频提取无输出文件"""
        with patch("vsub.audio.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            extractor = AudioExtractor()

            with patch("vsub.audio.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                video_path = tmp_path / "video.mp4"
                output_path = tmp_path / "output.wav"

                # 输出文件不存在
                with pytest.raises(RuntimeError, match="输出文件未生成"):
                    extractor.extract_to_wav(video_path, output_path)

    def test_extract_to_wav_empty_output(self, tmp_path):
        """测试音频提取输出为空"""
        with patch("vsub.audio.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            extractor = AudioExtractor()

            video_path = tmp_path / "video.mp4"
            output_path = tmp_path / "output.wav"

            # 使用 side_effect 在 subprocess.run 被调用后创建空文件
            def mock_run_side_effect(*args, **kwargs):
                output_path.write_text("")  # 创建空文件
                return MagicMock(returncode=0)

            with patch("vsub.audio.subprocess.run") as mock_run:
                mock_run.side_effect = mock_run_side_effect

                with pytest.raises(RuntimeError, match="输出文件为空"):
                    extractor.extract_to_wav(video_path, output_path)

    def test_cleanup_audio_failure(self, tmp_path, capsys):
        """测试清理音频失败"""
        audio_path = tmp_path / "test.wav"
        audio_path.write_text("content")

        # 模拟删除失败
        with patch.object(Path, "unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Permission denied")
            cleanup_audio(audio_path)

        captured = capsys.readouterr()
        assert "警告" in captured.out or "无法删除" in captured.out


class TestVideoExceptions:
    """视频模块异常测试"""

    def test_validate_nonexistent_file(self, tmp_path):
        """测试验证不存在的文件"""
        video_path = tmp_path / "nonexistent.mp4"
        with pytest.raises(FileNotFoundError):
            validate_video(video_path)

    def test_validate_directory(self, tmp_path):
        """测试验证目录"""
        with pytest.raises(ValueError, match="不是文件"):
            validate_video(tmp_path)

    def test_probe_video_ffprobe_failure(self, tmp_path):
        """测试 ffprobe 执行失败"""
        video_path = tmp_path / "test.mp4"
        video_path.write_text("dummy")

        with patch("vsub.video.check_ffprobe") as mock_check:
            mock_check.return_value = Path("/usr/bin/ffprobe")

            with patch("vsub.video.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stderr="Invalid data"
                )

                with pytest.raises(RuntimeError, match="ffprobe 失败"):
                    from vsub.video import probe_video
                    probe_video(video_path)


class TestSubtitleEdgeCases:
    """字幕模块边界条件测试"""

    def test_wrap_text_very_long_word(self):
        """测试超长单词"""
        generator = SubtitleGenerator(max_line_length=10, max_line_count=2)
        text = "supercalifragilisticexpialidocious"

        wrapped = generator._wrap_text(text)
        # 超长单词应该单独一行
        assert wrapped == text

    def test_wrap_text_exact_length(self):
        """测试恰好达到长度限制"""
        generator = SubtitleGenerator(max_line_length=10, max_line_count=1)
        text = "exactly10"  # 正好10个字符

        wrapped = generator._wrap_text(text)
        assert wrapped == "exactly10"

    def test_wrap_text_single_word(self):
        """测试单字文本"""
        generator = SubtitleGenerator()
        text = "Hello"

        wrapped = generator._wrap_text(text)
        assert wrapped == "Hello"

    def test_segments_from_asr_empty(self):
        """测试空单词列表"""
        segments = segments_from_asr_result([], max_duration=5.0, max_chars=100)
        assert segments == []

    def test_segments_from_asr_single_word(self):
        """测试单字"""
        words = [AsrWord("Hi", 0.0, 0.5)]
        segments = segments_from_asr_result(words, max_duration=5.0, max_chars=100)
        assert len(segments) == 1
        assert segments[0].text == "Hi"

    def test_subtitle_generator_write_permission_error(self, tmp_path):
        """测试写入权限错误"""
        generator = SubtitleGenerator()
        segments = [MagicMock(index=1, start=0.0, end=1.0, text="Test")]

        output_path = tmp_path / "readonly.srt"
        output_path.touch()

        # 模拟权限错误
        with patch.object(Path, "write_text") as mock_write:
            mock_write.side_effect = PermissionError("Permission denied")
            with pytest.raises(PermissionError):
                generator.write_to_file(segments, OutputFormat.SRT, output_path, overwrite=True)


class TestConfigEdgeCases:
    """配置模块边界条件测试"""

    def test_config_with_whitespace_yaml(self, tmp_path):
        """测试只有空白字符的 YAML"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("   \n\n   ")

        config = Config.from_file(config_file)
        assert config.format == OutputFormat.SRT

    def test_config_merge_with_none_values(self):
        """测试合并 None 值（默认值不覆盖）"""
        base = Config(language="zh")
        other = Config(language=None)

        merged = base.merge(other)
        # None 是默认值，不应该覆盖已有值
        assert merged.language == "zh"

    def test_config_invalid_path(self):
        """测试无效路径"""
        config = Config(output_dir=Path("/nonexistent/path"))
        # 应该正常创建，使用时再检查
        assert config.output_dir == Path("/nonexistent/path")


class TestAsrEdgeCases:
    """ASR 模块边界条件测试"""

    def test_whisper_engine_empty_transcribe(self):
        """测试空转录结果"""
        engine = WhisperEngine()

        with patch.object(engine, "_load_model"):
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([], MagicMock())
            engine._model = mock_model

            result = engine.transcribe(Path("test.wav"))
            assert result == []

    def test_whisper_engine_words_with_no_probability(self):
        """测试无概率属性的单词"""
        from vsub.asr import AsrWord

        engine = WhisperEngine()

        with patch.object(engine, "_load_model"):
            mock_model = MagicMock()

            mock_word = MagicMock()
            mock_word.word = "test"
            mock_word.start = 0.0
            mock_word.end = 0.5
            # 没有 probability 属性
            del mock_word.probability

            mock_segment = MagicMock()
            mock_segment.words = [mock_word]
            mock_segment.text = "test"
            mock_segment.start = 0.0
            mock_segment.end = 0.5

            mock_model.transcribe.return_value = ([mock_segment], MagicMock())
            engine._model = mock_model

            result = engine.transcribe(Path("test.wav"))
            assert len(result) == 1
            assert result[0].confidence == 1.0  # 使用默认值

    def test_whisper_engine_very_long_audio(self):
        """测试超长音频"""
        engine = WhisperEngine()

        # 模拟很多单词
        words = [AsrWord(f"word{i}", i, i + 0.5) for i in range(1000)]

        with patch.object(engine, "_load_model"):
            mock_model = MagicMock()

            mock_segments = []
            for i in range(1000):
                mock_word = MagicMock()
                mock_word.word = f"word{i}"
                mock_word.start = i
                mock_word.end = i + 0.5
                mock_word.probability = 0.9

                mock_segment = MagicMock()
                mock_segment.words = [mock_word]
                mock_segment.text = f"word{i}"
                mock_segment.start = i
                mock_segment.end = i + 0.5
                mock_segments.append(mock_segment)

            mock_model.transcribe.return_value = (mock_segments, MagicMock())
            engine._model = mock_model

            result = engine.transcribe(Path("test.wav"))
            assert len(result) == 1000
