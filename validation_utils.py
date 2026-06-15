"""
TTS 参数验证工具模块
提供参数验证和服务连接性检测功能
"""
import os
import requests
from typing import Dict, Optional, Tuple
from fastapi import HTTPException


def validate_required_params(
    text: str,
    text_lang: str,
    ref_audio_path: str,
    prompt_lang: str
) -> None:
    """
    验证必填参数是否为空
    
    Args:
        text: 待合成文本
        text_lang: 文本语言
        ref_audio_path: 参考音频路径
        prompt_lang: 提示文本语言
        
    Raises:
        HTTPException: 参数缺失时抛出 400 错误
    """
    missing_params = []
    
    if not text or text.strip() == "":
        missing_params.append("text(待合成文本)")
    
    if not text_lang or text_lang.strip() == "":
        missing_params.append("text_lang(文本语言)")
    
    if not ref_audio_path or ref_audio_path.strip() == "":
        missing_params.append("ref_audio_path(参考音频路径)")
    
    if not prompt_lang or prompt_lang.strip() == "":
        missing_params.append("prompt_lang(提示文本语言)")
    
    if missing_params:
        error_msg = f"缺少必填参数: {', '.join(missing_params)}"
        raise HTTPException(status_code=400, detail=error_msg)


def validate_audio_path(ref_audio_path: str) -> None:
    """
    验证参考音频文件路径是否存在
    
    Args:
        ref_audio_path: 参考音频文件路径
        
    Raises:
        HTTPException: 路径无效时抛出 400 错误
    """
    if not os.path.exists(ref_audio_path):
        error_msg = f"参考音频文件不存在: {ref_audio_path}"
        raise HTTPException(status_code=400, detail=error_msg)
    
    if not os.path.isfile(ref_audio_path):
        error_msg = f"参考音频路径不是有效文件: {ref_audio_path}"
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 验证文件扩展名
    valid_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
    _, ext = os.path.splitext(ref_audio_path)
    if ext.lower() not in valid_extensions:
        error_msg = f"不支持的音频格式: {ext},支持的格式: {', '.join(valid_extensions)}"
        raise HTTPException(status_code=400, detail=error_msg)


def check_sovits_connection(sovits_host: str, timeout: int = 3) -> None:
    """检测 TTS 后端连接（Genie 默认）。"""
    from config import get_tts_engine
    if get_tts_engine() == "genie":
        from services.genie_tts_client import check_connection
        if not check_connection(sovits_host, timeout=timeout):
            raise HTTPException(
                status_code=503,
                detail=f"无法连接 Genie TTS API，请确认 genie-tts 已启动 (地址: {sovits_host})"
            )
        return
    try:
        response = requests.get(f"{sovits_host}/", timeout=timeout, proxies={'http': None, 'https': None})
        if response.status_code >= 500:
            raise HTTPException(
                status_code=503,
                detail=f"GPT-SoVITS 服务异常(状态码 {response.status_code}),请检查服务运行状态"
            )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=503,
            detail=f"连接 GPT-SoVITS 服务超时,请检查服务是否启动(地址: {sovits_host})"
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=f"无法连接到 GPT-SoVITS 服务,请检查服务是否启动(地址: {sovits_host})"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"GPT-SoVITS 服务连接失败: {str(e)}"
        )


def validate_tts_request(
    text: str,
    text_lang: str,
    ref_audio_path: str,
    prompt_lang: str,
    sovits_host: str,
    char_name: Optional[str] = None,
) -> None:
    """
    综合验证 TTS 请求的所有参数
    
    Args:
        text: 待合成文本
        text_lang: 文本语言
        ref_audio_path: 参考音频路径
        prompt_lang: 提示文本语言
        sovits_host: SoVITS 服务地址
        
    Raises:
        HTTPException: 验证失败时抛出相应错误
    """
    # 1. 验证必填参数
    validate_required_params(text, text_lang, ref_audio_path, prompt_lang)
    
    validate_audio_path(ref_audio_path)
    from config import get_tts_engine
    if get_tts_engine() == "genie":
        if not char_name or not str(char_name).strip():
            raise HTTPException(status_code=400, detail="Genie 模式需要 char_name（酒馆角色名）")
        from services.genie_bridge import resolve_genie_for_character
        if not resolve_genie_for_character(char_name):
            raise HTTPException(
                status_code=400,
                detail=f"角色 {char_name} 未配置 Genie ONNX，请在 genie_character_models.json 或模型目录 onnx/ 下配置"
            )
    check_sovits_connection(sovits_host)
