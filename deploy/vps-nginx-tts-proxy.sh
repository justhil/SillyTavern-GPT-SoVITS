#!/usr/bin/env bash
# 在已有 nginx 的 server 块里 include，使 HTTPS 酒馆可访问中间件
set -e
CONF="/etc/nginx/snippets/sillytavern-tts-manager.conf"
mkdir -p /etc/nginx/snippets
cat > "$CONF" <<'NGX'
location /tts-manager/ {
    proxy_pass http://127.0.0.1:3000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 600s;
}
NGX
echo "OK: $CONF"
echo "在 server { } 内加: include snippets/sillytavern-tts-manager.conf;"
echo "nginx -t && systemctl reload nginx"
echo "扩展填: https://你的域名/tts-manager  (注意无末尾斜杠，请求会走 /tts-manager/ping)"