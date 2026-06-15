#!/bin/bash
set -euo pipefail
cd /www/genie
export GENIE_DATA_DIR="${GENIE_DATA_DIR:-/www/genie/GenieData}"
export PYTHONUNBUFFERED=1

PY="/www/genie/venv/bin/python"
RUN="/www/genie/run_server.py"

if [[ ! -x "$PY" ]]; then
  echo "[genie-tts] FATAL: 未找到宿主机 venv: $PY"
  echo "[genie-tts] 请在宿主机执行: systemctl start genie-tts"
  echo "[genie-tts] 并在 tts-manager 使用 GENIE_HOST=http://172.17.0.1:8429"
  exit 1
fi

if [[ ! -f "$RUN" ]]; then
  echo "[genie-tts] FATAL: 未找到 $RUN"
  exit 1
fi

echo "[genie-tts] 使用宿主机 venv 启动 (不 pip install)"
exec "$PY" "$RUN"