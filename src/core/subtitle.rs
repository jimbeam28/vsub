use std::fmt::Write;

use crate::core::config::OutputFormat;
use crate::asr::AsrWord;
use crate::VsubError;

/// 字幕片段
#[derive(Debug, Clone)]
pub struct SubtitleSegment {
    pub index: usize,
    pub start: f64,
    pub end: f64,
    pub text: String,
}

impl SubtitleSegment {
    pub fn new(index: usize, start: f64, end: f64, text: String) -> Self {
        Self { index, start, end, text }
    }

    /// 格式化时间戳为 SRT 格式 (HH:MM:SS,mmm)
    pub fn format_time_srt(seconds: f64) -> String {
        let hours = (seconds / 3600.0) as u32;
        let minutes = ((seconds % 3600.0) / 60.0) as u32;
        let secs = (seconds % 60.0) as u32;
        let millis = ((seconds % 1.0) * 1000.0) as u32;

        format!("{:02}:{:02}:{:02},{:03}", hours, minutes, secs, millis)
    }

    /// 格式化时间戳为 VTT 格式 (HH:MM:SS.mmm)
    pub fn format_time_vtt(seconds: f64) -> String {
        let hours = (seconds / 3600.0) as u32;
        let minutes = ((seconds % 3600.0) / 60.0) as u32;
        let secs = (seconds % 60.0) as u32;
        let millis = ((seconds % 1.0) * 1000.0) as u32;

        format!("{:02}:{:02}:{:02}.{:03}", hours, minutes, secs, millis)
    }
}

/// 字幕生成器
pub struct SubtitleGenerator {
    max_line_length: usize,
    max_line_count: usize,
}

impl SubtitleGenerator {
    pub fn new(max_line_length: usize, max_line_count: usize) -> Self {
        Self {
            max_line_length,
            max_line_count,
        }
    }

    /// 生成 SRT 格式字幕
    pub fn generate_srt(&self, segments: &[SubtitleSegment]) -> Result<String, VsubError> {
        let mut output = String::new();

        for segment in segments {
            // 序号
            writeln!(&mut output, "{}", segment.index)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

            // 时间戳
            let start = SubtitleSegment::format_time_srt(segment.start);
            let end = SubtitleSegment::format_time_srt(segment.end);
            writeln!(&mut output, "{} --> {}", start, end)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

            // 文本（自动换行）
            let wrapped = self.wrap_text(&segment.text);
            writeln!(&mut output, "{}", wrapped)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

            // 空行分隔
            writeln!(&mut output)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;
        }

        Ok(output)
    }

    /// 生成 VTT 格式字幕
    pub fn generate_vtt(&self, segments: &[SubtitleSegment]) -> Result<String, VsubError> {
        let mut output = String::new();

        // VTT 头部
        writeln!(&mut output, "WEBVTT")
            .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;
        writeln!(&mut output)
            .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

        for segment in segments {
            // 时间戳（VTT 不需要序号）
            let start = SubtitleSegment::format_time_vtt(segment.start);
            let end = SubtitleSegment::format_time_vtt(segment.end);
            writeln!(&mut output, "{} --> {}", start, end)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

            // 文本（自动换行）
            let wrapped = self.wrap_text(&segment.text);
            writeln!(&mut output, "{}", wrapped)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;

            // 空行分隔
            writeln!(&mut output)
                .map_err(|e| VsubError::Subtitle(format!("写入失败: {}", e)))?;
        }

        Ok(output)
    }

    /// 根据格式生成字幕
    pub fn generate(
        &self,
        segments: &[SubtitleSegment],
        format: OutputFormat,
    ) -> Result<String, VsubError> {
        match format {
            OutputFormat::Srt => self.generate_srt(segments),
            OutputFormat::Vtt => self.generate_vtt(segments),
        }
    }

    /// 文本自动换行
    fn wrap_text(&self, text: &str) -> String {
        let words: Vec<&str> = text.split_whitespace().collect();
        let mut lines: Vec<String> = Vec::new();
        let mut current_line = String::new();

        for word in words {
            // 检查是否需要换行
            if !current_line.is_empty()
                && current_line.len() + 1 + word.len() > self.max_line_length
            {
                lines.push(current_line);
                current_line = String::new();

                // 检查是否达到最大行数
                if lines.len() >= self.max_line_count {
                    // 剩余词作为新行开始
                    current_line = word.to_string();
                    continue;
                }
            }

            if !current_line.is_empty() {
                current_line.push(' ');
            }
            current_line.push_str(word);
        }

        if !current_line.is_empty() {
            lines.push(current_line);
        }

        lines.join("\n")
    }

