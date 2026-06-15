#!/bin/sh
set -e
SETTINGS="${SETTINGS_FILE:-/app/system_settings.json}"
GENIE_URL="${GENIE_HOST:-http://172.17.0.1:8429}"
python3 <<PY
import json, os
p = os.environ.get("SETTINGS_FILE", "/app/system_settings.json")
genie = os.environ.get("GENIE_HOST", "http://172.17.0.1:8429")
base = {
  "tts_engine": "genie",
  "genie_host": genie,
  "sovits_host": genie,
}
if os.path.isfile(p):
    with open(p) as f:
        s = json.load(f)
    s.update(base)
    for k in ("genie_host", "sovits_host"):
        if s.get(k) and ":8000" in str(s[k]):
            s[k] = str(s[k]).replace(":8000", ":8429", 1)
else:
    s = base
with open(p, "w", encoding="utf-8") as f:
    json.dump(s, f, ensure_ascii=False, indent=2)
print("genie_host ->", genie)
PY
exec python manager.py