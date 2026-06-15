import uvicorn
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# 导入配置和路由
from config import FRONTEND_DIR, init_settings
from routers import data, tts, system, admin, phone_call, speakers, eavesdrop, continuous_analysis, genie_admin

# 导入自定义日志中间件
from middleware.logging_middleware import LoggingMiddleware
from middleware.api_auth import MiddlewareApiKeyMiddleware

# 初始化配置(确保 system_settings.json 和目录存在)
init_settings()

app = FastAPI()


def _public_prefix(request: Request) -> str:
    h = (request.headers.get("X-Forwarded-Prefix") or "").strip().rstrip("/")
    if h:
        return h
    path = request.scope.get("path") or request.url.path or ""
    if path.startswith("/tts-mw/") or path == "/tts-mw":
        return "/tts-mw"
    return ""


@app.middleware("http")
async def strip_tts_mw_prefix(request: Request, call_next):
    """反代 /tts-mw/* 时去掉前缀；响应里把 Location 补回公网路径"""
    path = request.scope.get("path") or request.url.path
    if path.startswith("/tts-mw/"):
        request.scope["path"] = path[8:]
        request.scope["raw_path"] = request.scope["path"].encode()
    elif path == "/tts-mw":
        request.scope["path"] = "/"
        request.scope["raw_path"] = b"/"
    response = await call_next(request)
    prefix = _public_prefix(request)
    if not prefix:
        return response
    loc = response.headers.get("location")
    if not loc:
        return response
    if loc.startswith(prefix + "/") or loc == prefix:
        return response
    if loc.startswith("/"):
        response.headers["location"] = prefix + loc
    return response


app.add_middleware(MiddlewareApiKeyMiddleware)
app.add_middleware(LoggingMiddleware)

# 1. CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["X-Audio-Filename", "Content-Type", "Content-Length"],
)

# 添加验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"\n[ValidationError] ❌ 请求验证失败:")
    print(f"  - URL: {request.url}")
    print(f"  - Method: {request.method}")
    print(f"  - 错误详情: {exc.errors()}")
    try:
        body = await request.body()
        print(f"  - 请求体: {body.decode('utf-8')}")
    except:
        pass
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


# 2. 挂载静态文件 (前端界面)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
else:
    print(f"Warning: 'frontend' folder not found at {FRONTEND_DIR}")

# 挂载管理面板静态文件
admin_dir = os.path.join(os.path.dirname(__file__), "admin")
if os.path.exists(admin_dir):
    app.mount("/admin", StaticFiles(directory=admin_dir, html=True), name="admin")
else:
    print(f"Warning: 'admin' folder not found at {admin_dir}")

os.makedirs("data/favorites_audio", exist_ok=True)
app.mount("/favorites", StaticFiles(directory="data/favorites_audio"), name="favorites")

# 挂载主动电话音频目录 - 使用自定义路由处理中文路径
from config import init_settings
from fastapi.responses import FileResponse
from urllib.parse import unquote

cache_dir = init_settings().get("cache_dir", "Cache")
auto_call_audio_dir = os.path.join(cache_dir, "auto_phone_calls")
os.makedirs(auto_call_audio_dir, exist_ok=True)

# 自定义路由处理 URL 编码的中文路径
@app.get("/auto_call_audio/{speaker_name}/{filename}")
async def serve_auto_call_audio(speaker_name: str, filename: str):
    """
    提供自动电话音频文件
    
    手动解码 URL 路径以支持中文字符
    """
    # URL 解码
    speaker_name = unquote(speaker_name)
    filename = unquote(filename)
    
    # 构建文件路径
    file_path = os.path.join(auto_call_audio_dir, speaker_name, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"音频文件不存在: {speaker_name}/{filename}")
    
    # 返回文件
    return FileResponse(
        file_path,
        media_type="audio/wav",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

# 挂载对话追踪音频目录
eavesdrop_audio_dir = os.path.join(cache_dir, "eavesdrop")
os.makedirs(eavesdrop_audio_dir, exist_ok=True)

@app.get("/api/audio/eavesdrop/{filename}")
async def serve_eavesdrop_audio(filename: str):
    """
    提供对话追踪音频文件
    """
    # URL 解码
    filename = unquote(filename)
    
    # 构建文件路径
    file_path = os.path.join(eavesdrop_audio_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"音频文件不存在: {filename}")
    
    # 返回文件
    return FileResponse(
        file_path,
        media_type="audio/wav",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

# 3. 注册路由
app.include_router(data.router, tags=["Data Management"])
app.include_router(tts.router, tags=["TTS Core"])
app.include_router(system.router, tags=["System Settings"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])
app.include_router(phone_call.router, prefix="/api", tags=["Phone Call"])
app.include_router(speakers.router, prefix="/api", tags=["Speakers Management"])
app.include_router(eavesdrop.router, prefix="/api/eavesdrop", tags=["Eavesdrop Tracking"])
app.include_router(continuous_analysis.router, prefix="/api", tags=["Continuous Analysis"])
app.include_router(genie_admin.router)


if __name__ == "__main__":
    from config import get_genie_host
    from services.genie_tts_client import check_connection
    host = get_genie_host()
    if check_connection(host):
        print(f"[Genie TTS] ✅ API 可访问: {host}")
    else:
        print(f"[Genie TTS] ⚠️  无法连接 {host}，请在 /admin 配置 genie_host 并启动 genie-tts")

    # 必须是 0.0.0.0，否则局域网无法访问
    # access_log=False 禁用默认访问日志,使用自定义日志中间件
    uvicorn.run(app, host="0.0.0.0", port=3000, access_log=False)
