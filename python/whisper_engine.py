#!/usr/bin/env python3
"""
Whisper ASR Engine for Vsub
使用 faster-whisper 进行语音识别
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Whisper ASR Engine")
    parser.add_argument("audio_path", help="输入音频文件路径")
    parser.add_argument("--model", default="base", help="Whisper 模型大小")
    parser.add_argument("--language", help="语言代码 (如 zh, en)")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="计算设备")
    parser.add_argument("--output-json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Error: faster-whisper not installed. Run: pip install faster-whisper", file=sys.stderr)
        sys.exit(1)

    # 加载模型
    model_size = args.model
    device = args.device
    compute_type = "int8" if device == "cpu" else "float16"

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        sys.exit(1)

    # 转录
    try:
        segments, info = model.transcribe(
            args.audio_path,
            language=args.language,
            word_timestamps=True,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
    except Exception as e:
        print(f"Error transcribing: {e}", file=sys.stderr)
        sys.exit(1)

    # 构建结果
    result_segments = []
    all_words = []

    for segment in segments:
        seg_words = []
        if segment.words:
            for word in segment.words:
                word_dict = {
                    "text": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                    "confidence": getattr(word, "probability", 1.0),
                }
                seg_words.append(word_dict)
                all_words.append(word_dict)

        result_segments.append({
            "text": segment.text.strip(),
            "start": segment.start,
            "end": segment.end,
            "words": seg_words if seg_words else None,
        })

    result = {
        "segments": result_segments,
        "language": info.language,
        "duration": info.duration,
    }

    if args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 纯文本输出
        for seg in result_segments:
            print(f"[{seg['start']:.2f} -> {seg['end']:.2f}] {seg['text']}")


if __name__ == "__main__":
    main()
