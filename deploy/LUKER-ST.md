# Luker 酒馆 + TTS 中间件（本 VPS 实测）

## 架构

| 组件 | 说明 |
|------|------|
| **luker** | `ghcr.io/funnycups/luker`，容器内 **2345** |
| 本机访问 | `http://127.0.0.1:46938` → luker:2345 |
| 公网域名 | **https://st.justhil.uk**（Cloudflare Tunnel）→ `luker:2345` |
| **中间件** | `systemd` `sillytavern-tts-manager`，**0.0.0.0:3000** |
| **Genie** | `127.0.0.1:8000` |
| 扩展目录 | `/www/st/docker/extensions/SillyTavern-GPT-SoVITS` → 挂载到酒馆 `third-party` |

compose：`/www/st/luker/Luker/docker-compose.yml`

## 扩展中间件地址（必看）

不要用 `http://IP:3000`（和酒馆不同源）。

**推荐（已配置 Cloudflare 路径）：**

```text
https://st.justhil.uk/tts-mw
```

救援框点 **「使用酒馆同源 /tts-mw」** 或清除配置后让插件自动探测。

验证：`curl https://st.justhil.uk/tts-mw/ping`

## 部署/更新

```bash
cd /www/SillyTavern-GPT-SoVITS && git pull
bash deploy/vps-configure-luker-tts.sh
```

## Cloudflare

`/opt/cloudflared/config.yml`：

- `st.justhil.uk` + path `/tts-mw*` → `http://172.17.0.1:3000`
- `st.justhil.uk` → `http://luker:2345`

改后：`docker restart cloudflared-sillytavern`