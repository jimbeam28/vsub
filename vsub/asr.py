"""ASR 识别模块"""

from pathlib import Path
from typing import List, Optional


class AsrWord:
    """ASR 识别结果 - 单词级别"""

    def __init__(
        self,
        text: str,
        start: float,
        end: float,
        confidence: float = 1.0,
    ):
        self.text = text
        self.start = start
        self.end = end
        self.confidence = confidence

    def __repr__(self) -> str:
        return f"AsrWord({self.text!r}, {self.start:.2f}-{self.end:.2f})"


class AsrEngine:
    """ASR 引擎接口"""

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
    ) -> List[AsrWord]:
        raise NotImplementedError

    def is_available(self) -> bool:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError


class WhisperEngine(AsrEngine):
    """Whisper ASR 引擎"""

    def __init__(self, model: str = "base", device: str = "cpu"):
        self.model_name = model
        self.device = device
        self._model = None

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise RuntimeError(
                    "faster-whisper 未安装。运行: pip install faster-whisper"
                )

            compute_type = "int8" if self.device == "cpu" else "float16"
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=compute_type,
            )

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
    ) -> List[AsrWord]:
        """识别音频文件"""
        self._load_model()

        segments, info = self._model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        words = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    words.append(
                        AsrWord(
                            text=word.word.strip(),
                            start=word.start,
                            end=word.end,
                            confidence=getattr(word, "probability", 1.0),
                        )
                    )
            else:
                # 如果没有单词级时间戳，使用片段时间戳
                words.append(
                    AsrWord(
                        text=segment.text.strip(),
                        start=segment.start,
                        end=segment.end,
                        confidence=1.0,
                    )
                )

        return words

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return f"whisper-{self.model_name}"


def create_engine(model: str = "base", device: str = "cpu") -> AsrEngine:
    """创建 ASR 引擎"""
    return WhisperEngine(model=model, device=device)
