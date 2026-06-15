#!/usr/bin/env bash
# 宿主机 Genie 监听 8429（systemd + run_server.py）
set -euo pipefail
GENIE_ROOT="${GENIE_ROOT:-/www/genie}"
PORT=8429

if [[ -f "${GENIE_ROOT}/run_server.py" ]]; then
  sed -i 's/port=8000/port=8429/g; s/port: 8000/port: 8429/g; s/port=8429/port=8429/g' "${GENIE_ROOT}/run_server.py" 2>/dev/null || true
  sed -i 's/"port": 8000/"port": 8429/g; s/"port":8000/"port":8429/g' "${GENIE_ROOT}/run_server.py" 2>/dev/null || true
  if grep -qE '8000' "${GENIE_ROOT}/run_server.py" 2>/dev/null; then
    python3 -c "
import re, pathlib
p=pathlib.Path('${GENIE_ROOT}/run_server.py')
t=p.read_text()
t=re.sub(r'port\\s*=\\s*8000', 'port=8429', t)
t=re.sub(r'port\\s*=\\s*\"8000\"', 'port=\"8429\"', t)
p.write_text(t)
" && echo "[ok] python patched run_server.py"
  else
    echo "[ok] run_server.py uses 8429"
  fi
fi

UNIT=/etc/systemd/system/genie-tts.service
if [[ -f "$UNIT" ]]; then
  if grep -qE '8000|8429' "$UNIT"; then
    sed -i 's/8000/8429/g' "$UNIT" || true
    systemctl daemon-reload
    echo "[ok] patched $UNIT"
  fi
fi

systemctl restart genie-tts 2>/dev/null || true
sleep 2
curl -sf "http://127.0.0.1:${PORT}/docs" >/dev/null && echo "Genie :${PORT} OK" || echo "WARN: Genie :${PORT} not ready"