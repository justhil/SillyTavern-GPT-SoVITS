#!/usr/bin/env bash
# 放行 3000 + 更新中间件 + 可选 nginx HTTPS 反代
set -euo pipefail
INSTALL="/www/SillyTavern-GPT-SoVITS"
cd "$INSTALL"
git pull origin main || git pull
bash deploy/vps-open-port-3000.sh
systemctl restart sillytavern-tts-manager
sleep 2
curl -sf "http://127.0.0.1:3000/ping" && echo " manager OK"

if command -v nginx >/dev/null 2>&1; then
  bash deploy/vps-nginx-tts-proxy.sh
  # 若存在默认站点，尝试自动 include（失败则手动）
  for f in /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf; do
    if [[ -f "$f" ]] && ! grep -q sillytavern-tts-manager "$f"; then
      sed -i '/server_name/i \    include snippets/sillytavern-tts-manager.conf;' "$f" 2>/dev/null || true
    fi
  done
  nginx -t && systemctl reload nginx && echo " nginx reloaded"
fi

echo "---"
echo "HTTP 直连: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):3000/ping"
echo "若酒馆是 HTTPS，扩展请填: https://<同域名>/tts-manager （需 nginx 已配置）"