import os
import glob
from fastapi import APIRouter
from config import init_settings, load_json, save_json, get_current_dirs, SETTINGS_FILE
from schemas import SettingsRequest

router = APIRouter()


@router.get("/ping")
def ping():
    """健康检查（Docker/酒馆扩展探测中间件是否可达）"""
    from middleware.api_auth import get_middleware_api_key

    return {
        "ok": True,
        "service": "sillytavern-gpt-sovits-manager",
        "port": 3000,
        "auth_required": bool(get_middleware_api_key()),
    }


@router.post("/clear_cache")
def clear_cache():
    _, cache_dir = get_current_dirs()
    if not os.path.exists(cache_dir): return {"status": "empty"}

    for f in glob.glob(os.path.join(cache_dir, "*.wav")):
        try: os.remove(f)
        except: pass
    return {"status": "success"}

@router.post("/update_settings")
def update(req: SettingsRequest):
    s = load_json(SETTINGS_FILE)

    if req.enabled is not None: s["enabled"] = req.enabled
    if req.auto_generate is not None: s["auto_generate"] = req.auto_generate
    if req.base_dir and req.base_dir.strip(): s["base_dir"] = req.base_dir.strip()
    if req.cache_dir and req.cache_dir.strip(): s["cache_dir"] = req.cache_dir.strip()
    if req.default_lang is not None: s["default_lang"] = req.default_lang
    if req.iframe_mode is not None: s["iframe_mode"] = req.iframe_mode
    if req.bubble_style is not None: s["bubble_style"] = req.bubble_style
    save_json(SETTINGS_FILE, s)
    # 强制刷新一次，确保目录被创建
    init_settings()
    return {"status": "success", "settings": s}
