"""ASR 模块测试"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsub.asr import AsrWord, WhisperEngine, create_engine


class TestAsrWord:
    """ASR 单词测试"""

    def test_asr_word_creation(self):
        """测试创建 ASR 单词"""
        word = AsrWord("hello", 0.0, 0.5, 0.95)
        assert word.text == "hello"
        assert word.start == 0.0
        assert word.end == 0.5
        assert word.confidence == 0.95

    def test_asr_word_default_confidence(self):
        """测试默认置信度"""
        word = AsrWord("hello", 0.0, 0.5)
        assert word.confidence == 1.0

    def test_asr_word_repr(self):
        """测试字符串表示"""
        word = AsrWord("hello", 0.0, 0.5)
        assert "hello" in repr(word)
        assert "0.00-0.50" in repr(word)


class TestWhisperEngine:
    """Whisper 引擎测试"""

    def test_engine_creation(self):
        """测试引擎创建"""
        engine = WhisperEngine(model="base", device="cpu")
        assert engine.model_name == "base"
        assert engine.device == "cpu"
        assert engine.name == "whisper-base"

    def test_is_available_true(self):
        """测试引擎可用"""
        with patch("builtins.__import__") as mock_import:
            mock_import.return_value = MagicMock()
            engine = WhisperEngine()
            assert engine.is_available() is True

    def test_is_available_false(self):
        """测试引擎不可用"""
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError()
            engine = WhisperEngine()
            assert engine.is_available() is False

    def test_create_engine(self):
        """测试创建引擎工厂函数"""
        engine = create_engine(model="small", device="cpu")
        assert isinstance(engine, WhisperEngine)
        assert engine.model_name == "small"

    def test_transcribe_with_words(self):
        """测试带单词时间戳的转录"""
        # 模拟 faster-whisper 返回的结果
        mock_word = MagicMock()
        mock_word.word = "hello"
        mock_word.start = 0.0
        mock_word.end = 0.5
        mock_word.probability = 0.95

        mock_segment = MagicMock()
        mock_segment.words = [mock_word]
        mock_segment.text = "hello"
        mock_segment.start = 0.0
        mock_segment.end = 0.5

        mock_info = MagicMock()

        with patch.object(WhisperEngine, "_load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([mock_segment], mock_info)

            engine = WhisperEngine()
            engine._model = mock_model

            words = engine.transcribe(Path("test.wav"))

            assert len(words) == 1
            assert words[0].text == "hello"
            assert words[0].start == 0.0
            assert words[0].end == 0.5
            assert words[0].confidence == 0.95

    def test_transcribe_without_words(self):
        """测试无单词时间戳的转录"""
        mock_segment = MagicMock()
        mock_segment.words = None
        mock_segment.text = "hello world"
        mock_segment.start = 0.0
        mock_segment.end = 1.0

        mock_info = MagicMock()

        with patch.object(WhisperEngine, "_load_model"):
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([mock_segment], mock_info)

            engine = WhisperEngine()
            engine._model = mock_model

            words = engine.transcribe(Path("test.wav"))

            assert len(words) == 1
            assert words[0].text == "hello world"

    def test_load_model_not_installed(self):
        """测试模型未安装"""
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named faster_whisper")
            engine = WhisperEngine()
            with pytest.raises(RuntimeError, match="faster-whisper 未安装"):
                engine._load_model()
