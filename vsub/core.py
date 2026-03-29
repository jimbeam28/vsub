"""核心处理模块"""

import logging
from pathlib import Path
from typing import List, Tuple

from tqdm import tqdm

from vsub.asr import AsrWord, create_engine
from vsub.audio import AudioExtractor, cleanup_audio, temp_audio_path
from vsub.config import Config, OutputFormat
from vsub.subtitle import SubtitleGenerator, SubtitleSegment, segments_from_asr_result
from vsub.video import probe_video, validate_video

logger = logging.getLogger(__name__)


def process_video(input_path: Path, config: Config) -> Path:
    """处理单个视频文件"""
    logger.info(f"开始处理: {input_path}")

    # 1. 验证视频
    logger.debug("验证视频文件...")
    validate_video(input_path)
    video_info = probe_video(input_path)
    logger.info(f"视频信息: {video_info.resolution} @ {video_info.fps:.2f}fps, 时长: {video_info.duration:.2f}s")

    if not video_info.has_audio:
        raise RuntimeError("视频没有音频轨道")

    # 2. 提取音频
    logger.info("提取音频...")
    extractor = AudioExtractor()
    temp_audio = temp_audio_path(input_path)
    try:
        extractor.extract_to_wav(input_path, temp_audio)
        logger.debug(f"音频已提取到: {temp_audio}")

        # 3. ASR 识别（带进度条）
        logger.info("启动 ASR 识别...")
        engine = create_engine(model=config.model.value, device="cpu")
        if not engine.is_available():
            raise RuntimeError("ASR 引擎不可用，请安装 faster-whisper")

        # 使用 tqdm 显示进度
        with tqdm(total=100, desc="语音识别", unit="%") as pbar:
            words = engine.transcribe(temp_audio, language=config.language)
            pbar.update(100)

        logger.info(f"识别完成: {len(words)} 个单词")

        if not words:
            raise RuntimeError("未识别到任何语音")

        # 4. 生成字幕
        logger.debug("生成字幕...")
        segments = segments_from_asr_result(
            words,
            max_duration=5.0,
            max_chars=config.max_line_length * config.max_line_count,
        )
        logger.info(f"生成 {len(segments)} 个字幕片段")

        generator = SubtitleGenerator(
            max_line_length=config.max_line_length,
            max_line_count=config.max_line_count,
        )

        # 5. 确定输出路径
        output_path = determine_output_path(input_path, config)
        logger.debug(f"输出路径: {output_path}")

        # 6. 写入文件
        generator.write_to_file(segments, config.format, output_path, config.overwrite)
        logger.info(f"✓ 字幕已保存: {output_path}")

        return output_path

    finally:
        # 清理临时音频文件
        if not config.keep_audio:
            cleanup_audio(temp_audio)


def process_videos(inputs: List[Path], config: Config) -> List[Tuple[Path, Path]]:
    """处理多个视频文件"""
    results = []
    for i, input_path in enumerate(inputs, 1):
        logger.info(f"\n[{i}/{len(inputs)}] 处理 {input_path.name}...")
        try:
            output_path = process_video(input_path, config)
            results.append((input_path, output_path))
        except Exception as e:
            logger.error(f"✗ 处理失败: {e}")
            results.append((input_path, None))

    return results


def determine_output_path(input_path: Path, config: Config) -> Path:
    """确定输出路径"""
    base_name = input_path.stem

    ext = "srt" if config.format == OutputFormat.SRT else "vtt"

    if config.output_dir:
        output_dir = config.output_dir
    else:
        output_dir = input_path.parent

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir / f"{base_name}.{ext}"
