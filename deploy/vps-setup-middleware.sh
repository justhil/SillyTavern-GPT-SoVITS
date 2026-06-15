#!/usr/bin/env bash
# VPS 一键：拉取中间件到 /www/SillyTavern-GPT-SoVITS，对接本机 Genie，挂墨白参考音，systemd 启动
set -euo pipefail

REPO_URL="${TTS_REPO_URL:-https://github.com/justhil/SillyTavern-GPT-SoVITS.git}"
INSTALL_DIR="${TTS_INSTALL_DIR:-/www/SillyTavern-GPT-SoVITS}"
GENIE_REFS="${GENIE_REFS_DIR:-/www/genie/refs/墨白}"
GENIE_HOST="${GENIE_HOST:-http://127.0.0.1:8429}"
PORT="${TTS_MANAGER_PORT:-3000}"

echo "[1/7] 目录 ${INSTALL_DIR}"
mkdir -p "$(dirname "$INSTALL_DIR")"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  cd "$INSTALL_DIR"
  git fetch origin
  git reset --hard origin/main
else
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

echo "[2/7] Python 依赖"
if [[ ! -d "${INSTALL_DIR}/venv" ]]; then
  python3 -m venv "${INSTALL_DIR}/venv"
fi
# shellcheck disable=SC1091
source "${INSTALL_DIR}/venv/bin/activate"
pip install -q -U pip
pip install -q -r requirements.txt

echo "[3/7] 墨白 reference_audios（链到 Genie refs）"
EMO_DIR="${INSTALL_DIR}/MyCharacters/墨白/reference_audios/Chinese/emotions"
mkdir -p "$EMO_DIR"
if [[ -d "$GENIE_REFS" ]]; then
  shopt -s nullglob
  for wav in "$GENIE_REFS"/*.wav; do
    base=$(basename "$wav")
    ln -sf "$wav" "${EMO_DIR}/${base}"
    stem="${base%.wav}"
    if [[ "$stem" == *_* ]]; then
      txt="${EMO_DIR}/${stem}.txt"
      if [[ ! -f "$txt" ]]; then
        echo "${stem#*_}" > "$txt"
      fi
    fi
  done
  shopt -u nullglob
  echo "    linked $(ls -1 "$EMO_DIR"/*.wav 2>/dev/null | wc -l) wav"
else
  echo "    WARN: ${GENIE_REFS} 不存在，跳过参考音链接"
fi

echo "[4/7] genie_character_models.json"
cat > "${INSTALL_DIR}/genie_character_models.json" <<'JSON'
{
  "墨白": {
    "genie_character": "mobai",
    "onnx_model_dir": "/www/genie/characters/墨白",
    "language": "zh"
  }
}
JSON

echo "[5/7] system_settings.json"
SETTINGS="${INSTALL_DIR}/system_settings.json"
python3 <<PY
import json, os
p = "${SETTINGS}"
base = {
  "enabled": True,
  "auto_generate": True,
  "base_dir": "${INSTALL_DIR}/MyCharacters",
  "cache_dir": "${INSTALL_DIR}/Cache",
  "default_lang": "Chinese",
  "iframe_mode": False,
  "bubble_style": "default",
  "tts_engine": "genie",
  "genie_host": "${GENIE_HOST}",
  "sovits_host": "${GENIE_HOST}",
}
if os.path.isfile(p):
    with open(p) as f:
        cur = json.load(f)
    for k, v in base.items():
        cur[k] = v
    base = cur
os.makedirs(base["base_dir"], exist_ok=True)
os.makedirs(base["cache_dir"], exist_ok=True)
with open(p, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)
print("    wrote", p)
PY

echo "[6/7] systemd sillytavern-tts-manager"
cat > /etc/systemd/system/sillytavern-tts-manager.service <<EOF
[Unit]
Description=SillyTavern Genie TTS Middleware (manager.py)
After=network.target genie-tts.service
Wants=genie-tts.service

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python manager.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable sillytavern-tts-manager.service

echo "[7/7] 启动并探测"
systemctl restart sillytavern-tts-manager.service || true
sleep 2
systemctl is-active sillytavern-tts-manager.service || true
curl -sf "http://127.0.0.1:${PORT}/ping" && echo " ping OK" || echo " ping FAIL (检查 journalctl -u sillytavern-tts-manager)"
curl -sf "${GENIE_HOST}/docs" >/dev/null && echo " Genie OK" || echo " Genie FAIL"

echo "完成。中间件: http://$(hostname -I 2>/dev/null | awk '{print $1}'):${PORT}/admin"
echo "酒馆扩展填: http://<本机公网IP>:${PORT}  （Genie 默认 :8429，仅 Admin 配置）"