# -*- coding: utf-8 -*-
"""VPS 上经 st-gateway 测 /tts-mw/tts_proxy（需 GENIE_VPS_PASS）。"""
import os
import sys
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")
REMOTE = "/root/vps_test_tts_proxy_remote.py"

REMOTE_PY = r'''
import json
import os
import urllib.parse
import urllib.request

import json as _json

BASE = "http://127.0.0.1:46939/tts-mw"
GENIE = "http://127.0.0.1:8429"
ROOT_HOST = "/www/SillyTavern-GPT-SoVITS"
ROOT = "/app"

print("=== Genie POST /tts (host) ===")
ref_g = "/www/genie/refs/墨白/这是我的使命.wav"
for path, body in (
    ("/load_character", {"character_name": "墨白", "onnx_model_dir": "/www/genie/characters/墨白/onnx", "language": "zh"}),
    ("/set_reference_audio", {"character_name": "墨白", "audio_path": ref_g, "audio_text": "测试", "language": "zh"}),
    ("/tts", {"character_name": "墨白", "text": "你好，测试。", "split_sentence": True}),
):
    req = urllib.request.Request(
        GENIE + path,
        data=_json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
            print(path, "status", r.status, "bytes", len(data))
            if path == "/tts" and len(data) > 1000:
                print("Genie /tts OK (pcm)")
    except urllib.error.HTTPError as e:
        print(path, "HTTP", e.code, e.read()[:300])

print("=== middleware GET /tts_proxy ===")

def load_json(name):
    p = os.path.join(ROOT, name)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}

m = load_json("character_mappings.json")
gm = load_json("genie_character_models.json")
print("mappings", m)
print("genie_model_folders", list(gm.keys())[:8])

char = next(iter(m), "")
folder = m.get(char, "墨白")
if not char:
    char, folder = "墨白", "墨白"

ref = ""
for dp, _, fns in os.walk(os.path.join(ROOT, "MyCharacters", folder, "reference_audios")):
    for fn in sorted(fns):
        if fn.lower().endswith(".wav"):
            p = os.path.join(dp, fn)
            if os.path.isfile(p):
                ref = p
                break
    if ref:
        break
if not ref:
    for base in (f"/www/genie/refs/{folder}", f"/www/genie/characters/{folder}"):
        if not os.path.isdir(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                if fn.lower().endswith(".wav"):
                    ref = os.path.join(dp, fn)
                    break
            if ref:
                break
        if ref:
            break
ref = f"/www/genie/refs/{folder}/这是我的使命.wav"
if not os.path.isfile(ref):
    ref = f"/www/genie/refs/墨白/这是我的使命.wav"
print("char", char, "folder", folder, "ref", ref)
if not ref or not os.path.isfile(ref):
    raise SystemExit("no valid ref wav")

q = urllib.parse.urlencode({
    "text": "你好，这是一次语音合成测试。",
    "text_lang": "zh",
    "prompt_lang": "zh",
    "prompt_text": "测试",
    "ref_audio_path": ref,
    "char_name": char or folder,
    "emotion": "default",
})
url = f"{BASE}/tts_proxy?{q}"
print("GET", url[:120], "...")
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
        print("status", r.status, "bytes", len(data), "ctype", r.headers.get("Content-Type"))
        if len(data) > 4 and data[:4] == b"RIFF":
            print("RESULT: OK wav")
        else:
            print("RESULT: unexpected body", data[:300])
except urllib.error.HTTPError as e:
    print("RESULT: HTTP", e.code, e.read().decode("utf-8", errors="replace")[:800])
except Exception as e:
    print("RESULT: FAIL", e)
'''


def main():
    if not PASS:
        sys.exit("GENIE_VPS_PASS")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    stdin, stdout, stderr = c.exec_command(f"cat > {REMOTE} && python3 {REMOTE}", timeout=360)
    stdin.write(REMOTE_PY)
    stdin.channel.shutdown_write()
    out = stdout.read() + stderr.read()
    sys.stdout.buffer.write(out)
    c.close()


if __name__ == "__main__":
    main()