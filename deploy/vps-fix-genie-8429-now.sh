#!/usr/bin/env bash
# 立刻：Genie 改 8429 并验证（宿主机仍在 8000 时执行）
set -euo pipefail
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
cd "$TTS_ROOT"
bash deploy/patch-genie-port-8429.sh
systemctl restart genie-tts
sleep 3
echo -n "host 8429: "; curl -sf -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8429/docs || echo FAIL
echo -n "host 8000: "; curl -sf -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/docs || echo closed
python3 <<'PY'
import json, os
p = "/www/SillyTavern-GPT-SoVITS/system_settings.json"
s = json.load(open(p)) if os.path.isfile(p) else {}
s["genie_host"] = s["sovits_host"] = "http://172.17.0.1:8429"
json.dump(s, open(p, "w"), ensure_ascii=False, indent=2)
print("settings ->", s["genie_host"])
PY
CID=$(docker ps -q --filter name=tts-manager | head -1)
if [[ -n "$CID" ]]; then
  docker restart "$CID"
  sleep 2
  docker exec "$CID" python3 -c "import urllib.request; urllib.request.urlopen('http://172.17.0.1:8429/docs', timeout=8); print('tts-manager -> 8429 OK')" || echo "WARN: container cannot reach 8429"
fi