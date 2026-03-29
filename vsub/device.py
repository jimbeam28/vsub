"""设备检测模块"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# 模块级别导入 torch，避免重复导入
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False


class DeviceType(str, Enum):
    """设备类型"""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Metal Performance Shaders (Apple Silicon)


def check_cuda_available() -> bool:
    """检查 CUDA 是否可用"""
    if not TORCH_AVAILABLE:
        return False
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def check_mps_available() -> bool:
    """检查 MPS (Metal Performance Shaders) 是否可用"""
    if not TORCH_AVAILABLE:
        return False
    try:
        return torch.backends.mps.is_available()
    except (AttributeError, Exception):
        return False


def get_device(prefer_gpu: bool = True) -> str:
    """
    获取最佳可用设备

    Args:
        prefer_gpu: 是否优先使用 GPU

    Returns:
        设备名称: "cuda", "mps", 或 "cpu"
    """
    if not prefer_gpu:
        logger.debug("使用 CPU (用户指定)")
        return DeviceType.CPU

    # 检查 CUDA
    if check_cuda_available() and TORCH_AVAILABLE:
        try:
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"检测到 CUDA 设备: {device_name}")
            return DeviceType.CUDA
        except Exception as e:
            logger.warning(f"检测 CUDA 时出错: {e}")

    # 检查 MPS (Apple Silicon)
    if check_mps_available():
        logger.info("检测到 MPS 设备 (Apple Silicon)")
        return DeviceType.MPS

    logger.debug("未检测到 GPU 加速设备，使用 CPU")
    return DeviceType.CPU


def get_device_info() -> dict:
    """获取设备信息"""
    info = {
        "cpu": True,
        "cuda": False,
        "cuda_devices": 0,
        "cuda_device_name": None,
        "mps": False,
        "recommended": DeviceType.CPU.value,
    }

    if not TORCH_AVAILABLE:
        return info

    # 检查 CUDA
    try:
        if torch.cuda.is_available():
            info["cuda"] = True
            info["cuda_devices"] = torch.cuda.device_count()
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            info["recommended"] = DeviceType.CUDA.value
    except Exception:
        pass

    # 检查 MPS
    try:
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            info["mps"] = True
            if info["recommended"] == DeviceType.CPU.value:
                info["recommended"] = DeviceType.MPS.value
    except Exception:
        pass

    return info


def format_device_info(info: Optional[dict] = None) -> str:
    """格式化设备信息为可读字符串"""
    if info is None:
        info = get_device_info()

    lines = ["设备信息:"]
    lines.append("  CPU: 可用")

    if info.get("cuda"):
        lines.append("  CUDA: 可用")
        lines.append(f"  CUDA 设备: {info.get('cuda_device_name', '未知')}")
        lines.append(f"  CUDA 数量: {info.get('cuda_devices', 0)}")
    else:
        lines.append("  CUDA: 不可用")

    if info.get("mps"):
        lines.append("  MPS (Apple Silicon): 可用")
    else:
        lines.append("  MPS (Apple Silicon): 不可用")

    lines.append(f"  推荐设备: {info.get('recommended', 'cpu')}")

    return "\n".join(lines)
