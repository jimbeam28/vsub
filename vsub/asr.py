"""ASR 识别模块"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional


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


class AsrEngine(ABC):
    """ASR 引擎抽象基类"""

    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[AsrWord]:
        """识别音频文件"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        pass


class WhisperEngine(AsrEngine):
    """本地 Whisper ASR 引擎 (faster-whisper)"""

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

    def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        try:
            import wave

            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[AsrWord]:
        """识别音频文件"""
        self._load_model()

        # 获取音频时长用于进度计算
        duration = self._get_audio_duration(audio_path) if progress_callback else 0.0

        segments, info = self._model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        words = []
        last_progress = 0.0

        for segment in segments:
            # 计算进度
            if progress_callback and duration > 0:
                current_progress = min(segment.end / duration, 1.0)
                if current_progress - last_progress >= 0.01:  # 每1%更新一次
                    progress_callback(current_progress)
                    last_progress = current_progress

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

        # 确保进度到100%
        if progress_callback:
            progress_callback(1.0)

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


class OpenAIWhisperEngine(AsrEngine):
    """OpenAI Whisper API 引擎"""

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[AsrWord]:
        """使用 OpenAI API 识别音频"""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai 未安装。运行: pip install openai")

        if not self.api_key:
            raise RuntimeError("未设置 OpenAI API Key，请设置 OPENAI_API_KEY 环境变量")

        client = OpenAI(api_key=self.api_key)

        # OpenAI API 不支持实时进度回调，直接返回100%
        if progress_callback:
            progress_callback(0.1)

        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

        if progress_callback:
            progress_callback(1.0)

        words = []
        if hasattr(response, "words") and response.words:
            for word in response.words:
                words.append(
                    AsrWord(
                        text=word.word.strip(),
                        start=word.start,
                        end=word.end,
                        confidence=1.0,  # OpenAI 不提供置信度
                    )
                )
        elif hasattr(response, "text"):
            # 如果没有单词级时间戳，将整个文本作为一个片段
            words.append(
                AsrWord(
                    text=response.text.strip(),
                    start=0.0,
                    end=0.0,  # 无法获取时长
                    confidence=1.0,
                )
            )

        return words

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import openai
            return bool(self.api_key)
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return f"openai-{self.model}"


class AzureASREngine(AsrEngine):
    """Azure Speech Recognition 引擎"""

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.subscription_key = subscription_key or os.getenv("AZURE_SPEECH_KEY")
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "eastasia")

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[AsrWord]:
        """使用 Azure Speech SDK 识别音频"""
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            raise RuntimeError(
                "azure-cognitiveservices-speech 未安装。"
                "运行: pip install azure-cognitiveservices-speech"
            )

        if not self.subscription_key:
            raise RuntimeError(
                "未设置 Azure Speech Key，请设置 AZURE_SPEECH_KEY 环境变量"
            )

        speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key,
            region=self.region,
        )

        # 设置语言
        if language:
            speech_config.speech_recognition_language = language

        audio_config = speechsdk.audio.AudioConfig(filename=str(audio_path))
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        # Azure 不支持实时进度回调
        if progress_callback:
            progress_callback(0.1)

        # 识别
        result = speech_recognizer.recognize_once()

        if progress_callback:
            progress_callback(1.0)

        words = []
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # Azure SDK 不提供单词级时间戳在简单识别中
            words.append(
                AsrWord(
                    text=result.text,
                    start=0.0,
                    end=0.0,
                    confidence=1.0,
                )
            )
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise RuntimeError("Azure Speech: 未识别到语音")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            raise RuntimeError(f"Azure Speech 取消: {cancellation.error_details}")

        return words

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import azure.cognitiveservices.speech
            return bool(self.subscription_key)
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "azure-speech"


class FunASREngine(AsrEngine):
    """阿里 FunASR 引擎"""

    def __init__(
        self,
        model: str = "paraformer-zh",
        device: str = "cpu",
    ):
        self.model_name = model
        self.device = device
        self._model = None

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from funasr import AutoModel
            except ImportError:
                raise RuntimeError("funasr 未安装。运行: pip install funasr")

            self._model = AutoModel(
                model=self.model_name,
                device=self.device,
            )

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[AsrWord]:
        """使用 FunASR 识别音频"""
        self._load_model()

        # FunASR 不支持实时进度回调
        if progress_callback:
            progress_callback(0.1)

        result = self._model.generate(input=str(audio_path))

        if progress_callback:
            progress_callback(1.0)

        words = []
        if result and len(result) > 0:
            res = result[0]
            if isinstance(res, dict):
                text = res.get("text", "")
                # FunASR 提供的时间戳格式可能不同，这里做简单处理
                timestamp = res.get("timestamp", [])

                if timestamp and isinstance(timestamp, list):
                    # 如果有时间戳信息
                    for i, (start, end) in enumerate(timestamp):
                        # 这里假设 timestamp 是 [(start, end), ...] 格式
                        word_text = text[i] if i < len(text) else ""
                        words.append(
                            AsrWord(
                                text=word_text,
                                start=start / 1000.0,  # 转换为秒
                                end=end / 1000.0,
                                confidence=1.0,
                            )
                        )
                else:
                    # 没有时间戳，整个文本作为一个片段
                    words.append(
                        AsrWord(
                            text=text,
                            start=0.0,
                            end=0.0,
                            confidence=1.0,
                        )
                    )

        return words

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import funasr
            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return f"funasr-{self.model_name}"


# 引擎注册表
ENGINE_REGISTRY = {
    "whisper": WhisperEngine,
    "openai": OpenAIWhisperEngine,
    "azure": AzureASREngine,
    "funasr": FunASREngine,
}


def create_engine(
    engine_type: str = "whisper",
    model: str = "base",
    device: str = "cpu",
    **kwargs,
) -> AsrEngine:
    """创建 ASR 引擎

    Args:
        engine_type: 引擎类型 (whisper/openai/azure/funasr)
        model: 模型名称
        device: 计算设备
        **kwargs: 其他引擎特定参数

    Returns:
        ASR 引擎实例
    """
    engine_type = engine_type.lower()

    if engine_type not in ENGINE_REGISTRY:
        raise ValueError(
            f"未知的引擎类型: {engine_type}. "
            f"支持的引擎: {', '.join(ENGINE_REGISTRY.keys())}"
        )

    engine_class = ENGINE_REGISTRY[engine_type]

    if engine_type == "whisper":
        return engine_class(model=model, device=device)
    elif engine_type == "openai":
        return engine_class(api_key=kwargs.get("api_key"), model=model)
    elif engine_type == "azure":
        return engine_class(
            subscription_key=kwargs.get("subscription_key"),
            region=kwargs.get("region"),
        )
    elif engine_type == "funasr":
        return engine_class(model=model, device=device)

    raise ValueError(f"未实现的引擎类型: {engine_type}")


def list_available_engines() -> List[str]:
    """列出所有可用的引擎"""
    available = []
    for name, engine_class in ENGINE_REGISTRY.items():
        try:
            engine = engine_class()
            if engine.is_available():
                available.append(name)
        except Exception:
            pass
    return available
