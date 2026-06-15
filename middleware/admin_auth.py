"""管理面板登录（/admin、/api/admin）。"""
import hashlib
import hmac
import os
import secrets
import time

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

COOKIE_NAME = "tts_admin_session"
SESSION_TTL_SEC = 86400 * 7


def get_admin_panel_password() -> str:
    env = (os.environ.get("ADMIN_PANEL_PASSWORD") or os.environ.get("TTS_ADMIN_PASSWORD") or "").strip()
    if env:
        return env
    try:
        from config import SETTINGS_FILE, load_json

        s = load_json(SETTINGS_FILE)
        return (s.get("middleware_admin_password") or s.get("admin_panel_password") or "").strip()
    except Exception:
        return ""


def _session_secret() -> bytes:
    pw = get_admin_panel_password()
    if not pw:
        return b""
    return hashlib.sha256(f"tts-admin:{pw}".encode()).digest()


def _make_token() -> str:
    secret = _session_secret()
    if not secret:
        return ""
    ts = str(int(time.time()))
    sig = hmac.new(secret, ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def _verify_token(token: str) -> bool:
    secret = _session_secret()
    if not secret or not token or "." not in token:
        return False
    ts, sig = token.split(".", 1)
    try:
        if abs(int(time.time()) - int(ts)) > SESSION_TTL_SEC:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret, ts.encode(), hashlib.sha256).hexdigest()
    return secrets.compare_digest(expected, sig)


def is_admin_authenticated(request: Request) -> bool:
    if not get_admin_panel_password():
        return True
    return _verify_token(request.cookies.get(COOKIE_NAME) or "")


def _inner_path(path: str) -> str:
    if path.startswith("/tts-mw/"):
        return path[8:] or "/"
    return path


class AdminPanelAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not get_admin_panel_password():
            return await call_next(request)

        # 鉴权在 strip 中间件之前执行，必须用完整 URL 路径
        path = request.url.path or ""
        inner = _inner_path(path)
        if not (inner.startswith("/admin") or inner.startswith("/api/admin")):
            return await call_next(request)

        if inner.startswith("/api/admin/auth/"):
            return await call_next(request)
        if inner == "/admin/login.html" or inner.startswith("/admin/css/") or inner.startswith("/admin/js/"):
            return await call_next(request)

        if not is_admin_authenticated(request):
            if inner.startswith("/api/admin"):
                return JSONResponse(status_code=401, content={"detail": "需要登录管理面板"})
            login = "/tts-mw/admin/login.html" if path.startswith("/tts-mw") else "/admin/login.html"
            return RedirectResponse(url=login, status_code=302)

        return await call_next(request)