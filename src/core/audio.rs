use std::path::{Path, PathBuf};
use std::process::Command;
use tracing::{debug, info, trace};

use crate::VsubError;

/// 音频提取器
pub struct AudioExtractor {
    ffmpeg_path: PathBuf,
}

impl AudioExtractor {
    /// 创建新的音频提取器
    pub fn new() -> Result<Self, VsubError> {
        let ffmpeg_path = super::video::check_ffmpeg()?;
        Ok(Self { ffmpeg_path })
    }

    /// 提取音频为 WAV 格式（PCM 16-bit, 16kHz, mono）
    /// 这是 ASR 引擎的最佳输入格式
    pub fn extract_to_wav<P: AsRef<Path>, Q: AsRef<Path>>(
        &self,
        video_path: P,
        output_path: Q,
    ) -> Result<(), VsubError> {
        let video_path = video_path.as_ref();
        let output_path = output_path.as_ref();

        info!("提取音频: {} -> {}", video_path.display(), output_path.display());
        trace!("FFmpeg: {}", self.ffmpeg_path.display());

        // 如果输出文件已存在，先删除
        if output_path.exists() {
            std::fs::remove_file(output_path)
                .map_err(|e| VsubError::Io(e))?;
        }

        let output = Command::new(&self.ffmpeg_path)
            .args(&[
                "-y",
                "-i", video_path.to_str().unwrap(),
                "-vn",                          // 无视频
                "-acodec", "pcm_s16le",         // PCM 16-bit 小端
                "-ar", "16000",                 // 16kHz 采样率
                "-ac", "1",                     // 单声道
                output_path.to_str().unwrap(),
            ])
            .output()
            .map_err(|e| VsubError::Audio(format!("FFmpeg 执行失败: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(VsubError::Audio(format!("音频提取失败: {}", stderr)));
        }

        // 验证输出文件
        if !output_path.exists() {
            return Err(VsubError::Audio("输出文件未生成".to_string()));
        }

        let metadata = std::fs::metadata(output_path)
            .map_err(|e| VsubError::Io(e))?;

        if metadata.len() == 0 {
            return Err(VsubError::Audio("输出文件为空".to_string()));
        }

        debug!("音频提取完成: {} 字节", metadata.len());

        Ok(())
    }

    /// 获取音频时长（秒）
    pub fn get_audio_duration<P: AsRef<Path>>(&self, audio_path: P) -> Result<f64, VsubError> {
        let audio_path = audio_path.as_ref();

        let output = Command::new(&self.ffmpeg_path)
            .args(&[
                "-i", audio_path.to_str().unwrap(),
                "-f", "null",
                "-",
            ])
            .output()
            .map_err(|e| VsubError::Audio(format!("FFmpeg 执行失败: {}", e)))?;

        // FFmpeg 输出到 stderr
        let stderr = String::from_utf8_lossy(&output.stderr);

        // 解析 Duration: 00:00:12.34
        for line in stderr.lines() {
            if let Some(start) = line.find("Duration: ") {
                let duration_str = &line[start + 10..];
                if let Some(end) = duration_str.find(',') {
                    let time_str = &duration_str[..end];
                    if let Ok(duration) = parse_duration(time_str) {
                        return Ok(duration);
                    }
                }
            }
        }

        Err(VsubError::Audio("无法获取音频时长".to_string()))
    }
}

fn parse_duration(time_str: &str) -> Result<f64, VsubError> {
    // 格式: HH:MM:SS.sss
    let parts: Vec<&str> = time_str.split(':').collect();
    if parts.len() != 3 {
        return Err(VsubError::Audio("无效的时长格式".to_string()));
    }

    let hours: f64 = parts[0].parse().map_err(|_| VsubError::Audio("无效的小时".to_string()))?;
    let minutes: f64 = parts[1].parse().map_err(|_| VsubError::Audio("无效的分钟".to_string()))?;
    let seconds: f64 = parts[2].parse().map_err(|_| VsubError::Audio("无效的秒数".to_string()))?;

    Ok(hours * 3600.0 + minutes * 60.0 + seconds)
}

/// 生成临时音频文件路径
pub fn temp_audio_path(video_path: &Path) -> PathBuf {
    let stem = video_path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("audio");

    let temp_dir = std::env::temp_dir();
    temp_dir.join(format!("{}_{}.wav", stem, rand::random::<u32>()))
}

/// 清理临时音频文件
pub fn cleanup_audio<P: AsRef<Path>>(path: P) {
    let path = path.as_ref();
    if path.exists() {
        if let Err(e) = std::fs::remove_file(path) {
            tracing::warn!("无法删除临时音频文件 {}: {}", path.display(), e);
        } else {
            tracing::debug!("已删除临时音频文件: {}", path.display());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_duration() {
        assert_eq!(parse_duration("00:01:30.500").unwrap(), 90.5);
        assert_eq!(parse_duration("01:00:00.000").unwrap(), 3600.0);
        assert_eq!(parse_duration("00:00:12.340").unwrap(), 12.34);
    }
}
