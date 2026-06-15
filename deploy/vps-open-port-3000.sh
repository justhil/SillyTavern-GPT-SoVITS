#!/usr/bin/env bash
# 放行中间件 3000（ufw / firewalld）
set -e
PORT=3000
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow "${PORT}/tcp" comment 'sillytavern-tts-manager' || true
  ufw reload || true
  echo "ufw: allowed ${PORT}"
fi
if command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port="${PORT}/tcp" 2>/dev/null || true
  firewall-cmd --reload 2>/dev/null || true
fi
ss -tlnp | grep ":${PORT}" || netstat -tlnp 2>/dev/null | grep ":${PORT}" || true
curl -sf "http://127.0.0.1:${PORT}/ping" && echo " local ping OK"