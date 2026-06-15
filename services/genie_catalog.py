# -*- coding: utf-8 -*-
"""Genie 目录 characters + refs，与中间件 MyCharacters 共用视图。"""
import os
from typing import Any, Dict, List

from config import GENIE_MODELS_FILE, get_genie_models, init_settings, load_json, save_json

AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".aiff", ".aif"}


def get_genie_characters_root() -> str:
    s = init_settings()
    return (
        os.environ.get("GENIE_CHARACTERS_ROOT")
        or s.get("genie_characters_root")
        or "/www/genie/characters"
    ).rstrip("/")


def get_genie_refs_root() -> str:
    s = init_settings()
    return (
        os.environ.get("GENIE_REFS_ROOT") or s.get("genie_refs_root") or "/www/genie/refs"
    ).rstrip("/")


def _has_onnx(model_dir: str) -> bool:
    if not os.path.isdir(model_dir):
        return False
    if os.path.isfile(os.path.join(model_dir, "vits_fp32.onnx")):
        return True
    if os.path.isfile(os.path.join(model_dir, "onnx", "vits_fp32.onnx")):
        return True
    for root, _, files in os.walk(model_dir):
        if "vits_fp32.onnx" in files:
            return True
    return False


def resolve_onnx_dir(model_dir: str) -> str:
    model_dir = os.path.abspath(model_dir)
    if os.path.isfile(os.path.join(model_dir, "vits_fp32.onnx")):
        return model_dir
    sub = os.path.join(model_dir, "onnx")
    if os.path.isfile(os.path.join(sub, "vits_fp32.onnx")):
        return sub
    for root, _, files in os.walk(model_dir):
        if "vits_fp32.onnx" in files:
            return root
    return model_dir


def scan_genie_character_folders() -> List[Dict[str, Any]]:
    root = get_genie_characters_root()
    if not os.path.isdir(root):
        return []
    out = []
    base_dir = init_settings().get("base_dir") or ""
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isdir(path) or not _has_onnx(path):
            continue
        onnx_dir = resolve_onnx_dir(path)
        refs_dir = os.path.join(get_genie_refs_root(), name)
        ref_count = 0
        if os.path.isdir(refs_dir):
            for _, _, fns in os.walk(refs_dir):
                ref_count += sum(1 for f in fns if os.path.splitext(f)[1].lower() in AUDIO_EXT)
        gm = get_genie_models().get(name, {})
        mc_ref = os.path.join(base_dir, name, "reference_audios")
        out.append(
            {
                "name": name,
                "folder_name": name,
                "path": path,
                "onnx_model_dir": onnx_dir,
                "genie_character": gm.get("genie_character") or name,
                "language": gm.get("language", "zh"),
                "valid": True,
                "engine": "genie",
                "files": {
                    "onnx": True,
                    "gpt_weights": False,
                    "sovits_weights": False,
                    "reference_audios": ref_count > 0 or os.path.isdir(mc_ref),
                },
                "audio_stats": {"total": ref_count, "refs_root": refs_dir},
            }
        )
    return out


def list_reference_audios_for_folder(folder_name: str, base_dir: str) -> List[Dict[str, Any]]:
    audios: List[Dict[str, Any]] = []
    seen = set()

    def add(full_path: str, rel: str, source: str):
        if os.path.islink(full_path) or not os.path.isfile(full_path):
            full_path = os.path.realpath(full_path)
        if not os.path.isfile(full_path):
            return
        key = os.path.normcase(full_path)
        if key in seen:
            return
        seen.add(key)
        fn = os.path.basename(full_path)
        emotion = fn.split("_")[0] if "_" in fn else "default"
        audios.append(
            {
                "filename": fn,
                "path": full_path,
                "relative_path": rel,
                "language": "Chinese",
                "emotion": emotion,
                "size": os.path.getsize(full_path),
                "source": source,
            }
        )

    refs = os.path.join(get_genie_refs_root(), folder_name)
    if os.path.isdir(refs):
        for fn in sorted(os.listdir(refs)):
            if os.path.splitext(fn)[1].lower() in AUDIO_EXT:
                add(os.path.join(refs, fn), f"refs/{fn}", "genie_refs")

    mc = os.path.join(base_dir, folder_name, "reference_audios")
    if os.path.isdir(mc):
        for root, _, fns in os.walk(mc):
            for fn in fns:
                if os.path.splitext(fn)[1].lower() not in AUDIO_EXT:
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, mc).replace(os.sep, "/")
                add(full, rel, "mycharacters")

    return audios


def sync_genie_models_json_from_scan() -> Dict[str, Any]:
    models = load_json(GENIE_MODELS_FILE)
    for item in scan_genie_character_folders():
        fn = item["folder_name"]
        entry = {
            "genie_character": item["genie_character"],
            "onnx_model_dir": item["onnx_model_dir"],
            "language": item["language"],
        }
        models[fn] = {**models.get(fn, {}), **entry}
    save_json(GENIE_MODELS_FILE, models)
    return models