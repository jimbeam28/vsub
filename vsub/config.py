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


class AsrEngineType(str, Enum):
    """ASR 引擎类型"""
    WHISPER = "whisper"
    OPENAI = "openai"
    AZURE = "azure"
    FUNASR = "funasr"


class Config(BaseModel):
    """应用程序配置"""

    # 输出格式
    format: OutputFormat = Field(default=OutputFormat.SRT, description="输出字幕格式")

    # ASR 引擎类型
    engine: AsrEngineType = Field(default=AsrEngineType.WHISPER, description="ASR 引擎类型")

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

    # 批量处理并发数
    max_workers: Optional[int] = Field(default=None, description="批量处理并发数，None 表示自动")

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """从配置文件加载"""
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if data is None:
            data = {}
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
        """合并另一个配置，other 中显式设置且非 None 的字段覆盖当前配置"""
        # 获取 self 的数据
        data = self.model_dump()

        # 获取 other 中显式设置的字段
        other_data = other.model_dump()
        for key in other.model_fields_set:
            value = other_data[key]
            # 只合并非 None 的值
            if value is not None:
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

# ASR 引擎: whisper, openai, azure, funasr
engine: whisper

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

# 批量处理并发数 (留空为自动)
# max_workers: 4
"""
