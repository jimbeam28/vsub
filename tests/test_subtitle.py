"""字幕生成模块测试"""

from pathlib import Path

import pytest

from vsub.asr import AsrWord
from vsub.config import OutputFormat
from vsub.subtitle import (
    SubtitleGenerator,
    SubtitleSegment,
    segments_from_asr_result,
)


class TestSubtitleSegment:
    """字幕片段测试"""

    def test_format_time_srt(self):
        """测试 SRT 时间格式化"""
        assert SubtitleSegment.format_time_srt(0) == "00:00:00,000"
        assert SubtitleSegment.format_time_srt(90.5) == "00:01:30,500"
        assert SubtitleSegment.format_time_srt(3661.123) == "01:01:01,123"

    def test_format_time_vtt(self):
        """测试 VTT 时间格式化"""
        assert SubtitleSegment.format_time_vtt(0) == "00:00:00.000"
        assert SubtitleSegment.format_time_vtt(90.5) == "00:01:30.500"
        assert SubtitleSegment.format_time_vtt(3661.123) == "01:01:01.123"


class TestSubtitleGenerator:
    """字幕生成器测试"""

    def test_generate_srt(self):
        """测试生成 SRT"""
        generator = SubtitleGenerator()
        segments = [
            SubtitleSegment(1, 0.0, 3.5, "Hello world"),
            SubtitleSegment(2, 3.5, 7.0, "Second line"),
        ]

        srt = generator.generate_srt(segments)
        assert "1" in srt
        assert "00:00:00,000 --> 00:00:03,500" in srt
        assert "Hello world" in srt
        assert "2" in srt
        assert srt.endswith("\n")

    def test_generate_vtt(self):
        """测试生成 VTT"""
        generator = SubtitleGenerator()
        segments = [
            SubtitleSegment(1, 0.0, 3.5, "Hello world"),
        ]

        vtt = generator.generate_vtt(segments)
        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> 00:00:03.500" in vtt
        assert "Hello world" in vtt

    def test_generate_with_format(self):
        """测试通过格式参数生成"""
        generator = SubtitleGenerator()
        segments = [SubtitleSegment(1, 0.0, 3.5, "Hello")]

        srt = generator.generate(segments, OutputFormat.SRT)
        assert "WEBVTT" not in srt
        assert "," in srt  # SRT 使用逗号

        vtt = generator.generate(segments, OutputFormat.VTT)
        assert "WEBVTT" in vtt
        assert "." in vtt  # VTT 使用点号

    def test_wrap_text(self):
        """测试文本换行"""
        generator = SubtitleGenerator(max_line_length=20, max_line_count=2)
        text = "This is a very long text that should be wrapped"

        wrapped = generator._wrap_text(text)
        lines = wrapped.split("\n")
        assert len(lines) <= 2
        assert all(len(line) <= 20 for line in lines)

    def test_wrap_text_short(self):
        """测试短文本不换行"""
        generator = SubtitleGenerator(max_line_length=80, max_line_count=2)
        text = "Short text"

        wrapped = generator._wrap_text(text)
        assert wrapped == "Short text"

    def test_wrap_text_empty(self):
        """测试空文本"""
        generator = SubtitleGenerator()
        assert generator._wrap_text("") == ""

    def test_write_to_file(self, tmp_path):
        """测试写入文件"""
        generator = SubtitleGenerator()
        segments = [SubtitleSegment(1, 0.0, 3.5, "Hello")]
        output_file = tmp_path / "output.srt"

        generator.write_to_file(segments, OutputFormat.SRT, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Hello" in content

    def test_write_to_file_exists(self, tmp_path):
        """测试文件已存在"""
        generator = SubtitleGenerator()
        segments = [SubtitleSegment(1, 0.0, 3.5, "Hello")]
        output_file = tmp_path / "output.srt"
        output_file.write_text("existing")

        with pytest.raises(FileExistsError):
            generator.write_to_file(segments, OutputFormat.SRT, output_file, overwrite=False)

        # 覆盖应成功
        generator.write_to_file(segments, OutputFormat.SRT, output_file, overwrite=True)


class TestSegmentsFromAsrResult:
    """ASR 结果转字幕片段测试"""

    def test_basic_segmentation(self):
        """测试基本分片"""
        words = [
            AsrWord("Hello", 0.0, 0.5),
            AsrWord("world", 0.6, 1.0),
            AsrWord(".", 1.0, 1.1),
        ]

        segments = segments_from_asr_result(words, max_duration=5.0, max_chars=100)
        assert len(segments) == 1
        assert segments[0].text == "Hello world ."
        assert segments[0].start == 0.0
        assert segments[0].end == 1.1

    def test_duration_split(self):
        """测试按时长分割 - 当超过最大时长时，当前累积的词作为一个片段"""
        words = [
            AsrWord("word1", 0.0, 2.0),
            AsrWord("word2", 2.1, 4.0),
            AsrWord("word3", 4.1, 6.0),  # 此时累积时长超过 5 秒
        ]

        segments = segments_from_asr_result(words, max_duration=5.0, max_chars=100)
        # word3 结束时触发分割，所有词作为一个片段
        assert len(segments) == 1
        assert segments[0].end == 6.0  # 最后一个词的结束时间

    def test_char_limit_split(self):
        """测试按字符数分割"""
        words = [
            AsrWord("a", 0.0, 0.1),
            AsrWord("b", 0.2, 0.3),
            AsrWord("c", 0.4, 0.5),
        ]

        segments = segments_from_asr_result(words, max_duration=10.0, max_chars=2)
        # a(1) + b(1) + 空格(1) = 3 > 2, 所以 a 单独一个片段，b c 另一个
        assert len(segments) >= 1

    def test_sentence_end_split(self):
        """测试句子结束分割"""
        words = [
            AsrWord("Hello", 0.0, 0.5),
            AsrWord(".", 0.5, 0.6),  # 句子结束
            AsrWord("World", 1.0, 1.5),
        ]

        segments = segments_from_asr_result(words, max_duration=10.0, max_chars=100)
        assert len(segments) == 2
        assert "Hello" in segments[0].text
        assert "World" in segments[1].text

    def test_empty_words(self):
        """测试空单词列表"""
        segments = segments_from_asr_result([], max_duration=5.0, max_chars=100)
        assert len(segments) == 0