    /// 写入字幕文件
    pub fn write_to_file<P: AsRef<std::path::Path>>(
        &self,
        segments: &[SubtitleSegment],
        format: OutputFormat,
        path: P,
        overwrite: bool,
    ) -> Result<(), VsubError> {
        let path = path.as_ref();

        // 检查文件是否已存在
        if path.exists() && !overwrite {
            return Err(VsubError::Subtitle(format!(
                "文件已存在（使用 --overwrite 覆盖）: {}",
                path.display()
            )));
        }

        let content = self.generate(segments, format)?;

        std::fs::write(path, content)
            .map_err(|e| VsubError::Io(e))?;

        Ok(())
    }
}

/// 从 ASR 结果创建字幕片段
pub fn segments_from_asr_result(
    words: &[AsrWord],
    max_duration: f64,
    max_chars: usize,
) -> Vec<SubtitleSegment> {
    let mut segments: Vec<SubtitleSegment> = Vec::new();
    let mut current_words: Vec<&AsrWord> = Vec::new();
    let mut segment_start: f64 = 0.0;
    let mut char_count: usize = 0;

    for (i, word) in words.iter().enumerate() {
        // 开始新片段
        if current_words.is_empty() {
            segment_start = word.start;
        }

        current_words.push(word);
        char_count += word.text.len();

        let current_duration = word.end - segment_start;
        let is_last = i == words.len() - 1;

        // 检查是否需要分割
        let should_split = is_last
            || current_duration >= max_duration
            || char_count >= max_chars
            || word.text.ends_with(['.', '!', '?', '。', '！', '？']);

        if should_split && !current_words.is_empty() {
            let segment_text = current_words
                .iter()
                .map(|w| w.text.as_str())
                .collect::<Vec<_>>()
                .join(" ");

            let segment_end = current_words.last().unwrap().end;

            segments.push(SubtitleSegment::new(
                segments.len() + 1,
                segment_start,
                segment_end,
                segment_text,
            ));

            current_words.clear();
            char_count = 0;
        }
    }

    segments
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_time_srt() {
        assert_eq!(SubtitleSegment::format_time_srt(0.0), "00:00:00,000");
        assert_eq!(SubtitleSegment::format_time_srt(90.5), "00:01:30,500");
        assert_eq!(SubtitleSegment::format_time_srt(3661.123), "01:01:01,123");
    }

    #[test]
    fn test_format_time_vtt() {
        assert_eq!(SubtitleSegment::format_time_vtt(0.0), "00:00:00.000");
        assert_eq!(SubtitleSegment::format_time_vtt(90.5), "00:01:30.500");
    }

    #[test]
    fn test_wrap_text() {
        let generator = SubtitleGenerator::new(20, 2);
        let text = "This is a very long text that should be wrapped properly";
        let wrapped = generator.wrap_text(text);
        let lines: Vec<&str> = wrapped.lines().collect();
        assert!(lines.len() <= 2);
        assert!(lines.iter().all(|line| line.len() <= 20));
    }

    #[test]
    fn test_generate_srt() {
        let generator = SubtitleGenerator::new(40, 2);
        let segments = vec![
            SubtitleSegment::new(1, 0.0, 3.5, "Hello world".to_string()),
            SubtitleSegment::new(2, 3.5, 7.0, "Second subtitle".to_string()),
        ];

        let srt = generator.generate_srt(&segments).unwrap();
        assert!(srt.contains("1"));
        assert!(srt.contains("00:00:00,000 --> 00:00:03,500"));
        assert!(srt.contains("Hello world"));
    }

    #[test]
    fn test_segments_from_asr_result() {
        let words = vec![
            AsrWord { text: "Hello".to_string(), start: 0.0, end: 0.5, confidence: 0.9 },
            AsrWord { text: "world".to_string(), start: 0.6, end: 1.0, confidence: 0.95 },
            AsrWord { text: ".".to_string(), start: 1.0, end: 1.1, confidence: 1.0 },
        ];

        let segments = segments_from_asr_result(&words, 5.0, 50);
        assert_eq!(segments.len(), 1);
        assert_eq!(segments[0].text, "Hello world .");
    }
}
