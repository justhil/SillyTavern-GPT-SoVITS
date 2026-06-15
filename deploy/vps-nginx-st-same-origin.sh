#!/usr/bin/env bash
# 让酒馆与中间件同源：http://IP:酒馆端口/tts-mw/ -> 127.0.0.1:3000
set -euo pipefail
ST_PORT="${SILLYTAVERN_PORT:-8000}"
SNIP="/etc/nginx/snippets/sillytavern-tts-same-origin.conf"
mkdir -p /etc/nginx/snippets
cat > "$SNIP" <<'NGX'
location /tts-mw/ {
    proxy_pass http://127.0.0.1:3000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
    add_header Access-Control-Allow-Origin * always;
}
NGX

if ! command -v nginx >/dev/null 2>&1; then
  echo "未安装 nginx。请用 Docker 反代或手动安装 nginx。"
  echo "扩展可尝试: http://${ST_PORT} 同源需反代，临时方案见文档。"
  exit 0
fi

MARK="sillytavern-tts-same-origin"
FOUND=0
for f in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
  [[ -f "$f" ]] || continue
  if grep -q "listen.*${ST_PORT}" "$f" 2>/dev/null; then
    if ! grep -q "$MARK" "$f"; then
      sed -i "/listen.*${ST_PORT}/a \\    include snippets/sillytavern-tts-same-origin.conf; # ${MARK}" "$f"
      echo "patched $f"
    fi
    FOUND=1
  fi
done

if [[ "$FOUND" -eq 0 ]]; then
  echo "未找到 listen ${ST_PORT} 的 server 块。请手动在酒馆 nginx server 内加入:"
  echo "  include snippets/sillytavern-tts-same-origin.conf;"
  echo "然后: nginx -t && systemctl reload nginx"
  exit 0
fi

nginx -t
systemctl reload nginx
echo "OK: 测试 http://127.0.0.1:${ST_PORT}/tts-mw/ping"
curl -sf "http://127.0.0.1:${ST_PORT}/tts-mw/ping" && echo " same-origin proxy OK" || echo " FAIL（酒馆可能不经 nginx，改 SILLYTAVERN_PORT 或手动配置）"