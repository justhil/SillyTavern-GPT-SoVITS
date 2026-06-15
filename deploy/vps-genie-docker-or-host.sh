#!/usr/bin/env bash
# Genie 仅宿主机 systemd；中间件 Docker
set -euo pipefail
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
cd "$TTS_ROOT"
git pull origin main 2>/dev/null || true

bash deploy/vps-stop-genie-container.sh
systemctl enable genie-tts 2>/dev/null || true
systemctl start genie-tts 2>/dev/null || true
sleep 2

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

sleep 2
curl -sf http://127.0.0.1:8000/docs >/dev/null && echo "Genie :8000 OK" || echo "Genie :8000 未就绪 (systemctl status genie-tts)"
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'tts-manager|genie' || true