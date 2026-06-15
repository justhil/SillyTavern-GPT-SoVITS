#!/usr/bin/env python3
"""宿主机运行，不依赖 docker exec。扫 refs/*.wav 逐条调 /tts-mw/tts_proxy。"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.environ.get("TTS_ROOT", "/www/SillyTavern-GPT-SoVITS")
CHAR = os.environ.get("TTS_SAMPLE_CHAR", "墨白")
REFS = os.environ.get("GENIE_REFS_ROOT", "/www/genie/refs")
BASE = os.environ.get("TTS_MW_BASE", "http://127.0.0.1:46939/tts-mw")
TEXT = os.environ.get("TTS_SAMPLE_TEXT", "你好，这是情绪合成示例。")
OUT = os.path.join(ROOT, "samples", "emotion_demos", CHAR)


def prompt_for(wav: str) -> str:
    txt = os.path.splitext(wav)[0] + ".txt"
    if os.path.isfile(txt):
        with open(txt, encoding="utf-8", errors="replace") as f:
            s = f.read().strip()
            if s:
                return s[:300]
    fn = os.path.basename(wav)
    if "_" in fn:
        return os.path.splitext(fn.split("_", 1)[1])[0][:200]
    return os.path.splitext(fn)[0][:200] or "测试"


def safe_name(em: str, fn: str) -> str:
    stem = os.path.splitext(fn)[0]
    em = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", em)[:24]
    short = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", stem)[:60]
    return f"{em}__{short}.wav"


def main():
    ref_dir = os.path.join(REFS, CHAR)
    if not os.path.isdir(ref_dir):
        print("NO_DIR", ref_dir)
        sys.exit(1)
    wavs = sorted(
        f for f in os.listdir(ref_dir) if f.lower().endswith(".wav")
    )
    if not wavs:
        print("NO_WAV", ref_dir)
        sys.exit(1)

    os.makedirs(OUT, exist_ok=True)
    ok = fail = 0
    manifest = []

    for i, fn in enumerate(wavs, 1):
        path = os.path.join(ref_dir, fn)
        path = os.path.realpath(path)
        em = fn.split("_")[0] if "_" in fn else "default"
        out_path = os.path.join(OUT, safe_name(em, fn))
        q = urllib.parse.urlencode(
            {
                "text": TEXT,
                "text_lang": "zh",
                "prompt_lang": "zh",
                "prompt_text": prompt_for(path),
                "ref_audio_path": path,
                "char_name": CHAR,
                "emotion": em,
            }
        )
        url = f"{BASE}/tts_proxy?{q}"
        print(f"[{i}/{len(wavs)}] {em} {fn}")
        try:
            with urllib.request.urlopen(url, timeout=600) as r:
                data = r.read()
            if len(data) > 44 and data[:4] == b"RIFF":
                with open(out_path, "wb") as f:
                    f.write(data)
                ok += 1
                manifest.append({"emotion": em, "ref": path, "out": out_path, "ok": True})
                print(f"  OK {len(data)}")
            else:
                fail += 1
                manifest.append({"emotion": em, "ok": False, "err": f"bytes={len(data)}"})
        except Exception as e:
            fail += 1
            manifest.append({"emotion": em, "ref": path, "ok": False, "err": str(e)})
            print(f"  FAIL {e}")

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"DONE ok={ok} fail={fail} -> {OUT}")


if __name__ == "__main__":
    main()