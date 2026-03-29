"""字幕生成模块"""

import re
from pathlib import Path
from typing import List

from vsub.asr import AsrWord
from vsub.config import OutputFormat


class SubtitleSegment:
    """字幕片段"""

    def __init__(
        self,
        index: int,
        start: float,
        end: float,
        text: str,
    ):
        self.index = index
        self.start = start
        self.end = end
        self.text = text

    def __repr__(self) -> str:
        return f"SubtitleSegment({self.index}, {self.start:.2f}-{self.end:.2f}, {self.text!r})"

    @staticmethod
    def format_time(seconds: float, separator: str = ",") -> str:
        """格式化时间戳为 SRT/VTT 格式 (HH:MM:SS{separator}mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"

    @staticmethod
    def format_time_srt(seconds: float) -> str:
        """格式化时间戳为 SRT 格式 (HH:MM:SS,mmm)"""
        return SubtitleSegment.format_time(seconds, separator=",")

    @staticmethod
    def format_time_vtt(seconds: float) -> str:
        """格式化时间戳为 VTT 格式 (HH:MM:SS.mmm)"""
        return SubtitleSegment.format_time(seconds, separator=".")


class SubtitleGenerator:
    """字幕生成器"""

    def __init__(self, max_line_length: int = 80, max_line_count: int = 2):
        self.max_line_length = max_line_length
        self.max_line_count = max_line_count

    def generate_srt(self, segments: List[SubtitleSegment]) -> str:
        """生成 SRT 格式字幕"""
        lines = []
        for segment in segments:
            lines.append(str(segment.index))
            start = SubtitleSegment.format_time_srt(segment.start)
            end = SubtitleSegment.format_time_srt(segment.end)
            lines.append(f"{start} --> {end}")
            lines.append(self._wrap_text(segment.text))
            lines.append("")  # 空行分隔
        return "\n".join(lines)

    def generate_vtt(self, segments: List[SubtitleSegment]) -> str:
        """生成 VTT 格式字幕"""
        lines = ["WEBVTT", ""]
        for segment in segments:
            start = SubtitleSegment.format_time_vtt(segment.start)
            end = SubtitleSegment.format_time_vtt(segment.end)
            lines.append(f"{start} --> {end}")
            lines.append(self._wrap_text(segment.text))
            lines.append("")  # 空行分隔
        return "\n".join(lines)

    def generate(self, segments: List[SubtitleSegment], fmt: OutputFormat) -> str:
        """根据格式生成字幕"""
        if fmt == OutputFormat.SRT:
            return self.generate_srt(segments)
        elif fmt == OutputFormat.VTT:
            return self.generate_vtt(segments)
        else:
            raise ValueError(f"不支持的格式: {fmt}")

    def _wrap_text(self, text: str) -> str:
        """文本自动换行"""
        words = text.split()
        if not words:
            return ""

        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_len = len(word)
            # 检查当前行加上这个单词是否超过最大长度
            new_length = current_length + (1 if current_line else 0) + word_len

            if current_line and new_length > self.max_line_length:
                # 当前行已满，保存并开始新行
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_len
            else:
                # 添加到当前行
                current_line.append(word)
                current_length = new_length

            # 检查是否达到最大行数限制
            if len(lines) >= self.max_line_count:
                # 保存当前行，清空以继续处理剩余单词
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_length = 0
                break

        # 添加最后一行
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines[:self.max_line_count])

    def write_to_file(
        self,
        segments: List[SubtitleSegment],
        fmt: OutputFormat,
        path: Path,
        overwrite: bool = False,
    ) -> None:
        """写入字幕文件"""
        if path.exists() and not overwrite:
            raise FileExistsError(f"文件已存在（使用 --overwrite 覆盖）: {path}")

        content = self.generate(segments, fmt)
        path.write_text(content, encoding="utf-8")


def segments_from_asr_result(
    words: List[AsrWord],
    max_duration: float = 5.0,
    max_chars: int = 80,
) -> List[SubtitleSegment]:
    """从 ASR 结果创建字幕片段"""
    segments = []
    current_words = []
    segment_start = 0.0
    char_count = 0

    # 句子结束标点（修复：检测单词末尾包含标点）
    sentence_end = re.compile(r"[.!?。！？]")

    for i, word in enumerate(words):
        if not current_words:
            segment_start = word.start

        current_words.append(word)
        # 修复：字符计数考虑空格
        char_count += len(word.text)
        if current_words:  # 不是第一个单词，添加空格
            char_count += 1

        current_duration = word.end - segment_start
        is_last = i == len(words) - 1

        # 检查是否需要分割
        # 修复：检测单词末尾是否包含句子结束标点
        has_end_punctuation = bool(sentence_end.search(word.text)) if word.text else False
        should_split = (
            is_last
            or current_duration >= max_duration
            or char_count >= max_chars
            or has_end_punctuation
        )

        if should_split and current_words:
            segment_text = " ".join(w.text for w in current_words)
            segment_end = current_words[-1].end

            segments.append(
                SubtitleSegment(
                    index=len(segments) + 1,
                    start=segment_start,
                    end=segment_end,
                    text=segment_text,
                )
            )

            current_words = []
            char_count = 0

    return segments
