# -*- coding: utf-8 -*-
"""Genie TTS API 客户端（POST /load_character, /set_reference_audio, /tts）。"""
import io
import wave
import json
import hashlib
from typing import Dict, Optional

import requests

SAMPLE_RATE = 32000
CHANNELS = 1
SAMPLE_WIDTH = 2

_loaded_characters: set[str] = set()
_ref_cache: Dict[str, tuple] = {}  # key -> (audio_path, audio_text, lang)


def pcm_to_wav_bytes(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


def _post(host: str, path: str, body: dict, timeout: int = 300) -> requests.Response:
    url = f"{host.rstrip('/')}{path}"
    return requests.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
        proxies={"http": None, "https": None},
    )


def ensure_character(host: str, genie_name: str, onnx_dir: str, language: str = "zh") -> None:
    if genie_name in _loaded_characters:
        return
    r = _post(
        host,
        "/load_character",
        {
            "character_name": genie_name,
            "onnx_model_dir": onnx_dir,
            "language": language,
        },
    )
    if r.status_code != 200:
        raise RuntimeError(f"Genie load_character failed: {r.status_code} {r.text[:300]}")
    _loaded_characters.add(genie_name)


def set_reference(
    host: str,
    genie_name: str,
    audio_path: str,
    audio_text: str,
    language: str = "zh",
) -> None:
    key = f"{genie_name}|{audio_path}|{audio_text}|{language}"
    if _ref_cache.get(genie_name) == (audio_path, audio_text, language):
        return
    r = _post(
        host,
        "/set_reference_audio",
        {
            "character_name": genie_name,
            "audio_path": audio_path,
            "audio_text": audio_text,
            "language": language,
        },
    )
    if r.status_code != 200:
        raise RuntimeError(f"Genie set_reference_audio failed: {r.status_code} {r.text[:300]}")
    _ref_cache[genie_name] = (audio_path, audio_text, language)


def synthesize(
    host: str,
    genie_name: str,
    text: str,
    split_sentence: bool = False,
) -> bytes:
    r = _post(
        host,
        "/tts",
        {
            "character_name": genie_name,
            "text": text,
            "split_sentence": split_sentence,
        },
        timeout=600,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Genie tts failed: {r.status_code} {r.text[:300]}")
    if len(r.content) < 256:
        raise RuntimeError(f"Genie /tts 响应过短 ({len(r.content)} bytes)")
    return pcm_to_wav_bytes(r.content)


def check_connection(host: str, timeout: int = 5) -> bool:
    try:
        r = requests.get(f"{host.rstrip('/')}/docs", timeout=timeout, proxies={"http": None, "https": None})
        return r.status_code == 200
    except Exception:
        return False


def cache_key(text: str, emotion: str, text_lang: str, prompt_lang: str) -> str:
    raw = f"genie_{text}_{emotion}_{text_lang}_{prompt_lang}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest() + ".wav"