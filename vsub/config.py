"""配置管理模块"""

from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """字幕输出格式"""
    SRT = "srt"
    VTT = "vtt"


class WhisperModel(str, Enum):
    """Whisper 模型大小"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"


class Config(BaseModel):
    """应用程序配置"""

    # 输出格式
    format: OutputFormat = Field(default=OutputFormat.SRT, description="输出字幕格式")

    # ASR 模型
    model: WhisperModel = Field(default=WhisperModel.BASE, description="Whisper 模型大小")

    # 语言代码（如 "en", "zh"）
    language: Optional[str] = Field(default=None, description="语言代码，留空自动检测")

    # 保留临时音频文件
    keep_audio: bool = Field(default=False, description="保留临时提取的音频文件")

    # 强制覆盖输出文件
    overwrite: bool = Field(default=False, description="强制覆盖已存在的输出文件")

    # 输出目录
    output_dir: Optional[Path] = Field(default=None, description="输出目录")

    # 最大行长度
    max_line_length: int = Field(default=80, description="字幕最大行长度")

    # 每行最大单词数
    max_line_count: int = Field(default=2, description="字幕每行最大单词数")

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """从配置文件加载"""
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return cls(**data)

    @classmethod
    def load(cls) -> "Config":
        """加载默认配置，尝试从多个位置读取配置文件"""
        config = cls()

        # 尝试从默认位置加载配置文件
        if config_path := cls.find_config_file():
            try:
                file_config = cls.from_file(config_path)
                config = config.merge(file_config)
            except Exception:
                pass

        return config

    def merge(self, other: "Config") -> "Config":
        """合并另一个配置，其他配置的非默认值覆盖当前配置"""
        data = self.model_dump()
        other_data = other.model_dump()

        # 只覆盖非默认值
        defaults = Config().model_dump()
        for key, value in other_data.items():
            if value != defaults[key]:
                data[key] = value

        return Config(**data)

    @staticmethod
    def find_config_file() -> Optional[Path]:
        """查找配置文件"""
        candidates = [
            Path("vsub.yaml"),
            Path("vsub.yml"),
            Path.home() / ".config" / "vsub" / "config.yaml",
            Path("/etc/vsub/config.yaml"),
        ]

        for path in candidates:
            if path.exists():
                return path

        return None

    @staticmethod
    def default_config_yaml() -> str:
        """生成默认配置文件内容"""
        return """# Vsub 配置文件
# 放置于当前目录作为 vsub.yaml，或 ~/.config/vsub/config.yaml

# 输出格式: srt 或 vtt
format: srt

# Whisper 模型: tiny, base, small, medium, large, large-v2, large-v3
model: base

# 语言代码 (如 "en", "zh", 留空为自动检测)
# language: zh

# 保留临时音频文件
keep_audio: false

# 强制覆盖输出文件
overwrite: false

# 输出目录 (留空为与输入文件相同目录)
# output_dir: ./output

# 字幕最大行长度
max_line_length: 80

# 字幕每行最大单词数
max_line_count: 2
"""
