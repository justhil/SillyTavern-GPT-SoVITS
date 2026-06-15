# VPS 状态快照（2026-06-15，非训练）

## 已完成

- [x] 中间件接入 Genie TTS（`tts_engine: genie`，`genie_tts_client` PCM→WAV）
- [x] Docker 网 `docker_default`：`tts-manager` + `luker` + `st-gateway`
- [x] Genie：**systemd** `genie-tts`，端口 **8429**（`patch-genie-port-8429.sh`）
- [x] 公网单端口 **46939**：酒馆 + `/tts-mw` 同源（`docker-compose.gateway.yml`）
- [x] 禁用/清理 **genie-tts 容器**（`vps-stop-genie-container.sh`）
- [x] Admin `/tts-mw/admin` 重定向与 API 前缀修复
- [x] 可选中间件 API 鉴权：`TTS_MW_API_KEY` / `middleware_api_key`
- [x] 墨白：refs 链到 `MyCharacters`，经 `/tts-mw/tts_proxy` 合成测试通过（需有效 wav 路径）
- [x] 代码已推 **justhil** `main`（本地可能 ahead of haide-D origin）

## 未纳入本次整理

- 模型训练、新角色 ONNX 训练流水线
- 酒馆扩展在 Luker 内的安装步骤（用户自行 `git pull` 扩展目录）
- Cloudflare 隧道（可选，见 `CLOUDFLARE-TUNNEL.md`）

## 仓库内主要变更文件（部署向）

- `docker-compose.stack.host-genie.yml`、`docker-compose.gateway.yml`
- `deploy/nginx-st-gateway.conf`、`deploy/vps-*.sh`
- `middleware/api_auth.py`、`manager.py`（前缀与鉴权）
- `config.py`（8429 默认与 8000→8429 迁移）
- `admin/*`、`frontend/js/api.js`（鉴权头与连接配置）

## 远程仓库

- **推送目标**：`git remote justhil` → `https://github.com/justhil/SillyTavern-GPT-SoVITS.git`
- VPS：`git pull https://github.com/justhil/SillyTavern-GPT-SoVITS.git main`