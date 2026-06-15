#!/usr/bin/env bash
# 停掉所有 genie-tts 容器（slim 内无法执行 /www/genie/venv，只会刷 FATAL 日志）
set -euo pipefail
docker ps -a --format '{{.ID}} {{.Names}}' | while read -r id name; do
  case "$name" in
    *genie-tts*) docker rm -f "$id" 2>/dev/null || true ;;
  esac
done
docker compose -f "${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}/docker-compose.stack.yml" rm -sf genie-tts 2>/dev/null || true
echo "[ok] 已移除 genie-tts 容器；Genie 请只用: systemctl start genie-tts"