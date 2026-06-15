# 将 VPS 上的 Genie 同步到本地修改

## 目录对应

| VPS | 本地（建议） |
|-----|----------------|
| `/www/genie`（venv、`run_server.py`、`GenieData`） | `D:/workspace/voice-flow/genie-runtime` 或保留 VPS 仅部署 |
| `Genie-TTS` 源码 | `D:/workspace/voice-flow/Genie-TTS`（本仓库已改 `Server.py`） |
| `/www/genie/characters/<角色>` | 与中间件 `genie_character_models.json` 的 `onnx_model_dir` 一致 |
| `/www/genie/refs/<角色>/*.wav` | 与 `MyCharacters/<角色>/reference_audios` 符号链接目标相同 |

## 拉取 Genie 源码（本地）

```bash
# 仅 Server/API 变更时，从 VPS 拷 run_server 包装脚本即可
scp root@<IP>:/www/genie/run_server.py ./genie-runtime/
```

## 推送本地 Genie-TTS 到 VPS

```bash
cd D:/workspace/voice-flow/Genie-TTS
git status   # 或 rsync
rsync -avz --exclude .git src/ root@<IP>:/www/genie/Genie-TTS/src/
# 若 VPS 用 pip install -e，在 /www/genie/venv 重装；systemd 一般直接 PYTHONPATH 指源码
ssh root@<IP> 'systemctl restart genie-tts'
```

## 推送中间件

```bash
cd D:/workspace/voice-flow/SillyTavern-GPT-SoVITS
git push justhil main
ssh root@<IP> 'cd /www/SillyTavern-GPT-SoVITS && git pull && docker compose -f docker-compose.stack.host-genie.yml up -d --no-build --force-recreate tts-manager'
```

## 环境变量（VPS systemd / compose）

- `GENIE_CHARACTERS_ROOT=/www/genie/characters`
- `GENIE_REFS_ROOT=/www/genie/refs`
- `GENIE_DATA_DIR=/www/genie/GenieData`
- `ADMIN_PANEL_PASSWORD` 或 Admin 保存的 `middleware_admin_password`