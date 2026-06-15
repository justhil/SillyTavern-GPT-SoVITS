#!/usr/bin/env bash
set -euo pipefail
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
LUKER_COMPOSE="/www/st/luker/Luker/docker-compose.yml"
NGINX_CONF="${TTS_ROOT}/deploy/nginx-st-gateway.conf"
cd "$TTS_ROOT"
git pull origin main 2>/dev/null || true
echo "[1] tts stack"
docker compose -f docker-compose.stack.yml up -d
echo "[2] luker without 46938 bind"
if [[ -f "$LUKER_COMPOSE" ]]; then
  cp -a "$LUKER_COMPOSE" "${LUKER_COMPOSE}.bak.gateway"
  python3 <<'PY'
from pathlib import Path
p = Path("/www/st/luker/Luker/docker-compose.yml")
lines = [l for l in p.read_text(encoding="utf-8").splitlines() if "46938" not in l]
p.write_text("\n".join(lines)+"\n", encoding="utf-8")
print("ok")
PY
  cd /www/st/luker/Luker && docker compose up -d
fi
echo "[3] st-gateway"
docker rm -f st-gateway 2>/dev/null || true
docker run -d --name st-gateway --restart unless-stopped --network docker_default \
  -p 0.0.0.0:46938:80 -v "${NGINX_CONF}:/etc/nginx/conf.d/default.conf:ro" nginx:alpine
sleep 2
curl -sf "http://127.0.0.1:46938/tts-mw/ping" && echo " OK" || echo " FAIL"
IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo "酒馆: http://${IP}:46938"
echo "扩展: http://${IP}:46938/tts-mw"
