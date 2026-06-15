#!/usr/bin/env bash
# 无 /tmp 的 VPS：用 TMPDIR=/var/tmp 重建/启动 tts-manager
set -euo pipefail
export TMPDIR="${TMPDIR:-/var/tmp}"
export DOCKER_TMPDIR="${DOCKER_TMPDIR:-/var/tmp}"
TTS_ROOT="${TTS_ROOT:-/www/SillyTavern-GPT-SoVITS}"
cd "$TTS_ROOT"

git pull https://github.com/justhil/SillyTavern-GPT-SoVITS.git main 2>/dev/null || git pull origin main || true

bash deploy/patch-genie-port-8429.sh 2>/dev/null || true
sed -i 's/:8000/:8429/g' system_settings.json 2>/dev/null || true
python3 -c "
import json, os
p='system_settings.json'
if os.path.isfile(p):
 s=json.load(open(p))
 for k in ('genie_host','sovits_host'):
  if not s.get(k) or '172.17.0.1' not in str(s.get(k,'')):
   s[k]='http://172.17.0.1:8429'
 json.dump(s,open(p,'w'),ensure_ascii=False,indent=2)
 print('genie_host ->', s.get('genie_host'))
" 2>/dev/null || true

export TTS_ROOT GENIE_ROOT=/www/genie
if docker image inspect st-tts-manager:local >/dev/null 2>&1; then
  docker compose -f docker-compose.stack.host-genie.yml up -d --no-build --force-recreate tts-manager
else
  TMPDIR=/var/tmp docker compose -f docker-compose.stack.host-genie.yml up -d --build
fi
docker compose -f docker-compose.gateway.yml up -d --force-recreate 2>/dev/null || true
curl -sf http://127.0.0.1:46939/tts-mw/ping && echo " gateway ping OK" || true