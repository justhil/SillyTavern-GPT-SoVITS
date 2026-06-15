# -*- coding: utf-8 -*-
"""Genie TTS 连接检测与配置（替代原 Windows 整合包安装向导）。"""
import json
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter

from config import SETTINGS_FILE, GENIE_MODELS_FILE, load_json, save_json, get_genie_host, init_settings, _safe_load_for_update
from services.genie_tts_client import check_connection

router = APIRouter(prefix="/api/genie", tags=["Genie TTS"])


class GenieHostConfig(BaseModel):
    genie_host: str
    auto_check: bool = True


class GenieModelEntry(BaseModel):
    folder_name: str
    genie_character: str
    onnx_model_dir: str
    language: str = "zh"


@router.get("/status")
async def genie_status():
    host = get_genie_host()
    ok = check_connection(host)
    return {
        "engine": "genie",
        "url": host,
        "accessible": ok,
        "message": "Genie API 正常" if ok else "无法连接，请确认 genie-tts 已启动",
    }


@router.get("/config")
async def get_config():
    s = init_settings()
    models = load_json(GENIE_MODELS_FILE)
    return {
        "genie_host": get_genie_host(),
        "tts_engine": s.get("tts_engine", "genie"),
        "models": models,
    }


@router.post("/config")
async def save_host(cfg: GenieHostConfig):
    try:
        s = _safe_load_for_update(SETTINGS_FILE)
    except IOError:
        s = init_settings()
    s["genie_host"] = cfg.genie_host.strip().rstrip("/")
    s["sovits_host"] = s["genie_host"]
    s["tts_engine"] = "genie"
    save_json(SETTINGS_FILE, s)
    return {"success": True}


@router.post("/models")
async def upsert_model(entry: GenieModelEntry):
    models = load_json(GENIE_MODELS_FILE)
    models[entry.folder_name] = {
        "genie_character": entry.genie_character,
        "onnx_model_dir": entry.onnx_model_dir,
        "language": entry.language,
    }
    save_json(GENIE_MODELS_FILE, models)
    return {"success": True, "models": models}


@router.get("/test")
async def test_genie():
    host = get_genie_host()
    return {"success": check_connection(host), "url": host}


@router.get("/catalog")
async def genie_catalog():
    from services.genie_catalog import (
        get_genie_characters_root,
        get_genie_refs_root,
        scan_genie_character_folders,
        sync_genie_models_json_from_scan,
    )

    sync_genie_models_json_from_scan()
    folders = scan_genie_character_folders()
    return {
        "characters_root": get_genie_characters_root(),
        "refs_root": get_genie_refs_root(),
        "characters": folders,
        "total": len(folders),
    }