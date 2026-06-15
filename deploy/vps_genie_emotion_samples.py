# -*- coding: utf-8 -*-
"""VPS：对每个参考音（按文件/情绪）调用 /tts-mw/tts_proxy 生成示例 wav。"""
import os
import re
import sys
import json
import urllib.parse
import urllib.request

ROOT = os.environ.get("TTS_ROOT", "/www/SillyTavern-GPT-SoVITS")
sys.path.insert(0, ROOT)

from config import init_settings
from services.genie_catalog import list_reference_audios_for_folder

BASE = os.environ.get("TTS_MW_BASE", "http://127.0.0.1:46939/tts-mw")
CHAR = os.environ.get("TTS_SAMPLE_CHAR", "墨白")
TEXT = os.environ.get("TTS_SAMPLE_TEXT", "你好，这是情绪合成示例。")
OUT = os.path.join(ROOT, "samples", "emotion_demos", CHAR)


def prompt_for(wav_path: str) -> str:
    stem, _ = os.path.splitext(wav_path)
    txt = stem + ".txt"
    if os.path.isfile(txt):
        with open(txt, encoding="utf-8", errors="replace") as f:
            t = f.read().strip()
            if t:
                return t[:300]
    base = os.path.basename(wav_path)
    if "_" in base:
        return os.path.splitext(base.split("_", 1)[1])[0][:200]
    return os.path.splitext(base)[0][:200] or "测试"


def safe_name(emotion: str, filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    em = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", emotion)[:24]
    short = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", stem)[:48]
    return f"{em}__{short}.wav"


def main():
    settings = init_settings()
    base_dir = settings.get("base_dir") or os.path.join(ROOT, "MyCharacters")
    audios = list_reference_audios_for_folder(CHAR, base_dir)
    if not audios:
        print("NO_REF_AUDIOS", CHAR)
        sys.exit(1)

    os.makedirs(OUT, exist_ok=True)
    ok, fail = 0, 0
    manifest = []

    for i, a in enumerate(audios, 1):
        path = a["path"]
        em = a["emotion"]
        fn = a["filename"]
        out_name = safe_name(em, fn)
        out_path = os.path.join(OUT, out_name)

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
        print(f"[{i}/{len(audios)}] {em} <- {fn}")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=600) as r:
                data = r.read()
            if len(data) > 44 and data[:4] == b"RIFF":
                with open(out_path, "wb") as f:
                    f.write(data)
                ok += 1
                manifest.append(
                    {"emotion": em, "ref": path, "out": out_path, "bytes": len(data), "ok": True}
                )
                print(f"  OK {len(data)} -> {out_path}")
            else:
                fail += 1
                manifest.append({"emotion": em, "ref": path, "ok": False, "err": "not_wav"})
                print(f"  FAIL not wav, {len(data)} bytes")
        except Exception as e:
            fail += 1
            manifest.append({"emotion": em, "ref": path, "ok": False, "err": str(e)})
            print(f"  FAIL {e}")

    meta = os.path.join(OUT, "manifest.json")
    with open(meta, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"DONE ok={ok} fail={fail} dir={OUT}")
    print(f"manifest={meta}")


if __name__ == "__main__":
    main()