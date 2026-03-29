"""配置模块测试"""

import tempfile
from pathlib import Path

import pytest

from vsub.config import Config, OutputFormat, WhisperModel


class TestConfig:
    """配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        assert config.format == OutputFormat.SRT
        assert config.model == WhisperModel.BASE
        assert config.language is None
        assert config.keep_audio is False
        assert config.overwrite is False
        assert config.max_line_length == 80
        assert config.max_line_count == 2

    def test_config_from_file(self, tmp_path):
        """测试从文件加载配置"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
format: vtt
model: medium
language: zh
keep_audio: true
max_line_length: 60
""")

        config = Config.from_file(config_file)
        assert config.format == OutputFormat.VTT
        assert config.model == WhisperModel.MEDIUM
        assert config.language == "zh"
        assert config.keep_audio is True
        assert config.max_line_length == 60

    def test_config_from_empty_file(self, tmp_path):
        """测试从空文件加载配置"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = Config.from_file(config_file)
        assert config.format == OutputFormat.SRT
        assert config.model == WhisperModel.BASE

    def test_config_merge(self):
        """测试配置合并"""
        base = Config(format=OutputFormat.VTT, model=WhisperModel.SMALL)
        other = Config(language="en", keep_audio=True)

        merged = base.merge(other)
        assert merged.format == OutputFormat.VTT  # 保留原值
        assert merged.model == WhisperModel.SMALL  # 保留原值
        assert merged.language == "en"  # 覆盖
        assert merged.keep_audio is True  # 覆盖

    def test_find_config_file(self, tmp_path, monkeypatch):
        """测试查找配置文件"""
        # 创建临时配置文件
        config_file = tmp_path / "vsub.yaml"
        config_file.write_text("format: vtt\n")

        # 模拟当前目录
        monkeypatch.chdir(tmp_path)

        found = Config.find_config_file()
        assert found is not None
        assert found.name == "vsub.yaml"
        assert found.exists()

    def test_output_format_enum(self):
        """测试输出格式枚举"""
        assert OutputFormat.SRT.value == "srt"
        assert OutputFormat.VTT.value == "vtt"
        assert OutputFormat("srt") == OutputFormat.SRT
        assert OutputFormat("vtt") == OutputFormat.VTT

    def test_whisper_model_enum(self):
        """测试模型枚举"""
        assert WhisperModel.TINY.value == "tiny"
        assert WhisperModel.LARGE_V3.value == "large-v3"
        assert WhisperModel("medium") == WhisperModel.MEDIUM
