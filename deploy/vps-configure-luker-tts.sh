#!/usr/bin/env bash
# Luker + st.justhil.uk + TTS 中间件同源反代
set -euo pipefail

MW="/www/SillyTavern-GPT-SoVITS"
EXT="/www/st/docker/extensions/SillyTavern-GPT-SoVITS"
CF_CFG="/opt/cloudflared/config.yml"
HOST_GW="${DOCKER_HOST_GW:-172.17.0.1}"

echo "=== Luker 调查结论 ==="
echo "  容器 luker，应用端口 2345（非 8000）"
echo "  宿主机: 127.0.0.1:46938 -> luker:2345"
echo "  公网: Cloudflare -> st.justhil.uk -> 应指向 luker:2345"
echo "  中间件: 0.0.0.0:3000 (systemd)"
echo ""

echo "[1] 修复 cloudflared：sillytavern -> luker:2345，并加 /tts-mw -> 宿主机:3000"
if [[ -f "$CF_CFG" ]]; then
  cp -a "$CF_CFG" "${CF_CFG}.bak.$(date +%Y%m%d%H%M)"
  HOST_GW="$HOST_GW" python3 <<'PY'
import os
from pathlib import Path
p = Path("/opt/cloudflared/config.yml")
text = p.read_text(encoding="utf-8")
text = text.replace("http://sillytavern:2345", "http://luker:2345")
gw = os.environ.get("HOST_GW", "172.17.0.1")
block = f"""  - hostname: st.justhil.uk
    path: /tts-mw*
    service: http://{gw}:3000
"""
if "/tts-mw" not in text:
    text = text.replace("ingress:\n", "ingress:\n" + block, 1)
tts_host = f"""  - hostname: tts.justhil.uk
    service: http://{gw}:3000
"""
if "tts.justhil.uk" not in text:
    text = text.replace("ingress:\n", "ingress:\n" + tts_host, 1)
p.write_text(text, encoding="utf-8")
print("patched", p)
PY
  docker restart cloudflared-sillytavern
  sleep 3
else
  echo "  跳过: 无 $CF_CFG"
fi

echo "[2] 同步中间件仓库到酒馆扩展目录"
mkdir -p "$EXT"
rsync -a --delete \
  --exclude 'venv' --exclude 'runtime' --exclude 'Cache' --exclude '.git' \
  --exclude 'MyCharacters' --exclude 'data' \
  "$MW/" "$EXT/"
# 保留酒馆扩展需要的入口：仓库根 index.js + frontend
echo "  synced -> $EXT"

echo "[3] 写入角色映射示例（可按酒馆卡名改）"
MAP="$MW/character_mappings.json"
if [[ ! -s "$MAP" ]] || [[ "$(cat "$MAP")" == "{}" ]]; then
  echo '{"墨白":"墨白"}' > "$MAP"
fi
cp "$MAP" "$EXT/../character_mappings.json" 2>/dev/null || true

echo "[4] 探测"
curl -sf "http://127.0.0.1:3000/ping" && echo " :3000 OK"
curl -sf "http://127.0.0.1:46938/" -o /dev/null -w "luker_local:%{http_code}\n" || true
sleep 2
curl -sf "https://st.justhil.uk/tts-mw/ping" && echo " st.justhil.uk/tts-mw OK" || echo "  若失败: Cloudflare 缓存或路径规则稍等 1 分钟再试"

echo ""
echo "=== 酒馆扩展请填（同源，不要 :3000）==="
echo "  https://tts.justhil.uk   （推荐，需在 Cloudflare 隧道/DNS 添加该主机名）"
echo "  https://st.justhil.uk/tts-mw （备选）"
echo "  或本机调试: http://127.0.0.1:46938 对应扩展填 http://107.173.140.30:46938/tts-mw 需另配反代（见下）"
echo ""
echo "若只用 IP:46938 访问酒馆，在 1Panel OpenResty 为该端口加 location /tts-mw/ 或改用域名 st.justhil.uk"