#!/usr/bin/env bash
set -euo pipefail
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
cd "$TTS_ROOT"
git pull origin main 2>/dev/null || true

export TTS_ROOT GENIE_ROOT="${GENIE_ROOT:-/www/genie}"

echo "[1] TTS + Genie 容器"
docker compose -f docker-compose.stack.yml up -d

echo "[2] Nginx 反代 st-gateway :46939"
docker compose -f docker-compose.gateway.yml up -d --force-recreate

sleep 2
curl -sf "http://127.0.0.1:46939/tts-mw/ping" && echo " ping OK" || echo "ping FAIL"

IP=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "======== 不用 Cloudflare ========"
echo "酒馆打开:  http://${IP}:46939/"
echo "扩展填:    http://${IP}:46939/tts-mw"
echo "自测:      http://${IP}:46939/tts-mw/ping"
echo "安全组放行 TCP 46939"
echo "==============================="