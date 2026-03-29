"""Pytest 配置和 fixture"""

import pytest


@pytest.fixture
def sample_video_path(tmp_path):
    """创建模拟视频文件"""
    video_file = tmp_path / "sample.mp4"
    # 写入一些假数据
    video_file.write_bytes(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 100)
    return video_file


@pytest.fixture
def sample_config():
    """创建测试配置"""
    from vsub.config import Config, OutputFormat, WhisperModel

    return Config(
        format=OutputFormat.SRT,
        model=WhisperModel.BASE,
        language=None,
        keep_audio=False,
        overwrite=False,
        max_line_length=80,
        max_line_count=2,
    )
