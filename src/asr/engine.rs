use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};

/// ASR 识别结果 - 单词级别
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AsrWord {
    pub text: String,
    pub start: f64,
    pub end: f64,
    #[serde(default)]
    pub confidence: f32,
}

/// ASR 片段结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AsrSegment {
    pub text: String,
    pub start: f64,
    pub end: f64,
    pub words: Option<Vec<AsrWord>>,
}

/// ASR 完整结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AsrResult {
    pub segments: Vec<AsrSegment>,
    pub language: Option<String>,
    pub duration: f64,
}

/// ASR 引擎接口
#[async_trait::async_trait]
pub trait AsrEngine: Send + Sync {
    /// 识别音频文件，返回单词级别的时间戳
    async fn transcribe(
        &self,
        audio_path: &Path,
        language: Option<&str>,
    ) -> crate::Result<Vec<AsrWord>>;

    /// 检查引擎是否可用
    fn is_available(&self) -> bool;

    /// 引擎名称
    fn name(&self) -> &'static str;
}

/// 引擎工厂
pub fn create_engine(engine_type: crate::core::config::AsrEngine) -> Box<dyn AsrEngine> {
    match engine_type {
        crate::core::config::AsrEngine::Whisper => {
            Box::new(PythonWhisperEngine::default())
        }
    }
}

/// Python Whisper 引擎实现
pub struct PythonWhisperEngine {
    python_path: PathBuf,
    script_path: PathBuf,
    model: String,
}

impl Default for PythonWhisperEngine {
    fn default() -> Self {
        Self {
            python_path: PathBuf::from("python3"),
            script_path: PathBuf::from("python/whisper_engine.py"),
            model: "base".to_string(),
        }
    }
}

impl PythonWhisperEngine {
    pub fn new(python_path: PathBuf, script_path: PathBuf, model: String) -> Self {
        Self { python_path, script_path, model }
    }

    fn find_whisper_script(&self) -> Option<PathBuf> {
        // 检查多个可能的位置
        let candidates = [
            self.script_path.clone(),
            PathBuf::from("whisper_engine.py"),
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|p| p.join("whisper_engine.py")))
                .unwrap_or_default(),
            PathBuf::from("/usr/local/share/vsub/whisper_engine.py"),
            PathBuf::from("/usr/share/vsub/whisper_engine.py"),
        ];

        for path in &candidates {
            if path.exists() {
                return Some(path.clone());
            }
        }

        None
    }
}

#[async_trait::async_trait]
impl AsrEngine for PythonWhisperEngine {
    async fn transcribe(
        &self,
        audio_path: &Path,
        language: Option<&str>,
    ) -> crate::Result<Vec<AsrWord>> {
        let script = self.find_whisper_script()
            .ok_or_else(|| crate::VsubError::PythonEngineNotFound)?;

        let mut args = vec![
            script.to_str().unwrap().to_string(),
            audio_path.to_str().unwrap().to_string(),
            "--model".to_string(),
            self.model.clone(),
        ];

        if let Some(lang) = language {
            args.push("--language".to_string());
            args.push(lang.to_string());
        }

        args.push("--output-json".to_string());

        let output = tokio::process::Command::new(&self.python_path)
            .args(&args)
            .output()
            .await
            .map_err(|e| crate::VsubError::Asr(format!("Python 引擎执行失败: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(crate::VsubError::Asr(format!("Whisper 识别失败: {}", stderr)));
        }

        // 解析 JSON 输出
        let stdout = String::from_utf8_lossy(&output.stdout);
        let result: AsrResult = serde_json::from_str(&stdout)
            .map_err(|e| crate::VsubError::Asr(format!("解析识别结果失败: {}", e)))?;

        // 展开为单词列表
        let mut words = Vec::new();
        for segment in result.segments {
            if let Some(segment_words) = segment.words {
                words.extend(segment_words);
            } else {
                // 如果没有单词级时间戳，使用片段时间戳
                words.push(AsrWord {
                    text: segment.text.trim().to_string(),
                    start: segment.start,
                    end: segment.end,
                    confidence: 1.0,
                });
            }
        }

        Ok(words)
    }

    fn is_available(&self) -> bool {
        // 检查 Python 是否可用
        let python_ok = std::process::Command::new(&self.python_path)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);

        // 检查脚本是否存在
        let script_ok = self.find_whisper_script().is_some();

        python_ok && script_ok
    }

    fn name(&self) -> &'static str {
        "python-whisper"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_asr_result_deserialization() {
        let json = r#"
        {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 2.0,
                    "words": [
                        {"text": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
                        {"text": "world", "start": 0.6, "end": 1.0, "confidence": 0.9}
                    ]
                }
            ],
            "language": "en",
            "duration": 2.0
        }
        "#;

        let result: AsrResult = serde_json::from_str(json).unwrap();
        assert_eq!(result.segments.len(), 1);
        assert_eq!(result.language, Some("en".to_string()));
    }
}
