#!/usr/bin/env bash
# Genie：优先 Docker 用宿主机 /www/genie/venv；失败则宿主机 systemd
set -euo pipefail
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
cd "$TTS_ROOT"
git pull origin main 2>/dev/null || true

VENV_PY="/www/genie/venv/bin/python"
RUN_SERVER="/www/genie/run_server.py"

if [[ -x "$VENV_PY" && -f "$RUN_SERVER" ]]; then
  echo "[genie] 使用 Docker 容器 + 宿主机 venv"
  systemctl stop genie-tts 2>/dev/null || true
  export TTS_ROOT GENIE_ROOT=/www/genie
  docker compose -f docker-compose.stack.yml up -d genie-tts tts-manager
else
  echo "[genie] venv 不完整，改用宿主机 systemd genie-tts :8000"
  docker stop genie-tts 2>/dev/null || true
  docker rm genie-tts 2>/dev/null || true
  systemctl enable genie-tts 2>/dev/null || true
  systemctl start genie-tts
  export TTS_ROOT GENIE_ROOT=/www/genie
  docker compose -f docker-compose.stack.host-genie.yml up -d --build tts-manager
  python3 <<PY
import json, os
p = "/www/SillyTavern-GPT-SoVITS/system_settings.json"
g = "http://172.17.0.1:8000"
s = json.load(open(p)) if os.path.isfile(p) else {}
s.update({"genie_host": g, "sovits_host": g, "tts_engine": "genie"})
json.dump(s, open(p, "w"), ensure_ascii=False, indent=2)
print("genie_host ->", g)
PY
fi

sleep 3
curl -sf http://127.0.0.1:8000/docs >/dev/null && echo "Genie :8000 OK" || echo "Genie :8000 未就绪"
docker compose -f docker-compose.stack.yml ps 2>/dev/null || true