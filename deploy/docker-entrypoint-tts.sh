#!/bin/sh
set -e
SETTINGS="${SETTINGS_FILE:-/app/system_settings.json}"
GENIE_URL="${GENIE_HOST:-http://genie-tts:8000}"
python3 <<PY
import json, os
p = os.environ.get("SETTINGS_FILE", "/app/system_settings.json")
genie = os.environ.get("GENIE_HOST", "http://genie-tts:8000")
base = {
  "tts_engine": "genie",
  "genie_host": genie,
  "sovits_host": genie,
}
if os.path.isfile(p):
    with open(p) as f:
        s = json.load(f)
    s.update(base)
else:
    s = base
with open(p, "w", encoding="utf-8") as f:
    json.dump(s, f, ensure_ascii=False, indent=2)
print("genie_host ->", genie)
PY
exec python manager.py