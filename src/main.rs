use anyhow::Context;
use clap::Parser;
use std::io::Write;
use tracing::{info, warn, error, Level};

use vsub::cli::Cli;
use vsub::core::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 解析命令行参数
    let cli = Cli::parse();

    // 处理 --init 命令
    if cli.init {
        return init_config().await;
    }

    // 验证参数
    if let Err(e) = cli.validate() {
        eprintln!("错误: {}", e);
        std::process::exit(1);
    }

    // 设置日志
    setup_logging(cli.verbose);

    // 加载配置
    let config = load_config(&cli);
    info!("配置加载完成: {:?}", config);

    // 获取输入文件
    let inputs = cli.get_input_files();
    info!("处理 {} 个文件", inputs.len());

    // 检查是否是批量处理
    if inputs.len() > 1 {
        // TODO: Phase 3 实现批量处理
        println!("批量处理功能尚未实现，当前只处理第一个文件");
    }

    // 处理单个文件
    let input = &inputs[0];
    info!("处理文件: {}", input.display());

    // 调用处理函数
    match vsub::process_video(input, &config).await {
        Ok(output_path) => {
            println!("✓ 字幕已保存: {}", output_path.display());
            Ok(())
        }
        Err(e) => {
            error!("处理失败: {}", e);
            match e {
                vsub::VsubError::Video(msg) if msg == "功能尚未实现" => {
                    println!("注意: 核心功能将在 Phase 2 实现");
                    Ok(())
                }
                _ => {
                    eprintln!("错误: {}", e);
                    std::process::exit(1);
                }
            }
        }
    }
}

/// 设置日志记录
fn setup_logging(verbose: bool) {
    let level = if verbose {
        Level::DEBUG
    } else {
        Level::INFO
    };

    tracing_subscriber::fmt()
        .with_max_level(level)
        .with_target(false)
        .with_thread_ids(false)
        .with_file(false)
        .with_line_number(false)
        .init();
}

/// 加载配置（文件 + 命令行合并）
fn load_config(cli: &Cli) -> Config {
    let mut config = Config::load();

    // 应用命令行参数覆盖
    if let Some(format) = cli.format {
        config.format = format.to_format();
    }
    if let Some(model) = cli.model {
        config.model = model.to_model();
    }
    if cli.language.is_some() {
        config.language = cli.language.clone();
    }
    if cli.keep_audio {
        config.keep_audio = true;
    }
    if cli.overwrite {
        config.overwrite = true;
    }
    if cli.output.is_some() {
        // 从输出路径推断输出目录
        let output = cli.output.as_ref().unwrap();
        if let Some(parent) = output.parent() {
            if !parent.as_os_str().is_empty() {
                config.output_dir = Some(parent.to_path_buf());
            }
        }
    }

    config
}

/// 生成默认配置文件
async fn init_config() -> anyhow::Result<()> {
    let config_path = std::path::PathBuf::from("vsub.toml");

    if config_path.exists() {
        print!("配置文件 vsub.toml 已存在，是否覆盖? [y/N] ");
        std::io::stdout().flush()?;

        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;

        if !input.trim().eq_ignore_ascii_case("y") {
            println!("已取消");
            return Ok(());
        }
    }

    let content = Config::default_config_toml();
    tokio::fs::write(&config_path, content)
        .await
        .with_context(|| format!("无法写入配置文件: {}", config_path.display()))?;

    println!("✓ 配置文件已生成: {}", config_path.display());
    println!("您可以使用以下命令编辑配置文件:");
    println!("  vim vsub.toml");

    Ok(())
}
