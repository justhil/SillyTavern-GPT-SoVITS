# -*- coding: utf-8 -*-
"""角色文件夹 → Genie API 桥接。"""
import os
from typing import Dict, Optional, Tuple

from config import (
    get_current_dirs,
    get_genie_host,
    get_genie_models,
    load_json,
    MAPPINGS_FILE,
    get_tts_engine,
)
from services.genie_tts_client import ensure_character, set_reference


def _lang_code(prompt_lang: str) -> str:
    m = {
        "chinese": "zh",
        "zh": "zh",
        "中文": "zh",
        "english": "en",
        "en": "en",
        "japanese": "jp",
        "ja": "jp",
        "jp": "jp",
        "korean": "kr",
        "ko": "kr",
    }
    return m.get((prompt_lang or "zh").lower(), "zh")


def resolve_genie_for_character(char_name: str) -> Optional[Dict]:
    """
    返回 {genie_name, onnx_dir, language, model_folder} 或 None
    """
    mappings = load_json(MAPPINGS_FILE)
    if char_name not in mappings:
        return None
    folder = mappings[char_name]
    gm = get_genie_models()
    if folder in gm:
        e = gm[folder]
        return {
            "model_folder": folder,
            "genie_name": e["genie_character"],
            "onnx_dir": e["onnx_model_dir"],
            "language": e.get("language", "zh"),
        }
    from services.genie_catalog import get_genie_characters_root, resolve_onnx_dir

    groot = os.path.join(get_genie_characters_root(), folder)
    if os.path.isdir(groot) and os.path.isfile(
        os.path.join(resolve_onnx_dir(groot), "vits_fp32.onnx")
    ):
        return {
            "model_folder": folder,
            "genie_name": folder,
            "onnx_dir": resolve_onnx_dir(groot),
            "language": "zh",
        }
    base_dir, _ = get_current_dirs()
    onnx = os.path.join(base_dir, folder, "onnx")
    if os.path.isdir(onnx) and os.path.isfile(os.path.join(onnx, "vits_fp32.onnx")):
        return {
            "model_folder": folder,
            "genie_name": folder,
            "onnx_dir": os.path.abspath(onnx),
            "language": "zh",
        }
    return None


def prepare_genie_session(
    char_name: str,
    ref_audio_path: str,
    prompt_text: str,
    prompt_lang: str,
) -> Tuple[str, str]:
    """load + set_reference，返回 (host, genie_name)"""
    info = resolve_genie_for_character(char_name)
    if not info:
        raise ValueError(f"角色 {char_name} 未配置 Genie ONNX（见 genie_character_models.json 或 MyCharacters/模型/onnx）")
    host = get_genie_host()
    lang = _lang_code(prompt_lang)
    ensure_character(host, info["genie_name"], info["onnx_dir"], info["language"])
    set_reference(host, info["genie_name"], ref_audio_path, prompt_text or "", lang)
    return host, info["genie_name"]


def is_genie_engine() -> bool:
    return get_tts_engine() == "genie"