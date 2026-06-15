"""中间件 API 鉴权：环境变量 TTS_MW_API_KEY 非空时要求请求携带密钥。"""
import os
import secrets
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def get_middleware_api_key() -> str:
    env = (os.environ.get("TTS_MW_API_KEY") or "").strip()
    if env:
        return env
    try:
        from config import SETTINGS_FILE, load_json

        s = load_json(SETTINGS_FILE)
        return (s.get("middleware_api_key") or "").strip()
    except Exception:
        return ""


def _extract_key(request: Request) -> Optional[str]:
    h = request.headers.get("X-TTS-API-Key") or request.headers.get("X-Api-Key")
    if h and h.strip():
        return h.strip()
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.query_params.get("api_key") or request.query_params.get("tts_api_key")


class MiddlewareApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = get_middleware_api_key()
        if not expected:
            return await call_next(request)

        path = request.url.path or ""
        if (
            path.startswith("/admin")
            or path.startswith("/static")
            or path.startswith("/api/admin")
        ):
            return await call_next(request)

        provided = _extract_key(request)
        if not provided or not secrets.compare_digest(provided, expected):
            return JSONResponse(
                status_code=401,
                content={"detail": "需要有效的中间件 API 密钥（X-TTS-API-Key 或 Authorization: Bearer）"},
            )
        return await call_next(request)