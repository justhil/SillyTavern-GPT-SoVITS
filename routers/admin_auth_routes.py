# -*- coding: utf-8 -*-
from fastapi import APIRouter, Response
from pydantic import BaseModel

from middleware.admin_auth import (
    COOKIE_NAME,
    SESSION_TTL_SEC,
    _make_token,
    get_admin_panel_password,
    is_admin_authenticated,
)
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["Admin Auth"])


class LoginBody(BaseModel):
    password: str


@router.get("/status")
def auth_status(request: Request):
    configured = bool(get_admin_panel_password())
    return {
        "password_required": configured,
        "authenticated": is_admin_authenticated(request) if configured else True,
    }


@router.post("/login")
def login(body: LoginBody, response: Response):
    expected = get_admin_panel_password()
    if not expected:
        return {"success": True, "message": "未启用管理密码"}
    import secrets

    if not secrets.compare_digest(body.password.strip(), expected):
        return {"success": False, "detail": "密码错误"}
    token = _make_token()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_TTL_SEC,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"success": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"success": True}