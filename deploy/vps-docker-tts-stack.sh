#!/usr/bin/env bash
# 停用宿主机 systemd，改用 Docker 与 luker 同网
set -euo pipefail

TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
GENIE_ROOT="${GENIE_ROOT:-/www/genie}"
COMPOSE="${TTS_ROOT}/docker-compose.stack.yml"

echo "[1] 拉取中间件代码"
cd "$TTS_ROOT"
git pull origin main

echo "[2] 停止宿主机服务（避免占 3000/8000）"
systemctl stop sillytavern-tts-manager 2>/dev/null || true
systemctl disable sillytavern-tts-manager 2>/dev/null || true
systemctl stop genie-tts 2>/dev/null || true
# 不 disable genie 若你还要回退；默认 stop
systemctl stop genie-tts 2>/dev/null || true

echo "[3] 墨白参考音软链（若未做）"
EMO="${TTS_ROOT}/MyCharacters/墨白/reference_audios/Chinese/emotions"
mkdir -p "$EMO"
if [[ -d "${GENIE_ROOT}/refs/墨白" ]]; then
  for wav in "${GENIE_ROOT}/refs/墨白"/*.wav; do
    [[ -f "$wav" ]] || continue
    ln -sf "$wav" "${EMO}/$(basename "$wav")"
    stem=$(basename "$wav" .wav)
    [[ "$stem" == *_* ]] && [[ ! -f "${EMO}/${stem}.txt" ]] && echo "${stem#*_}" > "${EMO}/${stem}.txt"
  done
fi

echo "[4] docker compose up"
export TTS_ROOT GENIE_ROOT
docker compose -f "$COMPOSE" build --no-cache tts-manager 2>/dev/null || docker compose -f "$COMPOSE" build tts-manager
docker compose -f "$COMPOSE" up -d

echo "[5] 等待健康"
sleep 8
docker exec tts-manager python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:3000/ping').read().decode())" || true
docker exec tts-manager python3 -c "import urllib.request; print(urllib.request.urlopen('http://genie-tts:8000/docs').status)" 2>/dev/null || echo "genie 仍在启动…"

echo "[6] Cloudflare 路由提示"
echo "  主机名 tts.justhil.uk 服务改为: http://tts-manager:3000"
echo "  （与 luker 同在 docker_default，不要用 172.17.0.1）"
echo ""
echo "  酒馆扩展: https://tts.justhil.uk"
echo "  容器内自测: docker exec luker wget -qO- http://tts-manager:3000/ping 2>/dev/null || docker run --rm --network docker_default curlimages/curl -s http://tts-manager:3000/ping"