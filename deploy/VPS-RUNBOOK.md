# VPS 部署总览（不含训练）

> 仓库：`justhil/SillyTavern-GPT-SoVITS`  
> 典型路径：`/www/SillyTavern-GPT-SoVITS`  
> 更新：2026-06-15

## 请求链路（不用 Cloudflare）

```
浏览器
  ├─ 酒馆 UI     GET  http://<公网IP>:46939/
  │                    → st-gateway (nginx) → luker:2345
  │
  └─ TTS 中间件  GET/POST http://<公网IP>:46939/tts-mw/...
                         → st-gateway 剥前缀 /tts-mw/ → tts-manager:3000 (FastAPI manager.py)
                                    │
                                    ├─ /admin、/api/admin  管理面板（不经 API 密钥）
                                    ├─ /ping、/tts_proxy…   酒馆扩展 API（可要求 TTS_MW_API_KEY）
                                    └─ Genie 合成 HTTP → http://172.17.0.1:8429
                                                          （宿主机 systemd genie-tts，非 Docker）
```

**扩展里只填**：`http://<公网IP>:46939/tts-mw`（不要 `:3000`，不要容器名 `tts-manager`）。

**Admin**：`http://<公网IP>:46939/tts-mw/admin/`  
（若 307 丢前缀，见 `nginx-st-gateway.conf` + `manager.py` Location 修补。）

## 组件与端口

| 组件 | 运行方式 | 端口 / 路径 | 说明 |
|------|----------|-------------|------|
| **st-gateway** | Docker `docker-compose.gateway.yml` | 宿主机 **46939**→80 | 统一入口 |
| **luker** | Docker（SillyTavern） | 容器 2345；常映射 46938 | 酒馆本体 |
| **tts-manager** | Docker `docker-compose.stack.host-genie.yml` | 仅 docker 网 **3000** | 中间件，挂卷 `/app` = 仓库目录 |
| **genie-tts** | **宿主机 systemd** | **8429**（已从 8000 迁移） | `/www/genie/venv` + `run_server.py` |
| **墨白数据** | 宿主机 | `/www/genie/characters/墨白`、`/www/genie/refs/墨白` | ONNX + 参考音 |

**故意不用**：`genie-tts` Docker 容器（slim 镜像无法执行宿主机 venv，会刷 FATAL 日志）。

## VPS 目录

| 路径 | 内容 |
|------|------|
| `/www/SillyTavern-GPT-SoVITS` | 本仓库 git clone |
| `/www/genie` | Genie venv、`run_server.py`、`GenieData`、characters |
| `/www/st/docker/extensions/...` | 酒馆扩展（用户自行安装/同步） |

## 配置要点

| 配置项 | 位置 | 值（VPS） |
|--------|------|-----------|
| Genie API | `system_settings.json` → `genie_host` | `http://172.17.0.1:8429`（容器访问宿主机） |
| 中间件鉴权 | 环境变量 `TTS_MW_API_KEY` 或 Admin「中间件 API 密钥」 | 非空则扩展须带 `X-TTS-API-Key` |
| 角色映射 | `character_mappings.json`（gitignore） | 例 墨白→墨白 |
| Genie 模型 | `genie_character_models.json` | 墨白 ONNX 路径 |

`docker-entrypoint-tts.sh` 启动时会写入/修正 `genie_host`；`:8000` 会自动迁到 `:8429`。

## 一键 / 常用脚本（在 VPS 仓库根执行）

| 脚本 | 作用 |
|------|------|
| `deploy/vps-deploy-st-gateway.sh` | pull → 停 genie 容器 → systemd Genie → tts-manager + st-gateway |
| `deploy/vps-up-host-genie.sh` | 无 `/tmp` 时用 `TMPDIR=/var/tmp` 启中间件 |
| `deploy/vps-fix-genie-8429-now.sh` | 改 `run_server.py` 端口、重启 genie、改 settings |
| `deploy/patch-genie-port-8429.sh` | 仅改 Genie 端口与 systemd |
| `deploy/vps-stop-genie-container.sh` | 删除错误的 genie-tts 容器 |
| `deploy/vps-genie-docker-or-host.sh` | 仅 systemd Genie + host-genie compose |

本地远程执行（**勿把密码写入仓库**）：

```bash
export GENIE_VPS_HOST=<你的IP>
export GENIE_VPS_PASS=<仅本机环境变量>
python deploy/run_vps_gateway.py
```

## 本机特殊问题

- **无 `/tmp`**：`docker compose --build` 可能失败 → 用 `export TMPDIR=/var/tmp`，或 `up -d --no-build` 复用已有 `st-tts-manager:local` 镜像。
- **安全组**：放行 TCP **46939**（网关）；8429 仅需本机/容器访问，不必公网暴露。

## 验证

```bash
curl -sf http://127.0.0.1:8429/docs && echo genie_ok
curl -sf http://127.0.0.1:46939/tts-mw/ping
curl -sf "http://127.0.0.1:46939/tts-mw/tts_proxy?text=test&..."  # 需合法 ref_audio_path
```

## 相关文档

- `deploy/DOCKER-GENIE-FIX.md` — 为何不用 genie Docker
- `deploy/nginx-st-gateway.conf` — 反代与 `/api/admin` 兜底
- `deploy/.env.stack.example` — `TTS_MW_API_KEY` 示例（复制为本地 `.env`，勿提交）

## 敏感信息审查

- **勿提交**：`system_settings.json`、`character_mappings.json`、`.env`、root 密码、Cloudflare token、真实 API 密钥（已在 `.gitignore`）。
- 部署脚本中的默认 IP 仅为示例；密码仅通过 `GENIE_VPS_PASS` 环境变量传入。
- 公网 IP 出现在文档/脚本默认值中属运维便利，可按需改为 `GENIE_VPS_HOST` 覆盖。