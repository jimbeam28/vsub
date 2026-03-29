"""vsub - 视频字幕生成工具"""

__version__ = "0.2.0"
__all__ = ["Config", "process_video"]

from vsub.config import Config
from vsub.core import process_video
