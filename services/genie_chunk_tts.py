# -*- coding: utf-8 -*-
"""Genie 长文：按标点拆成多段合成再拼 WAV（不用 split_sentence，避免 G2P 长句崩溃）。"""
import io
import re
import wave
from typing import List

from services.genie_tts_client import pcm_to_wav_bytes, synthesize as genie_synthesize

# 单段超过此长度则尝试拆分（字符数）
CHUNK_THRESHOLD = 50
MAX_CHUNK = 36

_SPLIT_RE = re.compile(r"(?<=[。！？；\n])|(?<=[，、])|(?<=……)|(?<=…)")


def _normalize_ellipsis(text: str) -> str:
    return re.sub(r"……+", "……", text)


def split_text_for_genie(text: str) -> List[str]:
    text = _normalize_ellipsis((text or "").strip())
    if not text:
        return []
    if len(text) <= CHUNK_THRESHOLD:
        return [text]
    parts = [p.strip() for p in _SPLIT_RE.split(text) if p and p.strip()]
    if not parts:
        return [text]
    chunks: List[str] = []
    buf = ""
    for p in parts:
        if len(p) > MAX_CHUNK:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(p), MAX_CHUNK):
                chunks.append(p[i : i + MAX_CHUNK])
            continue
        if not buf:
            buf = p
        elif len(buf) + len(p) <= MAX_CHUNK:
            buf += p
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks if chunks else [text]


def _concat_wavs(wavs: List[bytes]) -> bytes:
    if not wavs:
        return b""
    if len(wavs) == 1:
        return wavs[0]
    out = io.BytesIO()
    params = None
    frames = []
    for w in wavs:
        with wave.open(io.BytesIO(w), "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames.append(wf.readframes(wf.getnframes()))
    with wave.open(out, "wb") as wo:
        wo.setparams(params)
        for fr in frames:
            wo.writeframes(fr)
    return out.getvalue()


def synthesize_genie_chunked(
    host: str,
    genie_name: str,
    text: str,
    *,
    split_sentence: bool = False,
) -> bytes:
    chunks = split_text_for_genie(text)
    if len(chunks) == 1:
        wav = genie_synthesize(host, genie_name, chunks[0], split_sentence=split_sentence)
        if len(wav) < 1024:
            raise RuntimeError("Genie 合成结果为空或过短")
        return wav

    wavs = []
    for i, ch in enumerate(chunks):
        wav = genie_synthesize(host, genie_name, ch, split_sentence=split_sentence)
        if len(wav) < 1024:
            raise RuntimeError(f"Genie 第 {i + 1}/{len(chunks)} 段合成失败（过短）: {ch[:40]}…")
        wavs.append(wav)
    return _concat_wavs(wavs)